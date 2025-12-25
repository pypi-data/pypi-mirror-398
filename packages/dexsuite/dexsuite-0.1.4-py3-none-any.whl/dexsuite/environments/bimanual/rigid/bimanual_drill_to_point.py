"""Drill-to-point environment (bimanual, rigid objects).

The robot must bring a power drill tip to a target point on a wooden wall. The
drill and wall are rigid bodies loaded from assets.

Entities:
  - drill: MJCF power drill.
  - drill_tip: Fixed marker linked to the drill.
  - wooden_wall: MJCF wall block.
  - target: Fixed marker linked to the wall.

Success:
  Intended to require the drill tip to be close to the target and the drill
  roll angle to be within a tolerance.

Failure:
  Intended to trigger if the drill leaves the workspace AABB or if the drill is
  detected as dropping.
"""

from __future__ import annotations

import math

import genesis as gs
import torch

from dexsuite.core.registry import register_env
from dexsuite.environments.base_env import BaseEnv
from dexsuite.utils import get_object_path
from dexsuite.utils.randomizers import (
    YawRandomizer,
    sample_in_aabb_center_xyz_band,
)

# Simulation
SIM_DT = 0.01
SUBSTEPS = 1
HORIZON = 30000

# Task
DRILL_MARGIN = 0.03

CUBE_SIZE = 0.05
DRILL_BASE_QUAT = (0.0, 0.0, 0.7071068, 0.7071068)
ZERO_POS = (0.0, 0.0, 0.0)

# Wall
WALL_BASE_POS = (1.05, 0.35, 0.35)
WALL_EULER_DEG = (0.0, 0.0, 80.0)
WALL_SCALE = 0.5

WALL_BAND_XYZ = (0.05, 0.0, 0.05)  # Band for sampling wall position xyz
SLOPE_TILT = -35.0  # Wall sampling slope tilt

# Child offsets (in local frames at link time)
DRILL_TIP_LOCAL = (-0.12, 0.055, 0.00)
TARGET_LOCAL_POS = (-0.02, 0.005, 0.00)
TARGET_EULER_DEG = (9.0, 90.0, 0.0)

# Sampling / randomization
DRILL_YAW_DEG = 10.0  # +/- deg

# Success / failure
TIP_TARGET_DIST_THR = 0.03  # 3 cm
ROLL_TARGET_RAD = 1.5707963  # about -90 deg about X
ROLL_TOL_RAD = math.radians(30.0)  # +/- 30 deg
DROP_VZ_THR = -0.80  # m/s (fast downward)
DROP_TCP_DIST = 0.20  # m (TCP far)
DROP_GRACE = 4  # frames


@register_env("bimanual_drill_to_point")
class BimanualDrillToPointEnv(BaseEnv):
    def __init__(
        self,
        *,
        robot,
        cameras,
        sim,
        render_mode: str | None,
        seed: int | None = None,
        **scene_kw,
    ):
        super().__init__(
            robot_options=robot,
            cameras_options=cameras,
            sim_options=sim,
            render_mode=render_mode,
            seed=seed,
            sim_dt=SIM_DT,
            substeps=SUBSTEPS,
            horizon=HORIZON,
            **scene_kw,
        )
        self._drops = 0

    # ------------------- scene --------------------------------------- #
    def _setup_scene(self) -> None:
        drill_path = get_object_path("tools/power_drill")
        wood_block = get_object_path("tools/wood_block/wood_block_fixed.xml")

        self.robot_offset_box = self.world_aabb.half("x", "low")

        self.wood_box = self.world_aabb.half("y", "high").half("y", "high")
        self.wood_box.min[0] = self.robot_offset_box.max[0]

        self.drill_box = self.world_aabb.half("y", "low").half("y", "low")
        self.drill_box.min[0] = self.robot_offset_box.max[0]
        drill_spawn_center_xyz = self.drill_box.center()
        drill_spawn_pos_list = drill_spawn_center_xyz.tolist()
        drill_spawn_pos_list[2] = 0.1
        self.drill_spawn_pos = tuple(drill_spawn_pos_list)
        self.drill_yaw_half_range_rad = math.radians(DRILL_YAW_DEG)

        # Drill parent (spawned at base pose)
        self.drill = self.scene.add_entity(
            gs.morphs.MJCF(
                file=str(drill_path),
                quat=DRILL_BASE_QUAT,
                collision=True,
                pos=self.drill_spawn_pos,
            ),
            material=gs.materials.Rigid(),
        )
        # Drill tip (child) - place near the chuck; simple local offset at link time
        self.drill_tip = self.scene.add_entity(
            gs.morphs.Sphere(
                radius=0.01,
                collision=False,
                fixed=True,
                pos=DRILL_TIP_LOCAL,
            ),
            material=gs.materials.Rigid(),
            surface=gs.surfaces.Default(color=(0.2, 0.8, 0.2)),
        )
        self.scene.link_entities(
            parent_entity=self.drill,
            child_entity=self.drill_tip,
            parent_link_name=self.drill.links[0].name,
            child_link_name=self.drill_tip.links[0].name,
        )
        # Wooden wall (parent)
        self.wooden_wall = self.scene.add_entity(
            gs.morphs.MJCF(
                file=str(wood_block),
                pos=WALL_BASE_POS,
                euler=WALL_EULER_DEG,
                scale=WALL_SCALE,
            ),
            material=gs.materials.Rigid(),
        )
        # Target (child of wall)
        self.target = self.scene.add_entity(
            gs.morphs.Cylinder(
                height=0.01,
                radius=0.005,
                pos=TARGET_LOCAL_POS,
                euler=TARGET_EULER_DEG,
                fixed=True,
            ),
            material=gs.materials.Rigid(),
            surface=gs.surfaces.Default(color=(0.2, 0.8, 0.2)),
        )
        self.scene.link_entities(
            parent_entity=self.wooden_wall,
            child_entity=self.target,
            parent_link_name=self.wooden_wall.links[0].name,
            child_link_name=self.target.links[0].name,
        )

    # ------------------- reset --------------------------------------- #
    def _on_episode_start(self, envs_idx: torch.Tensor | None) -> None:
        self._drops = 0
        # Randomize drill yaw around base orientation (absolute, world-frame)

        drill_yaw_randomizer = YawRandomizer(
            yaw_range=(-self.drill_yaw_half_range_rad, self.drill_yaw_half_range_rad),
        )
        yaw_rand_quat = drill_yaw_randomizer.quat(
            base_quat=DRILL_BASE_QUAT,
            frame="world",
            env_idx=envs_idx,
        )
        self.drill.set_quat(yaw_rand_quat, envs_idx=envs_idx)

        # Sample wall position around a line y = a*x + b

        # line parameters
        slope_tilt_rad = math.radians(SLOPE_TILT)  # tilt angle about Z in radians
        wall_slope = float(math.tan(slope_tilt_rad))  # slope
        wall_intercept = float(WALL_BASE_POS[1]) - wall_slope * float(WALL_BASE_POS[0])  # y-intercept

        raw_sample = sample_in_aabb_center_xyz_band(
            self.wood_box,
            band_xyz=WALL_BAND_XYZ,
            range_z=(0.48, 0.58),
            env_idx=envs_idx,
        )
        is_single_env_sample = raw_sample.ndim == 1
        wall_positions = raw_sample.reshape(-1, 3).to(
            device=self.device,
            dtype=torch.float32,
        )

        wall_x = wall_positions[:, 0]
        wall_y_on_line = wall_slope * wall_x + float(wall_intercept)

        wall_y = wall_y_on_line.clamp(
            float(self.wood_box.min[1]),
            float(self.wood_box.max[1]),
        )

        wall_z = wall_positions[:, 2]

        clamped_wall_positions = torch.stack([wall_x, wall_y, wall_z], dim=1)
        clamped_wall_positions = self.wood_box.clamp(clamped_wall_positions)
        wall_positions_to_set = (
            clamped_wall_positions.squeeze(0)
            if is_single_env_sample
            else clamped_wall_positions
        )

        self.wooden_wall.set_pos(wall_positions_to_set, envs_idx=envs_idx)
        # Children (target) follow automatically because of the link.

    # ------------------- obs / reward / success / failure ------------- #
    # def _get_extra_obs(self) -> dict[str, Any]:
    #     # Positions
    #     dpos = self.drill.get_pos()
    #     tpos = self.target.get_pos()
    #     tip = self.drill_tip.get_pos()
    #     # RPY (degrees)
    #     droll, dpitch, dyaw = quat_to_rpy(self.drill.get_quat())
    #     troll, tpitch, tyaw = quat_to_rpy(self.target.get_quat())
    #     d_rpy_deg = torch.tensor(
    #         [
    #             math.degrees(float(droll)),
    #             math.degrees(float(dpitch)),
    #             math.degrees(float(dyaw)),
    #         ],
    #         dtype=torch.float32,
    #     )
    #     t_rpy_deg = torch.tensor(
    #         [
    #             math.degrees(float(troll)),
    #             math.degrees(float(tpitch)),
    #             math.degrees(float(tyaw)),
    #         ],
    #         dtype=torch.float32,
    #     )
    #     # Tip to target distance (meters)
    #     dist = torch.norm(tip - tpos)
    #     # Console print (degrees only)
    #     print(
    #         f"pos (m): ({float(dpos[0]):.3f}, {float(dpos[1]):.3f}, {float(dpos[2]):.3f}) | "
    #         f"drill_rpy_deg: ({d_rpy_deg[0].item():.1f}, {d_rpy_deg[1].item():.1f}, {d_rpy_deg[2].item():.1f}) | "
    #         f"target_rpy_deg: ({t_rpy_deg[0].item():.1f}, {t_rpy_deg[1].item():.1f}, {t_rpy_deg[2].item():.1f}) | "
    #         f"tip->target: {float(dist):.3f} m"
    #     )
    #     return {
    #         "drill_pos": dpos,  # meters
    #         "target_pos": tpos,  # meters
    #         "drill_rpy_deg": d_rpy_deg,  # degrees
    #         "target_rpy_deg": t_rpy_deg,  # degrees
    #         "drill_tip_pos": tip,
    #         "tip_target_dist": dist,  # meters
    #     }
    def _compute_reward(self, obs) -> torch.Tensor:
        return torch.zeros(self.n_envs, dtype=torch.float32, device=self.device)

    # def _is_success(self, obs) -> bool:
    #     # (1) tip-to-target distance <= 3 cm
    #     tip_p = self.drill_tip.get_pos()
    #     tgt_p = self.target.get_pos()
    #     dist_ok = bool(torch.norm(tip_p - tgt_p) <= TIP_TARGET_DIST_THR)
    #     # (2) roll about X within +/- 10 deg of baseline
    #     roll_x, _, _ = quat_to_rpy(self.drill.get_quat())  # radians
    #     roll_err = abs(
    #         ((float(roll_x) - ROLL_TARGET_RAD + math.pi) % (2.0 * math.pi)) - math.pi
    #     )
    #     roll_ok = bool(roll_err <= ROLL_TOL_RAD)
    #     return dist_ok and roll_ok
    # def _is_failure(self, obs) -> bool:
    #     # Base failure gates
    #     if super()._is_failure(obs):
    #         return True
    #     # AABB outside workspace (drill)
    #     outside_ws = False
    #     if self.world_aabb is not None:
    #         lo, hi = self.world_aabb.half("y", "high"), self.world_aabb.half("y", "low")
    #         d_lo, d_hi = self.drill.get_AABB()
    #         outside_ws = ((d_hi < lo).any() or (d_lo > hi).any()).item()
    #     # Drop detector: far from TCP and moving down fast
    #     tcp = obs["state"]["gripper"]["tcp_pos"]
    #     d_p = self.drill.get_pos()
    #     d_v = self.drill.get_vel()
    #     far = torch.norm(d_p - tcp) > DROP_TCP_DIST
    #     fast_down = d_v[2] < DROP_VZ_THR
    #     drop_now = bool(far and fast_down)
    #     self._drops = self._drops + 1 if drop_now else 0
    #     return outside_ws or (self._drops >= DROP_GRACE)
