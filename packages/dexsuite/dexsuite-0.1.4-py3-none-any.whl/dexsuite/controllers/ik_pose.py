"""Inverse-kinematics controller for absolute end-effector poses.

This controller directly targets an end-effector pose in task space and uses
inverse kinematics (IK) to compute a joint configuration each step.

The action is interpreted as:

[x, y, z, roll, pitch, yaw]

with translation in meters and rotation in radians (RPY) when
normalized is False.

If normalized is True (DexSuite default), the action is expected in [-1, 1].
The translational components are passed through as-is, while the rotational
components are scaled by pi so that [-1, 1] maps to [-pi, pi].
"""

from __future__ import annotations

import math

import numpy as np
import torch
from gymnasium import spaces

from dexsuite.core.registry import register_controller
from dexsuite.utils.orientation_utils import rpy_to_quat_wxyz_torch

from .base_controller import Controller


@register_controller("ik_pose")
class IKPoseController(Controller):
    """Absolute end-effector pose control via IK.

    This controller solves IK every step and then commands the resulting joint
    positions. It is useful for scripted policies, evaluation, and debugging.

    Action semantics:
        The action is a 6D absolute target
        [x, y, z, roll, pitch, yaw] in world coordinates.

    IK configuration:
        - ik_max_iters: maximum solver iterations per step.
        - ik_damping: damping factor passed to the solver.
        - ik_max_step: optional maximum step size (passed as max_step_size to the
          Genesis IK API).
        - ik_init: IK seed selection:
          - "home": use the model's home_q if available, otherwise zeros.
          - "current": use the current simulator joint positions.

    Notes:
        The action space bounds are generic and not derived from the robot's
        workspace. Environments/policies should ensure targets are reachable.
    """

    def __init__(
        self,
        *,
        entity,
        model,
        normalized: bool | None,
        ik_max_iters: int | None,
        ik_damping: float | None,
        ik_max_step: float | None,
        ik_init: str | None,
        clip: bool | None = None,
        **kw,
    ) -> None:
        """Initialize the IK pose controller.

        Args:
            entity: The simulation entity to control.
            model: The corresponding robot component model.
            normalized: Whether actions are in the normalized range [-1, 1].
            ik_max_iters: Maximum IK solver iterations (> 0).
            ik_damping: IK damping factor (>= 0).
            ik_max_step: Optional maximum solver step size (> 0).
            ik_init: IK seed strategy, either "home" or "current".
            clip: If True, clamp input position to [-1, 1] and angles to [-pi, pi]
                before solving.
            kw: Additional keyword arguments for the base controller.

        Raises:
            ValueError: If required parameters are missing or invalid.
        """
        super().__init__(entity=entity, model=model, **kw)

        if normalized is None:
            raise ValueError("ik_pose: 'normalized' is required.")
        if ik_max_iters is None or ik_damping is None or ik_init is None:
            raise ValueError(
                "ik_pose: 'ik_max_iters', 'ik_damping', and 'ik_init' are required.",
            )
        if not (isinstance(ik_max_iters, int) and ik_max_iters > 0):
            raise ValueError(
                f"ik_pose: ik_max_iters must be a positive int, got {ik_max_iters!r}.",
            )
        if not (
            isinstance(ik_damping, (int, float))
            and math.isfinite(ik_damping)
            and ik_damping >= 0.0
        ):
            raise ValueError(f"ik_pose: ik_damping must be >= 0, got {ik_damping!r}.")
        if ik_max_step is not None and not (
            isinstance(ik_max_step, (int, float))
            and math.isfinite(ik_max_step)
            and ik_max_step > 0.0
        ):
            raise ValueError(
                "ik_pose: ik_max_step must be a finite number > 0 (or None), "
                f"got {ik_max_step!r}.",
            )
        if ik_init not in {"home", "current"}:
            raise ValueError("ik_pose: ik_init must be 'home' or 'current'.")

        self.normalized = bool(normalized)
        self.ik_max_iters = int(ik_max_iters)
        self.ik_damping = float(ik_damping)
        self.ik_max_step = float(ik_max_step) if ik_max_step is not None else None
        self.ik_init = str(ik_init)
        self.clip = bool(clip) if clip is not None else False

        self._link = self._get_end_effector_link()

    def action_space(self) -> spaces.Box:
        """Return the controller's Gymnasium action space.

        Returns:
            A spaces.Box of shape (6,) matching [x, y, z, roll, pitch, yaw].

            - If normalized is True, bounds are always [-1, 1].
            - If normalized is False, translation bounds are [-1, 1] and rotation
              bounds are [-pi, pi].
        """
        if self.normalized:
            return spaces.Box(low=-1.0, high=1.0, shape=(6,), dtype=np.float32)
        low = np.array(
            [-1.0, -1.0, -1.0, -math.pi, -math.pi, -math.pi],
            dtype=np.float32,
        )
        high = -low
        return spaces.Box(low=low, high=high, dtype=np.float32)

    @torch.no_grad()
    def _apply_cmd(self, vec_2d: torch.Tensor) -> None:
        """Apply an absolute end-effector pose command.

        Args:
            vec_2d: Action tensor with shape (6,) or (n_envs, 6).
        """
        v = self._expect_2d(vec_2d, 6).contiguous()
        v = v.clamp(-1.0, 1.0) if (self.clip and self.normalized) else v
        pos = v[:, :3].contiguous()
        rpy = v[:, 3:].contiguous()

        if self.normalized:
            rpy = rpy * float(math.pi)
        elif self.clip:
            pos = pos.clamp(-1.0, 1.0)
            rpy = rpy.clamp(-math.pi, math.pi)

        quat = rpy_to_quat_wxyz_torch(rpy).contiguous()

        if self.ik_init == "home":
            if self.home_q is None or self.home_q.numel() != self.dof:
                iq = torch.zeros(self.dof, dtype=torch.float32, device=self.device)
            else:
                iq = self.home_q
        else:
            iq = self.entity.get_dofs_position().contiguous()

        ik_kw: dict[str, object] = {
            "max_solver_iters": self.ik_max_iters,
            "damping": self.ik_damping,
        }
        if self.ik_max_step is not None:
            ik_kw["max_step_size"] = self.ik_max_step
        q_target = self._ik(link=self._link, pos=pos, quat=quat, init_qpos=iq, **ik_kw)
        self._control_position(self._q_to_ctrl(q_target).contiguous())
