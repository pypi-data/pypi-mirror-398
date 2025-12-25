import numpy as np
import torch
from gymnasium import spaces
from skrl.envs.wrappers.torch.base import Wrapper


class DexsuiteLiftWrapper(Wrapper):
    """Parallel-friendly Dexsuite lift wrapper (cuda:0, reset-by-index aware)."""

    def __init__(self, env):
        super().__init__(env)
        self._device = torch.device("cuda:0")

        obs_sp = self._env.observation_space
        state_sp = obs_sp["state"]

        tcp_sp = state_sp["gripper"]["tcp_pos"]
        cube_sp = state_sp["other"]["cube_pos"]
        tgt_sp = state_sp["other"]["target_pos"]
        qpos_sp = state_sp["manipulator"]["qpos"]
        qvel_sp = state_sp["manipulator"]["qvel"]

        # optional (if present)
        try:
            act_obs_sp = state_sp["other"]["action"]
        except Exception:
            act_obs_sp = obs_sp["other"]["action"]

        self._tcp_dim = tcp_sp.shape[-1]
        self._cube_dim = cube_sp.shape[-1]
        self._tgt_dim = tgt_sp.shape[-1]
        self._qpos_dim = qpos_sp.shape[-1]
        self._qvel_dim = qvel_sp.shape[-1]
        self._actobs_dim = act_obs_sp.shape[-1]

        self._obs_dim = (
            self._tcp_dim
            + self._cube_dim
            + self._tgt_dim
            + self._qpos_dim
            + self._qvel_dim
            + self._actobs_dim
        )

        act_sp = self._env.action_space
        D = act_sp.shape[-1]
        self._act_space = spaces.Box(
            low=np.ones(D, dtype=np.float32) * act_sp.low.min(),
            high=np.ones(D, dtype=np.float32) * act_sp.high.max(),
            shape=(D,),
            dtype=np.float32,
        )

        self._obs_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(self._obs_dim,),
            dtype=np.float32,
        )

    @property
    def observation_space(self):
        return self._obs_space

    @property
    def action_space(self):
        return self._act_space

    @property
    def num_envs(self):
        return getattr(self._env, "n_envs", 1)

    @property
    def num_agents(self):
        return 1

    @property
    def device(self):
        return self._device

    # ---- helpers ----
    def _grab(self, obs, path):
        x = obs
        for p in path:
            x = x[p]
        t = torch.as_tensor(x, device=self._device, dtype=torch.float32)
        if t.ndim == 1:
            t = t.unsqueeze(0)
        return t

    def _extract_parts(self, obs):
        tcp = self._grab(obs, ["state", "gripper", "tcp_pos"])
        cube = self._grab(obs, ["state", "other", "cube_pos"])
        tgt = self._grab(obs, ["state", "other", "target_pos"])
        qpos = self._grab(obs, ["state", "manipulator", "qpos"])
        qvel = self._grab(obs, ["state", "manipulator", "qvel"])
        act_obs = self._grab(obs, ["state", "other", "action"])
        return tcp, cube, tgt, qpos, qvel, act_obs

    def step(self, actions):
        actions = torch.as_tensor(actions, device=self._device, dtype=torch.float32)
        obs, reward, terminated, truncated, info = self._env.step(actions * 0.5)

        tcp, cube, tgt, qpos, qvel, act_obs = self._extract_parts(obs)
        observation = torch.cat([tcp, cube, tgt, qpos, qvel, act_obs], dim=-1)

        B = observation.shape[0]
        reward = torch.as_tensor(
            reward,
            device=self._device,
            dtype=torch.float32,
        ).reshape(B, 1)
        terminated = torch.as_tensor(
            terminated,
            device=self._device,
            dtype=torch.bool,
        ).reshape(B, 1)
        truncated = torch.as_tensor(
            truncated,
            device=self._device,
            dtype=torch.bool,
        ).reshape(B, 1)

        # selective reset
        done_mask = terminated[:, 0] | truncated[:, 0]
        if done_mask.any() and hasattr(self._env, "reset_env_idx"):
            reset_idx = done_mask.nonzero(as_tuple=False).squeeze(-1).cpu()
            reset_obs, _ = self._env.reset_env_idx(reset_idx)
            new_tcp, new_cube, new_tgt, new_qpos, new_qvel, new_act_obs = (
                self._extract_parts(reset_obs)
            )
            new_rows = torch.cat(
                [new_tcp, new_cube, new_tgt, new_qpos, new_qvel, new_act_obs],
                dim=-1,
            )
            observation[reset_idx] = new_rows[: len(reset_idx)]

        return observation, reward, terminated, truncated, info

    def reset(self):
        obs, info = self._env.reset()
        tcp, cube, tgt, qpos, qvel, act_obs = self._extract_parts(obs)
        observation = torch.cat([tcp, cube, tgt, qpos, qvel, act_obs], dim=-1)
        return observation, info
