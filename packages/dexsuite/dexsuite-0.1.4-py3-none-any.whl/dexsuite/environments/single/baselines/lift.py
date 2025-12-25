"""Lift environment (single-arm baseline).

This task spawns a single cube in the robot workspace and asks the agent to lift
it to a fixed height. The environment is parallel-safe: resets accept an
optional envs_idx subset for batched simulation.

Entities:
  - cube: A rigid cube that starts on the table/ground.
  - goal: A fixed, non-colliding sphere placed above the cube spawn.

Extra observations (under obs['state']['other']):
  - cube_pos, cube_quat
  - target_pos (goal sphere position)

Success:
  The cube reaches the target height (within LIFT_EPS) and its XY position is
  close to the target.

Failure:
  The TCP leaves the workspace AABB (see BaseEnv._is_tcp_outside_workspace).
"""

from __future__ import annotations

import genesis as gs
import torch

from dexsuite.core.registry import register_env
from dexsuite.environments.base_env import BaseEnv
from dexsuite.utils.randomizers import sample_in_aabb_center_xy_band

# Simulation
SIM_DT = 0.01
SUBSTEPS = 1
HORIZON = 600

# Task
CUBE_SIZE = 0.05
GOAL_R = 0.02
GOAL_UP = 0.20 + CUBE_SIZE / 2.0
LIFT_EPS = 0.01

# Reward shaping (kept for tuning; not all are used directly)
CENTER_BAND = 0.25
TCP_THR = 0.05
CLOSE_THR = 0.14  # grasp close threshold (m) for pinch_min
STD = 0.3

POS_TRACK_W = -0.20  # end_effector_position_tracking
POS_FINE_W = +0.10  # end_effector_position_tracking_fine_grained
GRSP_W = 0.5  # grasp reward weight
LIFT_W = 1.0  # lift reward weight
FINE_THRESH = 0.05  # meters: when the fine-grained term "hits" (ON if d < 5 cm)
ACT_RATE_W = -1.0e-4  # action_rate penalty on ||a - a_prev||^2
JOINT_VEL_W = -1.0e-4  # joint_vel   penalty on ||qdot||^2
SUCCESS_THRESHOLD = 0.03  # 3 cm success, like your docstring
SUCCESS_BONUS = 1.0  # one-time on success (optional)
TIME_PENALTY = 1.0e-3  # small per-step penalty


@register_env("lift")
class LiftEnv(BaseEnv):
    """Lift a cube to a target height above its spawn."""

    def __init__(
        self,
        *,
        robot=None,
        cameras=None,
        sim=None,
        render_mode: str | None = None,
        seed: int | None = None,
        **scene_kw,
    ):
        """Initialize the environment.

        Args:
            robot: Robot options.
            cameras: Camera options.
            sim: Simulation options.
            render_mode: Rendering mode. Use "human" to open the viewer.
            seed: Optional random seed.
            scene_kw: Additional keyword arguments forwarded to the underlying genesis.Scene.
        """
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

    def _setup_scene(self) -> None:
        """Create task entities (cube + goal marker)."""
        self.cube = self.scene.add_entity(
            gs.morphs.Box(size=(CUBE_SIZE, CUBE_SIZE, CUBE_SIZE)),
            material=gs.materials.Rigid(),
            surface=gs.surfaces.Default(color=(0.90, 0.76, 0.16)),
        )
        self.goal = self.scene.add_entity(
            gs.morphs.Sphere(radius=GOAL_R, fixed=True, collision=False),
            surface=gs.surfaces.Default(color=(1.0, 0.0, 0.0)),
        )

    def _on_episode_start(self, envs_idx: torch.Tensor | None) -> None:
        """Reset cube pose and place the goal above the cube.

        Args:
            envs_idx: Optional subset of environments to reset (batched sim).
        """
        # cube at table level
        cube_pos = sample_in_aabb_center_xy_band(
            self.world_aabb,
            band_xy=(0.1, 0.25),
            z=CUBE_SIZE / 2.0,
            env_idx=envs_idx,
            mode="square",
        )
        self.cube.set_pos(cube_pos, envs_idx=envs_idx)
        goal_pos = cube_pos + torch.as_tensor(
            [0.0, 0.0, GOAL_UP],
            device=cube_pos.device,
            dtype=cube_pos.dtype,
        )
        self.goal.set_pos(goal_pos, envs_idx=envs_idx)

    def _compute_reward(self, obs: dict) -> torch.Tensor:
        """Compute a dense lifting reward.

        Args:
            obs: Observation dict produced by BaseEnv.step.

        Returns:
            Reward tensor of shape (n_envs,).
        """
        tcp_position = obs["state"]["gripper"]["tcp_pos"]
        cube_position = obs["state"]["other"]["cube_pos"]
        joint_velocity = obs["state"]["manipulator"]["qvel"]

        # Distance-based reach
        tcp_to_cube_distance = torch.linalg.norm(tcp_position - cube_position, dim=-1)
        r_reach = -0.05 * tcp_to_cube_distance
        reach_bonus = 0.5 * torch.exp(-20 * tcp_to_cube_distance)  # small dense bonus

        # Smooth lift term
        cube_height = cube_position[..., 2]
        lift_score = torch.exp(-0.5 * ((GOAL_UP - cube_height) / 0.06) ** 2)
        r_lift = 5.0 * lift_score

        # Penalties
        r_jvel = -1e-4 * torch.sum(joint_velocity**2, dim=-1)
        r_time = -1e-4

        lift_error = torch.abs(GOAL_UP - cube_position[..., 2])
        r_height = torch.exp(-20 * lift_error)
        reward = 2.0 * r_height

        reward += r_reach + reach_bonus + r_lift + r_jvel + r_time
        return reward

    def _get_extra_obs(self) -> dict[str, torch.Tensor]:
        """Expose cube and goal poses in obs['state']['other']."""
        return {
            "cube_pos": self.cube.get_pos(),
            "cube_quat": self.cube.get_quat(),
            "target_pos": self.goal.get_pos(),
        }

    def _is_success(self, obs) -> torch.Tensor:
        """Check success based on cube proximity to the target pose."""
        cube_position = obs["state"]["other"]["cube_pos"]
        target_position = obs["state"]["other"]["target_pos"]
        # Success if cube height reaches the target height (with tolerance).
        target_z = GOAL_UP - LIFT_EPS
        is_height_reached = cube_position[..., 2] >= target_z
        xy_error = torch.linalg.norm(
            cube_position[..., :2] - target_position[..., :2],
            dim=-1,
        )

        # success if xy distance is below 5cm
        is_xy_aligned = xy_error <= 0.05
        return is_xy_aligned & is_height_reached

    def _is_failure(self, obs) -> torch.Tensor:
        """Fail the episode if the TCP leaves the workspace."""
        return self._is_tcp_outside_workspace(obs)
