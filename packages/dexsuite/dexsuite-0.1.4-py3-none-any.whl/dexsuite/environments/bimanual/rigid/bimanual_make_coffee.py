"""Make coffee environment (bimanual, rigid objects).

The robot must place a mug on the tray of a fixed coffee machine.

Entities:
  - machine: Fixed coffee machine.
  - mug: Rigid mug that the robot can move.
  - mug_target: Fixed marker linked to the mug (handle side).

Extra observations (under obs['state']['other']):
  - machine_pos
  - mug_pos

Success:
  Intended to require the mug to be within the tray region in XY and within a Z
  tolerance, while the mug is resting for a few consecutive frames.

Failure:
  Intended to trigger if the mug leaves the workspace AABB or the mug drops fast
  while the TCP is far away.
"""

from __future__ import annotations

import math
from typing import Any

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
HORIZON = 1000

# Scene
MACHINE_SCALE = 0.25
MUG_SCALE = 1

# Tray region (acceptance zone in the machine frame)
TRAY_OFF_X = 0.00  # machine, +X moves toward the robot if machine faces +Y
TRAY_OFF_Y = -0.1  # machine, negative Y = toward robot for a machine on +Y side
TRAY_HALF_SX = 0.06  # machine, half-width on X (acceptance region ~= 12 cm)
TRAY_HALF_SY = 0.06  # machine, half-width on Y
Z_TOL = 0.14  # Z-band relative to machine bottom (mug COM must be within)

# Success / failure
TCP_CLEARANCE = 0.1  # TCP must be >= 10 cm from mug AABB
REST_FRAMES = 5
REST_LIN_V_MAX, REST_ANG_V_MAX = 0.05, 0.50  # m/s, rad/s
DROP_VZ_THR = -0.60
DROP_TCP_DIST = 0.20
DROP_GRACE = 3
DROP_TCP_DIST_THR = DROP_TCP_DIST

# Sampling / randomization
MACHINE_Z = 0.1275
MUG_Z_OFFSET = 0.05
MACHINE_XY_BAND = 0.1  # meters
MACHINE_OFFSET_X = 0.5
MACHINE_OFFSET_Y = 0.2

MUG_XY_BAND = 0.17  # meters
YAW_DEG = 45.0  # Degree of random rotation
GAP_MARGIN = 0.05  # m, gap between table halves
ROBOT_BASE_RADIUS = 0.5
MACHINE_CORNER_STRIP = 0.07  # meters around the +X/+Y corner
MACHINE_PUSH_XY = 0.03  # extra offset toward +X/+Y after sampling

# Misc
ZERO_POSITION = (0, 0, 0)
MUG_TARGET_LOCAL = (0.0, 0.05, 0.05)  # Local offset for mug target (handle)


@register_env("bimanual_make_coffee")
class BimanualMakeCoffeeEnv(BaseEnv):
    """Place a mug on the tray of a coffee machine."""

    allowed_modes = ("single",)

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
        # Runtime gates / caches
        self._resting: int = 0
        self._drops: int = 0

        # Cached machine AABB and derived tray region
        self._mach_lo: torch.Tensor | None = None  # (3,)
        self._mach_hi: torch.Tensor | None = None  # (3,)
        self._mach_bottom_z: float | None = None
        self._tray_lo: torch.Tensor | None = None  # (2,) xy only
        self._tray_hi: torch.Tensor | None = None  # (2,) xy only

        # Last-step booleans for debug printing
        self._last_success: dict[str, bool] = {}
        self._last_failure: dict[str, bool] = {}

    # Scene --------------------------------------------------------------
    def _setup_scene(self) -> None:
        machine_path = get_object_path("partnet/nespresso_machine")
        mug_path = get_object_path("kitchen/mug")

        # Coffee machine body
        self.machine = self.scene.add_entity(
            morph=gs.morphs.URDF(
                file=str(machine_path),
                scale=MACHINE_SCALE,
                pos=ZERO_POSITION,
                euler=(0.0, 0.0, 0.0),
                fixed=True,
            ),
            material=gs.materials.Rigid(),
        )

        # Mug to place on the tray
        self.mug = self.scene.add_entity(
            morph=gs.morphs.MJCF(
                file=str(mug_path),
                scale=MUG_SCALE,
                pos=ZERO_POSITION,
                euler=(0.0, 0.0, 0.0),
            ),
            material=gs.materials.Rigid(),
        )

        # Target point on the mug (e.g., handle)
        self.mug_target = self.scene.add_entity(
            morph=gs.morphs.Sphere(
                radius=0.01,
                collision=False,
                fixed=True,
                pos=MUG_TARGET_LOCAL,
            ),
            material=gs.materials.Rigid(),
            surface=gs.surfaces.Default(color=(255, 0.0, 0.0)),
        )
        self.scene.link_entities(
            parent_entity=self.mug,
            child_entity=self.mug_target,
            parent_link_name=self.mug.links[0].name,
            child_link_name=self.mug_target.links[0].name,
        )

        self.machine_box = self.world_aabb.half("y", "high")
        self.mug_box = self.world_aabb.half("y", "low").half("y", "low")

        # away from the robot arm
        self.objects_side_x = self.world_aabb.half("x", "high")

        self.mug_box.min[0] = self.objects_side_x.min[0]
        self.machine_box.min[0] = self.objects_side_x.min[0] + MACHINE_OFFSET_X
        self.machine_box.min[1] += MACHINE_OFFSET_Y

    # Reset --------------------------------------------------------------
    def _on_episode_start(self, envs_idx: torch.Tensor | None) -> None:
        self._resting = 0
        self._drops = 0

        # -----------------------------------------------------------------
        mug_pos = sample_in_aabb_center_xyz_band(
            self.mug_box,
            band_xyz=(MUG_XY_BAND, MUG_XY_BAND, 0),
            range_z=(MUG_Z_OFFSET, MUG_Z_OFFSET),
            env_idx=envs_idx,
        )

        machine_pos = sample_in_aabb_center_xyz_band(
            self.machine_box,
            range_x=(
                float(self.machine_box.max[0]) - MACHINE_CORNER_STRIP,
                float(self.machine_box.max[0]),
            ),
            range_y=(
                float(self.machine_box.max[1])
                - MACHINE_OFFSET_Y
                - MACHINE_CORNER_STRIP,
                float(self.machine_box.max[1]) - MACHINE_OFFSET_Y,
            ),
            range_z=(MACHINE_Z, MACHINE_Z),
            env_idx=envs_idx,
        )
        machine_pos = machine_pos.reshape(-1, 3)
        machine_pos[:, 0] += MACHINE_PUSH_XY
        machine_pos[:, 1] += MACHINE_PUSH_XY
        machine_pos = self.machine_box.clamp(machine_pos)
        if machine_pos.shape[0] == 1 and envs_idx is None:
            machine_pos = machine_pos.squeeze(0)

        # -----------------------------------------------------------------

        # Comment this if you want fixed locations and uncomment above
        # ------------------------------------------------------------------------------------
        # Randomize which side the machine and mug are on
        # if self.np_random.uniform() > 0.5:
        #     # Mug on low Y, Machine on high Y
        #     mug_side_box = self.world_aabb.half("y", "low")
        #     mug_side_box.min[1] = max(mug_side_box.min[1], safe_min_y)
        #     mug_side_box.min[0] = max(mug_side_box.min[0], safe_min_x)

        #     mach_side_box = self.world_aabb.half("y", "high")
        #     mach_side_box.min[1] = max(mach_side_box.min[1], safe_min_y)
        #     mach_side_box.min[0] = max(mach_side_box.min[0], safe_min_x)
        #     mach_side_box.min[1] += GAP_MARGIN
        # else:
        #     # Machine on low Y, Mug on high Y
        #     mach_side_box = self.world_aabb.half("y", "low")
        #     mach_side_box.min[1] = max(mach_side_box.min[1], safe_min_y)
        #     mach_side_box.min[0] = max(mach_side_box.min[0], safe_min_x)

        #     mug_side_box = self.world_aabb.half("y", "high")
        #     mug_side_box.min[1] = max(mug_side_box.min[1], safe_min_y)
        #     mug_side_box.min[0] = max(mug_side_box.min[0], safe_min_x)
        #     mug_side_box.min[1] += GAP_MARGIN

        # # Sample positions wrt. AABB
        # machine_pos = sample_in_aabb_center_xyz_band(
        #     mach_side_box,
        #     band_xyz=(MACHINE_XY_BAND, MACHINE_XY_BAND, 0.0),
        #     range_z=(MACHINE_Z, MACHINE_Z),
        #     env_idx=envs_idx,
        # )

        # mug_pos = sample_in_aabb_center_xyz_band(
        #     mug_side_box,
        #     band_xyz=(MUG_XY_BAND, MUG_XY_BAND, 0.0),
        #     range_z=(MUG_Z_OFFSET, MUG_Z_OFFSET), # Z is relative to table
        #     env_idx=envs_idx,
        # )
        # -----------------------------------------------------------------

        # Apply random yaws
        yaw_limit_rad = math.radians(YAW_DEG)

        # make it more prone to face the robot
        yaw_randomizer = YawRandomizer(
            yaw_range=(yaw_limit_rad / 3, yaw_limit_rad),
        )

        self.machine.set_pos(machine_pos, envs_idx=envs_idx)

        self.machine.set_quat(
            yaw_randomizer.quat(env_idx=envs_idx),
            envs_idx=envs_idx,
        )

        self.mug.set_pos(mug_pos, envs_idx=envs_idx)
        self.mug.set_quat(yaw_randomizer.quat(env_idx=envs_idx), envs_idx=envs_idx)

        # Save machine AABB and compute tray rectangle
        machine_aabb = self.machine.get_AABB().to(self.device)  # (2, 3)
        self._mach_lo = machine_aabb[0]
        self._mach_hi = machine_aabb[1]
        self._mach_bottom_z = float(self._mach_lo[2].item())

        machine_center_x = float((self._mach_lo[0] + self._mach_hi[0]) * 0.5)
        machine_center_y = float((self._mach_lo[1] + self._mach_hi[1]) * 0.5)

        # Calculate the tray's target center, offset from the machine's center
        # The tray is where we need to place the mug
        tray_center_x = machine_center_x + TRAY_OFF_X
        tray_center_y = machine_center_y + TRAY_OFF_Y

        # Calculate the min/max bounds of the tray acceptance region
        tray_min_x = tray_center_x - TRAY_HALF_SX
        tray_max_x = tray_center_x + TRAY_HALF_SX
        tray_min_y = tray_center_y - TRAY_HALF_SY
        tray_max_y = tray_center_y + TRAY_HALF_SY

        self._tray_min = (tray_min_x, tray_min_y)
        self.tray_max = (tray_max_x, tray_max_y)

    # Observations -------------------------------------------------------
    def _get_extra_obs(self) -> dict[str, Any]:
        return {
            "machine_pos": self.machine.get_pos(),
            "mug_pos": self.mug.get_pos(),
        }

    # Reward -------------------------------------------------------------
    # #TODO REWARD SYSTEM
    # def _compute_reward(self, obs) -> float:
    #     pass

    # # Success / Failure --------------------------------------------------
    # #TODO needs work
    # def _is_success(self, obs) -> bool:
    #     if self._instant_place_ok(obs):
    #         self._resting_count += 1
    #     else:
    #         self._resting_count = 0

    #     return self._resting_count >= REST_FRAMES

    # def _is_failure(self, obs) -> bool:
    #     if super()._is_failure(obs):
    #         return True
    #     # Outside workspace AABB
    #     outside_ws = False
    #     if self.world_aabb is not None:
    #         lo = self.world_aabb.min
    #         hi = self.world_aabb.max
    #         p = self.mug.get_pos()
    #         outside_ws = bool(torch.any(p < lo) or torch.any(p > hi))

    #     # Fast drop while TCP is far
    #     tcp = obs["state"]["gripper"]["tcp_pos"]
    #     mug_p = self.mug.get_pos()
    #     mug_v = self.mug.get_vel()
    #     far_from_tcp = torch.norm(tcp - mug_p) > DROP_TCP_DIST_THR
    #     fast_down = mug_v[2] < DROP_VZ_THR
    #     dropped_fast_now = bool(far_from_tcp and fast_down)
    #     if dropped_fast_now:
    #         self._drop_count += 1
    #     else:
    #         self._drop_count = 0

    #     self._last_failure = {
    #         "outside_ws": outside_ws,
    #         "dropped_fast": dropped_fast_now,
    #     }

    #     return outside_ws or (self._drop_count >= REST_FRAMES)

    # # Instantaneous placement check -------------------------------------
    # def _instant_place_ok(self, obs) -> bool:
    #     ready = (
    #         self._mach_lo is not None
    #         and self._mach_hi is not None
    #         and self._tray_lo is not None
    #         and self._tray_hi is not None
    #         and self._mach_bottom_z is not None
    #     )
    #     if not ready:
    #         self._last_success = {}
    #         return False

    #     mug_p = self.mug.get_pos()

    #     # 1) Inside tray rectangle on XY
    #     inside_xy = bool(
    #         (self._tray_lo[0] <= mug_p[0] <= self._tray_hi[0])
    #         and (self._tray_lo[1] <= mug_p[1] <= self._tray_hi[1])
    #     )
    #     if not inside_xy:
    #         self._last_success = {
    #             "inside_xy": False,
    #             "z_band": False,
    #             "resting": False,
    #             "tcp_clear": False,
    #             "tcp_far": False,
    #         }
    #         return False

    #     # 2) Height band relative to machine bottom
    #     z = float(mug_p[2].item())
    #     bottom = float(self._mach_bottom_z)
    #     z_band = bottom <= z <= bottom + Z_TOL
    #     if not z_band:
    #         self._last_success = {
    #             "inside_xy": True,
    #             "z_band": False,
    #             "resting": False,
    #             "tcp_clear": False,
    #             "tcp_far": False,
    #         }
    #         return False

    #     # 3) TCP NOT inside machine AABB
    #     tcp = obs["state"]["gripper"]["tcp_pos"]
    #     tcp_inside_mach = bool(
    #         (self._mach_lo[0] <= tcp[0] <= self._mach_hi[0])
    #         and (self._mach_lo[1] <= tcp[1] <= self._mach_hi[1])
    #         and (self._mach_lo[2] <= tcp[2] <= self._mach_hi[2])
    #     )
    #     tcp_clear = not tcp_inside_mach
    #     if not tcp_clear:
    #         self._last_success = {
    #             "inside_xy": True,
    #             "z_band": True,
    #             "resting": False,
    #             "tcp_clear": False,
    #             "tcp_far": False,
    #         }
    #         return False

    #     # 4) TCP far from mug
    #     tcp_far = bool(torch.norm(tcp - mug_p) >= TCP_CLEARANCE)
    #     if not tcp_far:
    #         self._last_success = {
    #             "inside_xy": True,
    #             "z_band": True,
    #             "resting": False,
    #             "tcp_clear": True,
    #             "tcp_far": False,
    #         }
    #         return False

    #     # 5) Resting kinematics
    #     v = self.mug.get_vel()
    #     w = self.mug.get_ang()
    #     resting = bool(torch.norm(v) <= REST_LIN_V_MAX and torch.norm(w) <= REST_ANG_V_MAX)

    #     self._last_success = {
    #         "inside_xy": True,
    #         "z_band": True,
    #         "resting": resting,
    #         "tcp_clear": True,
    #         "tcp_far": True,
    #     }
    #     return resting

    # # Info + debug print -------------------------------------------------
    # def _get_info(self, obs) -> dict[str, Any]:
    #     mach_p = self.machine.get_pos()
    #     mug_p = self.mug.get_pos()
    #     v = self.mug.get_vel()
    #     w = self.mug.get_ang()
    #     tcp = obs["state"]["gripper"]["tcp_pos"]
    #     tcp_dist = float(torch.norm(tcp - mug_p))

    #     tray_center = None
    #     tray_half = (TRAY_HALF_SX, TRAY_HALF_SY)
    #     if self._tray_lo is not None and self._tray_hi is not None:
    #         cx = 0.5 * float(self._tray_lo[0] + self._tray_hi[0])
    #         cy = 0.5 * float(self._tray_lo[1] + self._tray_hi[1])
    #         tray_center = (cx, cy)

    #     return {
    #         "spatial": {
    #             "machine_pos": tuple(float(x) for x in mach_p.tolist()),
    #             "mug_pos": tuple(float(x) for x in mug_p.tolist()),
    #             "machine_bottom_z": self._mach_bottom_z,
    #             "tray_center": tray_center,
    #             "tray_half_size": tray_half,
    #         },
    #         "kinematics": {
    #             "mug_speed": float(torch.norm(v)),
    #             "mug_ang_speed": float(torch.norm(w)),
    #             "tcp_to_mug": tcp_dist,
    #         },
    #         "counters": {
    #             "rest": self._resting,
    #             "drops": self._drops,
    #         },
    #     }
