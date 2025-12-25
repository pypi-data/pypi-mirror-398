from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import genesis as gs
import gymnasium as gym
import torch
from gymnasium import spaces

from dexsuite.core.camera import CameraSystem
from dexsuite.core.robots.bimanual_robot import BimanualRobot
from dexsuite.core.robots.factory import make_robot_from_options
from dexsuite.models.arena import Arena
from dexsuite.options import (
    CamerasOptions,
    RobotOptions,
    SimOptions,
)
from dexsuite.utils import dict_to_space, get_device, set_n_envs
from dexsuite.utils.status import building, show_action_terms, show_intro_env
from dexsuite.utils.workspace_utils import (
    compute_world_aabb_from_options,
    draw_workspace_corners,
)


class BaseEnv(gym.Env):
    """Base environment that takes component dataclasses directly."""

    def __init__(
        self,
        *,
        robot_options: RobotOptions,
        cameras_options: CamerasOptions,
        sim_options: SimOptions,
        render_mode: str | None = None,
        sim_dt: float | None = None,
        substeps: int | None = None,
        horizon: int | None = None,
        seed: int | None = None,
        **scene_kw,
    ):
        if seed is not None:
            torch.manual_seed(seed)

        self.sim_options = sim_options
        self.robot_options = robot_options
        self.cameras_options = cameras_options
        self.device = get_device()

        self.sim_dt = float(sim_dt)
        self.substeps = int(substeps) if substeps is not None else 1
        self.horizon = horizon
        self.n_envs = int(self.sim_options.n_envs)
        self.control_dt = 1.0 / float(self.sim_options.control_hz)
        self._n_phys_per_ctrl = max(1, int(round(self.control_dt / self.sim_dt)))
        self.render_mode = render_mode
        set_n_envs(self.n_envs)

        show_intro_env(
            robot_options=self.robot_options,
            sim=self.sim_options,
            render_mode=self.render_mode,
            sim_dt=self.sim_dt,
            substeps=self.substeps,
        )

        self.scene = gs.Scene(
            gs.options.SimOptions(dt=self.sim_dt, substeps=self.substeps),
            show_viewer=(self.render_mode == "human"),
            vis_options=gs.options.VisOptions(show_world_frame=False),
            **scene_kw,
        )

        with building("Initializing Scene Entities"):
            self.arena = Arena(self.scene)

            self.robot = make_robot_from_options(
                robot_options=self.robot_options,
                scene=self.scene,
            )

            self._workspace_aabbs = compute_world_aabb_from_options(
                self.robot_options,
                self.device,
            )

            self.world_aabb = self._workspace_aabbs["union"]

            if self.robot_options.visualize_aabb and self.world_aabb is not None:
                draw_workspace_corners(self.scene, self.world_aabb, radius=0.01)

            self.camera_sys = CameraSystem(
                self.scene,
                self.robot,
                cam_options=self.cameras_options,
                gui=False,
            )

            self._built = False
            self._setup_scene()
            self.camera_sys.create()

        with building("Building Physics Scene"):
            if self.n_envs > 1:
                self.scene.build(n_envs=self.n_envs, env_spacing=(3.0, 3.0))
            else:
                self.scene.build()

        with building("Finalizing Controllers & API"):
            self.camera_sys.mount()
            self.robot.install_pd()
            self._built = True
            self._act_dim = int(self.robot._act_dim)

            if self.n_envs == 1:
                self._current_action = torch.zeros(
                    self._act_dim,
                    dtype=torch.float32,
                    device=self.device,
                )
            else:
                self._current_action = torch.zeros(
                    (self.n_envs, self._act_dim),
                    dtype=torch.float32,
                    device=self.device,
                )

            self._last_action = torch.zeros_like(self._current_action)
            self._t = torch.zeros(self.n_envs, dtype=torch.int64, device=self.device)
            self._on_episode_start(envs_idx=None)
            self.robot.reset()
            self.scene.step()
            self._render_mode = render_mode
            self.action_space = self.robot.action_space
            self.observation_space = self._build_obs_space()

        show_action_terms(self.robot._layout)

    def get_workspace_aabbs(self) -> dict[str, Any]:
        """Return workspace AABB info dict with keys: union, left, right, overlap."""
        return self._workspace_aabbs

    def reset(self, *, seed: int | None = None, options: Any | None = None):
        if seed is not None:
            torch.manual_seed(seed)
        self.scene.reset()
        self._on_episode_start(envs_idx=None)
        self.robot.reset()
        self.scene.step()
        self._t = torch.zeros(self.n_envs, dtype=torch.int64, device=self.device)
        self._last_action.zero_()
        return self._make_obs(), {}

    def reset_env_idx(
        self,
        env_idx: torch.Tensor | Sequence[int] | None = None,
        *,
        seed: int | None = None,
    ):
        """Reset a subset of envs (parallelized) or the whole scene (single env or None).
        Returns (obs, info_like).
        """
        if not self._built:
            raise RuntimeError("Environment not built. Call reset() first.")

        if self.n_envs == 1 or env_idx is None:
            self.scene.reset()
            self._on_episode_start(envs_idx=None)
            self.robot.reset()
            self.scene.step()
            self._t.zero_()
            self._last_action.zero_()
            return self._make_obs(), {}

        env_idx_t = torch.as_tensor(env_idx, dtype=torch.long, device="cpu").view(-1)
        if not ((env_idx_t >= 0) & (env_idx_t < self.n_envs)).all().item():
            raise ValueError(
                f"env_idx {env_idx_t.tolist()} out of range [0, {self.n_envs})",
            )

        self._on_episode_start(envs_idx=env_idx_t)
        self.robot.reset(env_idx_t)
        self.scene.step()
        self._t[env_idx_t] = 0
        self._last_action[env_idx_t] = 0.0
        return self._make_obs(), {}

    def step(self, action):
        action = validate_action_input(
            action,
            self._act_dim,
            self.n_envs,
            device=self.device,
        )
        self._current_action.copy_(action.detach())

        action_for_robot = action if self.n_envs > 1 else action.unsqueeze(0)
        self.robot.apply_action_validated(action_for_robot)
        self._step()

        for _ in range(self._n_phys_per_ctrl):
            self.scene.step()

        obs = self._make_obs()
        reward = self._compute_reward(obs)
        self._t += 1

        success = torch.as_tensor(
            self._is_success(obs),
            dtype=torch.bool,
            device=self.device,
        )
        failure_mask = torch.as_tensor(
            self._is_failure(obs),
            dtype=torch.bool,
            device=self.device,
        )

        failure = (~success) & failure_mask
        terminated = success | failure

        if self.horizon is None:
            truncated = torch.zeros_like(
                terminated,
                dtype=torch.bool,
                device=self.device,
            )
        else:
            truncated = (self._t >= self.horizon).to(torch.bool)

        info = self._get_info(obs)
        info.setdefault("success", success)
        info.setdefault("failure", failure)
        info.setdefault("terminated", terminated)
        info.setdefault("truncated", truncated)

        reset_mask = terminated | truncated
        info["needs_reset"] = reset_mask
        if reset_mask.any().item():
            if self.n_envs == 1:
                obs, _ = self.reset_env_idx(None)
            else:
                reset_idx = reset_mask.nonzero(as_tuple=False).squeeze(-1)
                obs, _ = self.reset_env_idx(reset_idx)

        self._last_action.copy_(action.detach())

        return obs, reward, terminated, truncated, info

    def render(self, mode: str = "human") -> dict[str, torch.Tensor] | None:
        """Render the environment.

        Args:
            mode (str): The mode to render with.
                - "human": Render to the interactive viewer. This is typically
                handled automatically while stepping when render_mode is "human".
                Calling this manually has no effect.
                - "rgb_array": Returns a dictionary of images from all
                attached cameras.

        Returns:
            A dictionary mapping camera names to rendered (H, W, C) image
            tensors if mode is "rgb_array" and cameras exist. Returns None if
            mode is "human" or if no cameras are available.

        Raises:
            ValueError: If an unsupported render mode is requested.
        """
        if mode == "human":
            return None

        if mode == "rgb_array":
            if self.camera_sys and self.camera_sys.num_cameras > 0:
                return self.camera_sys.render_all()
            else:
                return None

        raise ValueError(
            f"Unknown render mode: '{mode}'. "
            "Supported modes are 'human' and 'rgb_array'.",
        )

    def close(self) -> None:
        if self.scene.viewer:
            self.scene.viewer.stop()

    def _setup_scene(self) -> None:
        pass

    def _step(self) -> None:
        pass

    def _on_episode_start(self, envs_idx: torch.Tensor | None) -> None:
        pass

    def _get_extra_obs(self) -> dict[str, Any]:
        return {}

    def _compute_reward(self, obs) -> torch.Tensor:
        return torch.tensor(
            [0.0] * self.n_envs,
            dtype=torch.float32,
            device=self.device,
        )

    def _get_info(self, obs) -> dict[str, Any]:
        return {
            "episode": {"step": self._t, "horizon": self.horizon},
        }

    def _is_success(self, obs) -> torch.Tensor:
        return torch.zeros(self.n_envs, dtype=torch.bool, device=self.device)

    def _is_failure(self, obs) -> torch.Tensor:
        return torch.zeros(self.n_envs, dtype=torch.bool, device=self.device)

    def _build_obs_space(self) -> spaces.Dict:
        proto_state = self.robot.get_obs()
        extra = self._get_extra_obs() or {}
        if extra:
            proto_state.setdefault("other", {}).update(extra)

        proto_state.setdefault("other", {})["action"] = self._last_action
        proto_state["other"]["last_action"] = self._last_action.clone()
        state_space = dict_to_space(proto_state)
        cams_space_dict = self.camera_sys.obs_space()
        cameras_space = spaces.Dict(cams_space_dict)
        return spaces.Dict(state=state_space, cameras=cameras_space)

    def _make_obs(self) -> dict[str, Any]:
        state = self.robot.get_obs()

        extras = self._get_extra_obs() or {}
        for k, v in extras.items():
            tensor = v if torch.is_tensor(v) else torch.as_tensor(v, device=self.device)
            state.setdefault("other", {})[k] = tensor

        state.setdefault("other", {})["action"] = self._current_action.clone()
        state.setdefault("other", {})["last_action"] = self._last_action.clone()

        cameras = self.camera_sys.render_all()
        return {"state": state, "cameras": cameras}

    def _is_tcp_outside_workspace(self, obs) -> torch.Tensor:
        """Return (n_envs,) bool: True where tool center point (TCP) is outside the world AABB (robot's workspace)."""
        if isinstance(self.robot, BimanualRobot):
            left_inside = self.world_aabb.contains(
                obs["state"]["left"]["gripper"]["tcp_pos"],
            )
            right_inside = self.world_aabb.contains(
                obs["state"]["right"]["gripper"]["tcp_pos"],
            )
            return ~(left_inside & right_inside)
        else:
            inside = self.world_aabb.contains(obs["state"]["gripper"]["tcp_pos"])
            return ~inside


def validate_action_input(
    action,
    action_dim: int,
    n_envs: int,
    *,
    device: torch.device,
) -> torch.Tensor:
    """Validate and normalize actions passed to env.step().

    DexSuite uses a flat action vector (single: (D,), batched: (n_envs, D)).

    This function is intentionally permissive at the boundary:
    - Accepts torch tensors, numpy arrays, and Python sequences.
    - Casts to float32 and moves to the environment device.
    - For batched envs, a single (D,) action is broadcast to (n_envs, D).
    """
    if torch.is_tensor(action):
        action_t = action
    else:
        action_t = torch.as_tensor(action, dtype=torch.float32, device=device)

    if action_t.dtype != torch.float32:
        action_t = action_t.to(dtype=torch.float32)
    if action_t.device != device:
        action_t = action_t.to(device=device)

    D = action_dim
    if n_envs == 1:
        if action_t.ndim == 1:
            if action_t.numel() != D:
                raise ValueError(f"Expected action len {D}, got {action_t.numel()}")
            return action_t
        elif action_t.ndim == 2:
            if action_t.shape != (1, D):
                raise ValueError(
                    f"Single env expects shape (1,{D}), got {tuple(action_t.shape)}",
                )
            return action_t[0]
        else:
            raise ValueError(
                f"Single env expects (D,) or (1,D); got ndim={action_t.ndim}",
            )
    else:
        if action_t.ndim == 1 and action_t.numel() == D:
            return action_t.view(1, D).repeat(n_envs, 1)
        if action_t.ndim == 2 and action_t.shape == (1, D):
            return action_t.repeat(n_envs, 1)
        if action_t.ndim != 2 or action_t.shape != (n_envs, D):
            raise ValueError(
                f"Batched env expects {(n_envs, D)}, got {tuple(action_t.shape)}",
            )
    return action_t
