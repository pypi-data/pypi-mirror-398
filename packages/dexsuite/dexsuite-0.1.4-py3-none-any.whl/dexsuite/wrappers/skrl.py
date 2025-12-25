from collections.abc import Sequence
from typing import Any

import gymnasium as gym
import numpy as np
import torch
from gymnasium import spaces
from skrl.envs.wrappers.torch.base import Wrapper


class DexsuiteReachWrapper(Wrapper):
    """DexSuite reach wrapper for skrl (torch).

    The wrapper flattens the nested DexSuite observation dict into a single
    1D vector per environment and adapts reset-by-index behavior to skrl.

    Observation vector layout (per environment):
        [tcp_pos, target_pos, manipulator.qpos, manipulator.qvel, other.action]

    Notes:
        - Actions are moved to self.device and cast to float32.
        - Input actions may be shaped (B, D) or (B, 1, D); the wrapper squeezes
          the middle dimension when present.
        - Rewards and done flags are returned as shape (B, 1).
    """

    # ----------- init / spaces -----------
    def __init__(self, env: Any) -> None:
        super().__init__(env)
        self._device = torch.device("cuda:0")  # fixed device

        # ---- Inspect nested observation spaces for dims ----
        obs_sp = self._env.observation_space
        state_sp = obs_sp["state"]

        tcp_sp = state_sp["gripper"]["tcp_pos"]
        tgt_sp = state_sp["other"]["target_pos"]
        qpos_sp = state_sp["manipulator"]["qpos"]
        qvel_sp = state_sp["manipulator"]["qvel"]

        # Try to locate 'other.action' under 'state' first, then top-level
        act_obs_sp = None
        try:
            act_obs_sp = state_sp["other"]["action"]
        except Exception:
            try:
                act_obs_sp = obs_sp["other"]["action"]
            except Exception as e:
                raise KeyError(
                    'Could not find observation space for ["other"]["action"] '
                    "(tried under ['state']['other'] and top-level ['other']).",
                ) from e

        self._tcp_dim = int(tcp_sp.shape[-1])
        self._tgt_dim = int(tgt_sp.shape[-1])
        self._qpos_dim = int(qpos_sp.shape[-1])
        self._qvel_dim = int(qvel_sp.shape[-1])
        self._actobs_dim = int(
            act_obs_sp.shape[-1],
        )  # dimension of obs["..."]["action"]

        self._obs_dim = (
            self._tcp_dim
            + self._tgt_dim
            + self._qpos_dim
            + self._qvel_dim
            + self._actobs_dim
        )

        # ---- Action space: ensure per-env Box(D,) ----
        act_sp = self._env.action_space
        if isinstance(act_sp, spaces.Box) and len(act_sp.shape) > 1:
            D = int(act_sp.shape[-1])
            try:
                low = np.asarray(act_sp.low)
                high = np.asarray(act_sp.high)
                if low.shape == act_sp.shape and high.shape == act_sp.shape:
                    act_low = low.reshape(-1, D)[0].astype(np.float32)
                    act_high = high.reshape(-1, D)[0].astype(np.float32)
                else:
                    act_low = -np.ones(D, dtype=np.float32)
                    act_high = np.ones(D, dtype=np.float32)
            except Exception:
                act_low = -np.ones(D, dtype=np.float32)
                act_high = np.ones(D, dtype=np.float32)
            self._act_space = spaces.Box(
                low=act_low,
                high=act_high,
                shape=(D,),
                dtype=np.float32,
            )
        else:
            self._act_space = act_sp  # already per-env shape

        self._obs_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(self._obs_dim,),
            dtype=np.float32,
        )

    # ----------- spaces (per-env) -----------
    @property
    def observation_space(self) -> gym.Space:
        return self._obs_space

    @property
    def action_space(self) -> gym.Space:
        return self._act_space

    # ----------- vectorization metadata / device -----------
    @property
    def num_envs(self) -> int:
        return int(getattr(self._env, "n_envs", 1))

    @property
    def num_agents(self) -> int:
        # Single-agent env; prevents skrl from allocating (B, B) tensors.
        return 1

    @property
    def device(self) -> torch.device:
        return self._device

    # ----------- helpers -----------
    @staticmethod
    def _squeeze_B1D(x: torch.Tensor) -> torch.Tensor:
        # Only squeeze singleton middle dim: (B, 1, D) -> (B, D)
        if x.ndim == 3 and x.shape[1] == 1:
            return x.squeeze(1)
        return x

    @staticmethod
    def _ensure_2d(x: torch.Tensor) -> torch.Tensor:
        # Single-env (D,) -> (1, D). If already (B, D), keep.
        if x.ndim == 1:
            return x.unsqueeze(0)
        return x

    @staticmethod
    def _to_B1(x: Any, B: int, *, dtype, device) -> torch.Tensor:
        # Minimal (B, 1) tensors for skrl memory
        t = torch.as_tensor(x, dtype=dtype, device=device)
        if t.ndim == 2:
            return t if t.shape[1] == 1 else t[:, :1]
        if t.ndim == 1:
            return t.reshape(B, 1)
        if t.ndim == 0:
            return t.view(1, 1).expand(B, 1)
        return t.reshape(B, -1)[:, :1]

    def _grab_as_tensor(
        self,
        obs: Any,
        path: Sequence[str],
        *,
        dtype=torch.float32,
    ) -> torch.Tensor:
        # Walk nested dict with given path, convert to tensor on device, normalize shape to (B, D)
        node = obs
        for k in path:
            node = node[k]
        t = node if torch.is_tensor(node) else torch.as_tensor(node)
        t = self._ensure_2d(self._squeeze_B1D(t)).to(self.device, dtype=dtype)
        return t

    def _grab_first_as_tensor(
        self,
        obs: Any,
        path_options: Sequence[Sequence[str]],
        *,
        dtype=torch.float32,
    ) -> torch.Tensor:
        # Try multiple candidate paths, return the first that works
        last_err = None
        for path in path_options:
            try:
                return self._grab_as_tensor(obs, path, dtype=dtype)
            except Exception as e:
                last_err = e
                continue
        raise KeyError(
            f"None of the candidate paths exist: {path_options}",
        ) from last_err

    def _extract_parts(
        self,
        obs: Any,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        # Returns (tcp, tgt, qpos, qvel, act_obs), each (B, D*)
        tcp = self._grab_as_tensor(obs, ["state", "gripper", "tcp_pos"])
        tgt = self._grab_as_tensor(obs, ["state", "other", "target_pos"])
        qpos = self._grab_as_tensor(obs, ["state", "manipulator", "qpos"])
        qvel = self._grab_as_tensor(obs, ["state", "manipulator", "qvel"])
        act_obs = self._grab_first_as_tensor(
            obs,
            (["state", "other", "action"], ["other", "action"]),
        )

        # Align batch sizes (expand 1 to B as needed).
        B = max(
            tcp.shape[0],
            tgt.shape[0],
            qpos.shape[0],
            qvel.shape[0],
            act_obs.shape[0],
        )

        def _align(x: torch.Tensor) -> torch.Tensor:
            return (
                x
                if x.shape[0] == B
                else (x.expand(B, x.shape[1]) if x.shape[0] == 1 else x)
            )

        return _align(tcp), _align(tgt), _align(qpos), _align(qvel), _align(act_obs)

    # ----------- interaction -----------
    def step(
        self,
        actions: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, Any]:
        # actions: pass through on device, float32
        if not torch.is_tensor(actions):
            actions = torch.as_tensor(actions)
        actions = actions.to(self.device, dtype=torch.float32)

        obs, reward, terminated, truncated, info = self._env.step(actions * 0.5)

        # Build observation = [tcp, tgt, qpos, qvel, other.action]
        tcp, tgt, qpos, qvel, act_obs = self._extract_parts(obs)
        B = tcp.shape[0]
        observation = torch.cat([tcp, tgt, qpos, qvel, act_obs], dim=-1)  # (B, obs_dim)

        # reward / dones: (B, 1)
        reward2d = self._to_B1(reward, B, dtype=torch.float32, device=self._device)
        terminated2d = self._to_B1(terminated, B, dtype=torch.bool, device=self._device)
        truncated2d = self._to_B1(truncated, B, dtype=torch.bool, device=self._device)

        # selective reset-by-index (patch rows)
        done_mask = terminated2d[:, 0] | truncated2d[:, 0]  # (B,)
        if done_mask.any().item() and hasattr(self._env, "reset_env_idx"):
            reset_idx = done_mask.nonzero(as_tuple=False).squeeze(-1)  # cuda idx
            reset_idx_cpu = reset_idx.detach().long().cpu()

            reset_obs, _ = self._env.reset_env_idx(reset_idx_cpu)

            # Extract new parts after reset
            new_tcp, new_tgt, new_qpos, new_qvel, new_act_obs = self._extract_parts(
                reset_obs,
            )
            new_rows = torch.cat(
                [new_tcp, new_tgt, new_qpos, new_qvel, new_act_obs],
                dim=-1,
            )

            # Patch: handle whether reset_obs returned B rows or only len(reset_idx)
            if new_rows.shape[0] == observation.shape[0]:
                observation[reset_idx] = new_rows[reset_idx]
            elif new_rows.shape[0] == reset_idx.numel():
                observation[reset_idx] = new_rows
            else:
                observation[reset_idx] = new_rows[: reset_idx.numel()]

        return observation, reward2d, terminated2d, truncated2d, info

    def reset(self) -> tuple[torch.Tensor, Any]:
        obs, info = self._env.reset()

        tcp, tgt, qpos, qvel, act_obs = self._extract_parts(obs)
        observation = torch.cat([tcp, tgt, qpos, qvel, act_obs], dim=-1)  # (B, obs_dim)
        return observation, info

    def render(self, *args, **kwargs) -> Any:
        return self._env.render(*args, **kwargs)

    def close(self) -> None:
        self._env.close()
