"""Operational Space Control (OSC) for relative end-effector poses.

This controller accepts a 6D delta pose command for the end effector and
converts it into joint position targets using inverse kinematics (IK).

The action is interpreted as:

[dx, dy, dz, droll, dpitch, dyaw]

where translation is in meters and rotation is in radians (roll/pitch/yaw).
"""

from __future__ import annotations

import math

import numpy as np
import torch
from gymnasium import spaces

from dexsuite.core.registry import register_controller
from dexsuite.utils.orientation_utils import (
    quat_mul_wxyz_torch,
    quat_normalize_torch,
    rpy_to_quat_wxyz_torch,
)

from .base_controller import Controller


@register_controller("osc_pose")
class OSCPoseController(Controller):
    """Relative OSC pose controller.

    This controller is a common default for interactive teleoperation and RL
    because it operates in task space while still producing joint targets.

    Action semantics:

    - The action is 6D: [dx, dy, dz, droll, dpitch, dyaw].
    - If normalized is True:
      - Values are expected in [-1, 1].
      - When clip is True they are clamped to [-1, 1].
      - Linear deltas are scaled by lin_scale (meters per unit action).
      - Angular deltas are scaled by ang_scale (radians per unit action).
    - If normalized is False:
      - Values are interpreted directly as deltas in meters/radians.
      - When clip is True deltas are clamped to [-lin_scale, lin_scale] and
        [-ang_scale, ang_scale].

    Implementation overview:

    1. Compute current end-effector pose via FK.
    2. Apply the delta translation and delta rotation.
    3. Solve IK for the resulting target pose.
    4. Send the IK solution as a joint position command.

    Requirements:
        The associated model must define end_link so FK/IK can target the
        correct end-effector link.
    """

    def __init__(
        self,
        *,
        entity,
        model,
        normalized: bool | None,
        clip: bool | None,
        lin_scale: float | None,
        ang_scale: float | None,
        **kw,
    ) -> None:
        """Initialize the relative OSC pose controller.

        Args:
            entity: The simulation entity to control.
            model: The corresponding robot component model.
            normalized: Whether actions are in the normalized range [-1, 1].
            clip: Whether to clip actions to the valid range.
            lin_scale: Scaling factor for linear delta actions.
            ang_scale: Scaling factor for angular delta actions.
            kw: Additional keyword arguments for the base controller.

        Raises:
            ValueError: If required parameters are missing or invalid.
        """
        super().__init__(entity=entity, model=model, **kw)

        if normalized is None or clip is None or lin_scale is None or ang_scale is None:
            raise ValueError(
                "osc_pose: 'normalized', 'clip', 'lin_scale', and 'ang_scale' are "
                "required.",
            )
        if not (
            isinstance(lin_scale, (int, float))
            and math.isfinite(lin_scale)
            and lin_scale > 0.0
        ):
            raise ValueError(f"osc_pose: lin_scale must be > 0, got {lin_scale!r}.")
        if not (
            isinstance(ang_scale, (int, float))
            and math.isfinite(ang_scale)
            and ang_scale > 0.0
        ):
            raise ValueError(f"osc_pose: ang_scale must be > 0, got {ang_scale!r}.")

        self.normalized = bool(normalized)
        self.clip = bool(clip)
        self.lin_scale = float(lin_scale)
        self.ang_scale = float(ang_scale)

        self._link = self._get_end_effector_link()
        self._link_idx = self._link.idx_local

    def action_space(self) -> spaces.Box:
        """Return the controller's Gymnasium action space.

        Returns:
            A spaces.Box of shape (6,).

            - If normalized is True, bounds are always [-1, 1].
            - If normalized is False, bounds are derived from lin_scale and
              ang_scale to reflect the intended clipping magnitudes.
        """
        if self.normalized:
            return spaces.Box(low=-1.0, high=1.0, shape=(6,), dtype=np.float32)
        low = np.concatenate(
            [
                np.full(3, -self.lin_scale, dtype=np.float32),
                np.full(3, -self.ang_scale, dtype=np.float32),
            ],
        )
        high = -low
        return spaces.Box(low=low, high=high, dtype=np.float32)

    @torch.no_grad()
    def _apply_cmd(self, vec_2d: torch.Tensor) -> None:
        """Apply a delta end-effector pose command.

        Args:
            vec_2d: Action tensor with shape (6,) or (n_envs, 6).
        """
        v = self._expect_2d(vec_2d, 6).contiguous()
        dp = v[:, :3].contiguous()
        dr = v[:, 3:].contiguous()

        if self.normalized:
            if self.clip:
                dp = dp.clamp(-1.0, 1.0)
                dr = dr.clamp(-1.0, 1.0)
            dp = dp * self.lin_scale
            dr = dr * self.ang_scale
        else:
            if self.clip:
                dp = dp.clamp(-self.lin_scale, self.lin_scale)
                dr = dr.clamp(-self.ang_scale, self.ang_scale)

        pos_cur, quat_cur = self._fk_pos_quat_2d(self._link_idx)

        pos_tgt = (pos_cur + dp).contiguous()

        qd = rpy_to_quat_wxyz_torch(dr).contiguous()
        quat_tgt = quat_mul_wxyz_torch(qd, quat_cur).contiguous()
        quat_tgt = quat_normalize_torch(quat_tgt).contiguous()

        q = self._ik(
            link=self._link,
            pos=pos_tgt,
            quat=quat_tgt,
            init_qpos=None,
        )
        self._control_position(self._q_to_ctrl(q).contiguous())
