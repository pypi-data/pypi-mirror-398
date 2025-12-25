"""Pick-and-place pan environment (bimanual, rigid objects).

The robot must pick a frying pan from a random burner on the hot plate and
place it onto a kitchen mat.

Success:
  Success is declared when the pan is resting on the mat inside an inner XY
  region, the pan bottom is within a small Z tolerance, and both TCPs are clear
  of the pan for a few consecutive frames.

Failure:
  Failure is declared if the pan leaves the workspace AABB or the pan drops fast
  while the TCPs are far away.

Reward:
  Sparse. Returns 1.0 when the episode succeeds, otherwise 0.0.
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
    sample_around_point_xy,
    sample_index,
)

# Simulation
SIM_DT = 0.01
SUBSTEPS = 1
HORIZON = 700

# Success / failure thresholds
XY_MARGIN = 0.04
Z_TOL = 0.02
TCP_CLEARANCE = 0.08
REST_FRAMES = 5
REST_LIN_V_MAX = 0.05
REST_ANG_V_MAX = 0.50
DROP_VZ_THR = -0.60
DROP_TCP_DIST = 0.20
DROP_GRACE = 3

# Scene
HOT_PLATE_SCALE = 2
KITCHEN_MAT_SCALE = 0.8

# Base poses
HOT_PLATE_Z = -0.01
MAT_Z = -0.005
PAN_Z_OFFSET = 0.01  # Z offset for pan relative to hot plate

HOT_PLATE_BASE = (0.65, -0.10, -0.01)
MAT_BASE = (HOT_PLATE_BASE[0], HOT_PLATE_BASE[1] + 0.55, -0.005)

# Sampling
BURNERS_POSITIONS = [(-0.07, 0.14), (-0.10, -0.17), (0.14, 0.17), (0.12, -0.15)]
BURNER_INDICES = range(len(BURNERS_POSITIONS))
BURNERS_TENSOR = torch.tensor(BURNERS_POSITIONS, dtype=torch.float32)

PAN_HOTPLATE_SAMPLING = (0.03, 0.03)
YAW_DEG = 20.0

GAP_MARGIN = 0.05

ZERO_POSITION = (0, 0, 0)

# Mat collision box dimensions
MAT_W, MAT_L, THICK = 0.44, 0.30, 0.010

# Target point for pan
PAN_TARGET_LOCAL = (0.0, 0.0535, 0.18)

MAT_OFFSET = 1


@register_env("bimanual_pick_place_pan")
class Bimanual_PickPlacePanEnv(BaseEnv):
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
        self._resting = 0
        self._drops = 0
        self._mat_lo = self._mat_hi = self._mat_top_z = None
        self._inner_lo = self._inner_hi = None

    def _setup_scene(self) -> None:
        hp_path = get_object_path("kitchen/hot_plate")
        mat_path = get_object_path("kitchen/kitchen_mat")
        pan_path = get_object_path("kitchen/pan")

        self.hot_plate = self.scene.add_entity(
            gs.morphs.MJCF(
                file=str(hp_path),
                scale=HOT_PLATE_SCALE,
                pos=HOT_PLATE_BASE,
                euler=(0.0, 0.0, -90.0),
                collision=False,
                visualization=True,
            ),
            material=gs.materials.Rigid(),
        )

        self.kitchen_mat = self.scene.add_entity(
            gs.morphs.MJCF(
                file=str(mat_path),
                scale=KITCHEN_MAT_SCALE,
                pos=MAT_BASE,
                euler=(90.0, 0.0, 0.0),
                collision=False,
                visualization=True,
            ),
        )

        self.mat_collision = self.scene.add_entity(
            gs.morphs.Box(
                size=(MAT_W, MAT_L, THICK),
                pos=(MAT_BASE[0], MAT_BASE[1], MAT_BASE[2] + THICK * 0.5),
                euler=(0.0, 0.0, 0.0),
                collision=True,
                visualization=False,
                fixed=True,
            ),
            material=gs.materials.Rigid(),
        )

        self.pan = self.scene.add_entity(
            gs.morphs.MJCF(file=str(pan_path), collision=True, pos=HOT_PLATE_BASE),
            material=gs.materials.Rigid(),
            surface=gs.surfaces.Aluminium(),
        )

        self.pan_target = self.scene.add_entity(
            gs.morphs.Sphere(
                radius=0.01,
                collision=False,
                quat=(0.5, -0.5, 0.5, 0.5),
                fixed=True,
                pos=PAN_TARGET_LOCAL,
            ),
            material=gs.materials.Rigid(),
            surface=gs.surfaces.Default(color=(255, 0.0, 0.0)),
        )

        # TODO: Update the MUG's placing position ball
        self.scene.link_entities(
            parent_entity=self.pan,
            child_entity=self.pan_target,
            parent_link_name=self.pan.links[0].name,
            child_link_name=self.pan_target.links[0].name,
        )

        # self.hot_plate_box = self.world_aabb.half("y", "low")
        # self.mat_box = self.world_aabb.half("y", "high")

        # self.objects_side_x = self.world_aabb.half("x", "high")

        # self.hot_plate_box.min[0] = self.objects_side_x.min[0]
        # self.mat_box.min[0] = self.objects_side_x.min[0]

    def _on_episode_start(self, envs_idx: torch.Tensor | None) -> None:
        self._resting = 0
        self._drops = 0

        # SET HOT PLATES AND MAT CLOSE TO CENTER OF AABB
        hot_plate_base = self.world_aabb.half("y", "low").center()
        hot_plate_base[0] *= 1.2
        hot_plate_base[2] = -0.01
        self.hot_plate.set_pos(hot_plate_base, envs_idx=envs_idx)
        mat_base = self.world_aabb.half("y", "high").center()
        mat_base[2] = -0.005
        self.kitchen_mat.set_pos(mat_base, envs_idx=envs_idx)
        mat_collision_base = (mat_base[0], mat_base[1], mat_base[2] + THICK * 0.5)
        self.mat_collision.set_pos(mat_collision_base, envs_idx=envs_idx)

        # if self.np_random.uniform() > 0.5:
        #     # Mat on low Y (near), Hotplate on high Y (far)
        #     mat_side_box = self.world_aabb.half("y", "low")
        #     mat_side_box.max[1] -= GAP_MARGIN
        #     hp_side_box = self.world_aabb.half("y", "high")
        #     hp_side_box.min[1] += GAP_MARGINenvs_idx
        # else:
        #     # Hotplate on low Y (near), Mat on high Y (far)
        #     hp_side_box = self.world_aabb.half("y", "low")
        #     hp_side_box.max[1] -= GAP_MARGIN
        #     mat_side_box = self.world_aabb.half("y", "high")
        #     mat_side_box.min[1] += GAP_MARGIN

        # hot_plate_pos = sample_in_aabb_center_xyz_band(
        #     self.hot_plate_box,
        #     band_xyz = (HOT_PLATE_XY_BAND, HOT_PLATE_XY_BAND, 0.0),
        #     range_z = (HOT_PLATE_Z, HOT_PLATE_Z),
        #     env_idx = envs_idx
        # )

        # mat_pos = sample_in_aabb_center_xyz_band(
        #     self.mat_box,
        #     band_xyz = (MAT_XY_BAND, MAT_XY_BAND, 0.0),
        #     range_z = (MAT_Z, MAT_Z),
        #     env_idx = envs_idx,
        # )

        burner_index = sample_index(
            BURNER_INDICES,
            envs_idx,
        )  # get a random burner index i.e. choose a random burner to place the pan on
        burner_offset_xy = BURNERS_TENSOR[burner_index.squeeze(-1)].to(
            self.device,
        )  # make it shape (N,) instead of (N,1)
        hot_plate_center_xy = torch.tensor(
            hot_plate_base[:2],
            dtype=torch.float32,
            device=self.device,
        )  # get the hotplate's base XY as a tensor
        burner_world_xy = (
            hot_plate_center_xy + burner_offset_xy
        )  # position of the burner with the offset of the burners relative to the hotplate

        pan_pos = sample_around_point_xy(
            anchor_xy=burner_world_xy,  # Anchor to one of the hotplate's burners
            band_xy=PAN_HOTPLATE_SAMPLING,
            z=float(HOT_PLATE_Z + PAN_Z_OFFSET),
            mode="circle",
            env_idx=envs_idx,
        )

        # mat_collision_pos = (
        #     mat_pos[0],
        #     mat_pos[1],
        #     mat_pos[2] + THICK * 0.5,
        # )

        yaw_half_range_rad = math.radians(YAW_DEG)
        yaw_randomizer = YawRandomizer(
            yaw_range=(-yaw_half_range_rad, yaw_half_range_rad),
        )

        # self.kitchen_mat.set_pos(mat_pos, envs_idx=envs_idx)
        # self.hot_plate.set_pos(hot_plate_pos, envs_idx=envs_idx)
        self.pan.set_pos(pan_pos, envs_idx=envs_idx)
        # self.mat_collision.set_pos(mat_collision_pos, envs_idx=envs_idx)

        # self.hot_plate.set_quat(yaw_rand.quat(), relative=True)
        # self.kitchen_mat.set_quat(yaw_rand.quat(), relative=True)

        pan_flat_base_quat = (
            0.5,
            0.5,
            -0.5,
            -0.5,
        )  # Make the pan lay flat (default is vertical)
        pan_world_quat = yaw_randomizer.quat(
            base_quat=pan_flat_base_quat,
            frame="local",
            env_idx=envs_idx,
        )  # random yaw
        self.pan.set_quat(pan_world_quat, envs_idx=envs_idx)  # flat + rnadom yaw

        # Get AABB from the collision box, not the visual mat
        mat_lo, mat_hi = self.mat_collision.get_AABB()
        self.mat_lo, self.mat_hi = mat_lo.to(self.device), mat_hi.to(self.device)

        # mat_top_z is the top surface of the collision box
        self._mat_top_z = float(self.mat_hi[2])

        # Get inner bounds for success
        self._inner_lo = self.mat_lo[:2] + XY_MARGIN
        self._inner_hi = self.mat_hi[:2] - XY_MARGIN

    # def _get_extra_obs(self) -> dict[str, Any]:
    #     """Return ONLY tensor-like leaves (no nested dicts) so BaseEnv._make_obs can torch.as_tensor() them.
    #     Includes the handle/pan-target world pose + useful scalars for logging.
    #     """
    #     dev = self.device

    #     # World poses (already torch Tensors from Genesis)
    #     pan_pos = self.pan.get_pos()  # (3,)
    #     mat_pos = self.kitchen_mat.get_pos()  # (3,)
    #     pan_target_pos = self.pan_target.get_pos()  # (3,)
    #     pan_target_quat = self.pan_target.get_quat()  # (4,) wxyz

    #     # If _mat_top_z wasn't set yet, fall back to mat height; otherwise use stored value
    #     if self._mat_top_z is not None:
    #         mat_top_z = torch.tensor(self._mat_top_z, dtype=torch.float32, device=dev)
    #     else:
    #         # defensive fallback (shouldn't be needed because _on_episode_start runs first)
    #         mat_top_z = torch.tensor(
    #             float(mat_pos[2].item()) + THICK * 0.5, dtype=torch.float32, device=dev
    #         )

    #     # Pan kinematics (magnitudes, float32)
    #     lin_v = torch.norm(self.pan.get_vel()).to(dtype=torch.float32)
    #     ang_v = torch.norm(self.pan.get_ang()).to(dtype=torch.float32)

    #     # Episode counters (store as float32 scalars to keep obs space homogeneous)
    #     rest_ctr = torch.tensor(float(self._resting), dtype=torch.float32, device=dev)
    #     drop_ctr = torch.tensor(float(self._drops), dtype=torch.float32, device=dev)

    #     return {
    #         "pan_pos": pan_pos,
    #         "mat_pos": mat_pos,
    #         "pan_target_pos": pan_target_pos,
    #         "pan_target_quat": pan_target_quat,
    #         "mat_top_z": mat_top_z,
    #         "pan_lin_v": lin_v,
    #         "pan_ang_v": ang_v,
    #         "rest_counter": rest_ctr,
    #         "drop_counter": drop_ctr,
    #     }

    # def _compute_reward(self, obs) -> float:
    #     return 1.0 if self._is_success(obs) else 0.0

    # def _is_success(self, obs) -> bool:
    #     if any(v is None for v in (self._inner_lo, self._inner_hi, self._mat_top_z)):
    #         return False  # Bounds not set yet

    #     p = self.pan.get_pos()
    #     v = self.pan.get_vel()
    #     w = self.pan.get_ang()
    #     tcp = obs["state"]["gripper"]["tcp_pos"]

    #     xy_ok = (self._inner_lo[0] <= p[0] <= self._inner_hi[0]) and (
    #         self._inner_lo[1] <= p[1] <= self._inner_hi[1]
    #     )

    #     pan_aabb = self.pan.get_AABB().to(self.device)
    #     pan_bottom_z = pan_aabb[0, 2]
    #     z_ok = abs(float(pan_bottom_z.item()) - self._mat_top_z) <= Z_TOL

    #     pan_lo, pan_hi = pan_aabb[0], pan_aabb[1]
    #     tcp_overlap = (
    #         (pan_lo[0] <= tcp[0] <= pan_hi[0])
    #         and (pan_lo[1] <= tcp[1] <= pan_hi[1])
    #         and (pan_lo[2] <= tcp[2] <= pan_hi[2])
    #     )
    #     tcp_clear = not tcp_overlap

    #     clamped = torch.minimum(torch.maximum(tcp, pan_lo.to(tcp.device)), pan_hi.to(tcp.device))
    #     tcp_far = torch.linalg.vector_norm(tcp - clamped) >= TCP_CLEARANCE

    #     rest = (torch.norm(v) <= REST_LIN_V_MAX) and (torch.norm(w) <= REST_ANG_V_MAX)

    #     good = xy_ok and z_ok and tcp_clear and tcp_far and rest
    #     self._resting = self._resting + 1 if good else 0
    #     return self._resting >= REST_FRAMES

    # # TODO Pushing is the pan -> failure
    # # TODO Flipping the pan -> failure
    # #TODO If the pan was dropped midway -> failure
    # def _is_failure(self, obs) -> bool:
    #     if super()._is_failure(obs):
    #         return True

    #     outside_ws = False
    #     if self.world_aabb is not None:
    #         lo, hi = self.world_aabb.min, self.world_aabb.max
    #         pan_lo, pan_hi = self.pan.get_AABB()

    #         # Move lo and hi to the same device as the pan tensors
    #         lo_gpu = lo.to(pan_hi.device)
    #         hi_gpu = hi.to(pan_hi.device)

    #         outside_ws = ((pan_hi < lo_gpu).any() or (pan_lo > hi_gpu).any()).item()

    #     tcp = obs["state"]["gripper"]["tcp_pos"]
    #     p = self.pan.get_pos()
    #     v = self.pan.get_vel()
    #     far = torch.norm(p - tcp) > DROP_TCP_DIST
    #     fast_down = v[2] < DROP_VZ_THR
    #     drop_now = bool(far and fast_down)
    #     self._drops = self._drops + 1 if drop_now else 0

    #     return outside_ws or (self._drops >= DROP_GRACE)

    # def _get_info(self, obs) -> dict[str, Any]:
    #     p = self.pan.get_pos()
    #     v = self.pan.get_vel()
    #     w = self.pan.get_ang()
    #     return {
    #         "spatial": {
    #             "pan_pos": tuple(float(x) for x in p.tolist()),
    #             "mat_top_z": self._mat_top_z,
    #         },
    #         "kinematics": {
    #             "lin_v": float(torch.norm(v)),
    #             "ang_v": float(torch.norm(w)),
    #         },
    #         "counters": {"rest": self._resting, "drops": self._drops},
    #     }
