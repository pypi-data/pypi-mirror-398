"""Logger integration for writing DexSuite rollouts to LeRobot datasets.

This module is only needed for data-collection scripts. It depends on the
external lerobot package and is intentionally not imported by dexsuite.utils.
"""

import datetime
import json
from pathlib import Path

import gymnasium as gym
import numpy as np
import torch
from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.datasets.utils import write_info

from dexsuite.utils.options_utils import get_ds_converter


class LeRobotLogger:
    """Record environment rollouts into a LeRobotDataset on disk."""

    def __init__(self, task, env, root_dir=None):
        """Create a LeRobot logger for an environment instance.

        Args:
            task: Task name (used in repo_id and output folder structure).
            env: DexSuite environment instance (must provide observation/action spaces
                and options attributes used by this logger).
            root_dir: Optional root directory to store datasets under. If None,
                stores under ./{task}/.
        """
        self.env = env
        self.schema = self.extract_scheme(
            self.env.observation_space,
            self.env.action_space,
            parent_key="obs",
            rgb_as="video",
        )

        self.sim = self.env.sim_options
        self.robot_options = self.env.robot_options
        self.cameras_options = self.env.cameras_options
        self.task = task
        self.fps = int(self.sim.control_hz)
        self.repo_id = ""

        if self.robot_options.type_of_robot == "single":
            manipulator = self.robot_options.single.manipulator
            if self.robot_options.single.gripper is not None:
                gripper = self.robot_options.single.gripper
                self.repo_id = f"lerobot/dexsuite_{self.task}_{manipulator}_{gripper}"
            else:
                self.repo_id = f"lerobot/dexsuite_{self.task}_{manipulator}"

        timestamp = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
        if root_dir is None:
            self.dataset_dir = Path(self.task) / f"{self.task}_{timestamp}"
        else:
            self.dataset_dir = Path(root_dir) / self.task / f"{self.task}_{timestamp}"
        info_path = self.dataset_dir / "meta" / "info.json"
        if info_path.exists():
            self.ds = LeRobotDataset(
                repo_id=self.repo_id,
                root=self.dataset_dir,
                download_videos=True,
            )
        else:
            self.ds = LeRobotDataset.create(
                repo_id=self.repo_id,
                root=self.dataset_dir,
                fps=self.fps,
                features=self.schema,
                use_videos=True,
            )
        self._metadata()

    def add_step_pre(self, obs_before, action, reward, terminated, truncated, info):
        """Add one transition to the current episode buffer."""
        frame = self._construct_frame(
            obs_before,
            reward,
            terminated,
            truncated,
            info,
            action,
        )
        self.ds.add_frame(frame)

    def save_episode(self):
        """Finalize and save the current episode to the dataset."""
        self.ds.save_episode()

    def clear_buffer(self):
        """Clear the current episode buffer without saving."""
        self.ds.clear_episode_buffer()

    def close(self):
        """Closing the logger."""
        self.ds.finalize()

    def extract_scheme(
        self,
        obs_space: gym.spaces.Dict,
        action_space: gym.spaces.Space | None = None,
        *,
        parent_key: str = "obs",
        add_action_feature: bool = False,
        action_key: str = "obs.state.other.action",
        rgb_as: str = "video",
    ) -> dict[str, dict]:
        """Build the LeRobot feature schema from an observation space.

        Args:
            obs_space: Gymnasium Dict observation space.
            action_space: Optional action space (used to populate the "action" feature).
            parent_key: Prefix for nested observation keys.
            add_action_feature: Deprecated (kept for API compatibility).
            action_key: Deprecated (kept for API compatibility).
            rgb_as: How to encode RGB observations (currently always uses "video").

        Returns:
            dict[str, dict]: Mapping of flattened feature names to dtype/shape metadata.
        """
        schema: dict[str, dict] = {}
        for key, val in obs_space.items():
            new_key = f"{parent_key}.{key}" if parent_key else key
            if isinstance(val, gym.spaces.Dict):
                schema.update(
                    self.extract_scheme(
                        val,
                        action_space,
                        parent_key=new_key,
                        rgb_as=rgb_as,
                    ),
                )
            elif isinstance(val, gym.spaces.Box):
                shape = val.shape if val.shape != () else (1,)
                if new_key.startswith("obs.cameras.") and new_key.endswith(".rgb"):
                    schema[new_key] = {"dtype": "video", "shape": shape}
                else:
                    schema[new_key] = {"dtype": str(val.dtype), "shape": shape}
        schema.update(
            {
                "reward": {"dtype": "float32", "shape": (1,)},
                "truncated": {"dtype": "bool", "shape": (1,)},
                "success": {"dtype": "bool", "shape": (1,)},
                "failure": {"dtype": "bool", "shape": (1,)},
            },
        )
        act_shape = action_space.shape
        schema["action"] = {"dtype": "float32", "shape": act_shape}
        return schema

    def _construct_frame(
        self,
        obs,
        reward,
        terminated,
        truncated,
        info,
        action,
    ):
        """Flatten a step into the LeRobot frame dict expected by LeRobotDataset."""
        frame = {}

        def flatten(o, prefix="obs"):
            for k, v in o.items():
                nk = f"{prefix}.{k}" if prefix else k
                if isinstance(v, dict):
                    flatten(v, nk)
                else:
                    frame[nk] = (
                        v.detach().cpu().numpy() if isinstance(v, torch.Tensor) else v
                    )

        flatten(obs)

        def to_np1(x, dtype):
            if isinstance(x, torch.Tensor):
                x = x.detach().cpu().numpy()
            x = np.asarray(x)
            if x.shape == ():
                x = x.reshape(
                    1,
                )
            return x.astype(dtype, copy=False)

        frame["reward"] = to_np1(reward, np.float32)
        frame["success"] = to_np1(info.get("success", False), np.bool_)
        frame["failure"] = to_np1(info.get("failure", False), np.bool_)
        frame["truncated"] = to_np1(truncated, np.bool_)
        frame["action"] = to_np1(action.detach().cpu().numpy(), np.float32)
        frame["task"] = self.task
        return frame

    def _metadata(self):
        """Write dataset metadata files (options + action layout)."""
        info = self.ds.meta.info
        self._save_layout_json()
        info["task"] = self.task
        info["options"] = self._save_options_json()
        write_info(info, self.ds.meta.root)

    def _save_layout_json(self):
        """Persist the action layout (segment breakdown) to meta/action_layout.json."""
        layout = self.env.robot._layout
        meta_dir = self.dataset_dir / "meta"
        meta_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "total_dim": layout.total_dim,
            "segments": [
                {
                    "name": ".".join(seg.name),
                    "start": int(seg.start),
                    "stop": int(seg.stop),
                    "width": int(seg.width()),
                    "ctrl_type": type(seg.ctrl).__name__,
                }
                for seg in layout.segments
            ],
        }
        with open(meta_dir / "action_layout.json", "w") as f:
            json.dump(payload, f, indent=2)

    def _save_options_json(self):
        """Persist the environment options to meta/env_config.json."""
        meta_dir = self.dataset_dir / "meta"
        meta_dir.mkdir(parents=True, exist_ok=True)
        c = get_ds_converter()
        blob = {}
        blob["task"] = self.task
        blob["options"] = {
            "sim": c.unstructure(self.sim),
            "robot": c.unstructure(self.robot_options),
            "cameras": c.unstructure(self.cameras_options),
        }
        with open(meta_dir / "env_config.json", "w") as f:
            json.dump(blob, f, indent=2)
