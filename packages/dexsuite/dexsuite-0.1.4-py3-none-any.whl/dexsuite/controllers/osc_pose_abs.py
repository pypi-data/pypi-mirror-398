"""Operational Space Control (OSC) for absolute end-effector pose offsets.

This controller accepts a 6D offset from a captured reference pose (origin)
and converts it into joint position targets using inverse kinematics (IK).

The action is interpreted as:

[dx, dy, dz, droll, dpitch, dyaw]

where translation is in meters and rotation is in radians (roll/pitch/yaw).
"""

from __future__ import annotations

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


@register_controller("osc_pose_abs")
class OSCPoseAbsoluteController(Controller):
    """Absolute OSC pose controller (offset-from-origin).

    Unlike OSCPoseController, this controller does not apply deltas relative to
    the current end-effector pose. Instead, it captures an origin pose once and
    interprets actions as offsets from that origin.

    Action semantics:

    - The action is 6D: [dx, dy, dz, droll, dpitch, dyaw].
    - If normalized is True:
      - Values are expected in [-1, 1].
      - When clip is True they are clamped to [-1, 1].
      - Linear offsets are scaled per-axis by lin_range.
      - Angular offsets are scaled per-axis by ang_range.
    - If normalized is False:
      - Values are interpreted directly as offsets in meters/radians.
      - When clip is True offsets are clamped to [-lin_range, lin_range] and
        [-ang_range, ang_range].

    Origin capture:
        The origin pose is captured lazily on the first call to step (when the
        controller's internal _origin_pos and _origin_quat are uninitialized).
        It is not automatically re-captured on every environment reset.
    """

    def __init__(
        self,
        *,
        entity,
        model,
        normalized: bool | None,
        clip: bool | None,
        lin_range: tuple[float, float, float] | None,
        ang_range: tuple[float, float, float] | None,
        ik_max_iters: int = 100,
        ik_damping: float = 0.05,
        **kw,
    ) -> None:
        """Initialize the absolute OSC pose controller.

        Args:
            entity: The simulation entity to control.
            model: The corresponding robot component model.
            normalized: Whether actions are in the normalized range [-1, 1].
            clip: Whether to clip actions to the valid range.
            lin_range: Max linear delta [x, y, z] from origin.
            ang_range: Max angular delta [r, p, y] from origin.
            ik_max_iters: Maximum IK solver iterations.
            ik_damping: Damping factor for the IK solver.
            kw: Additional keyword arguments for the base controller.

        Raises:
            ValueError: If required parameters are missing or invalid.
        """
        super().__init__(entity=entity, model=model, **kw)
        if normalized is None or clip is None or lin_range is None or ang_range is None:
            raise ValueError(
                "osc_pose_abs: 'normalized', 'clip', 'lin_range', and 'ang_range' are "
                "required.",
            )
        if len(lin_range) != 3 or len(ang_range) != 3:
            raise ValueError(
                "osc_pose_abs: lin_range and ang_range must be length-3 sequences.",
            )
        if not all(np.isfinite(lin_range)) or not all(np.isfinite(ang_range)):
            raise ValueError("osc_pose_abs: ranges must be finite numbers.")
        if any(v <= 0.0 for v in lin_range) or any(v <= 0.0 for v in ang_range):
            raise ValueError("osc_pose_abs: range entries must be > 0.")

        if not (isinstance(ik_max_iters, int) and ik_max_iters > 0):
            raise ValueError(
                f"osc_pose_abs: ik_max_iters must be > 0 int; got {ik_max_iters!r}.",
            )
        if not (
            isinstance(ik_damping, (int, float))
            and np.isfinite(ik_damping)
            and ik_damping >= 0.0
        ):
            raise ValueError(
                f"osc_pose_abs: ik_damping must be >= 0, got {ik_damping!r}.",
            )

        self.normalized = bool(normalized)
        self.clip = bool(clip)
        self.lin_range = torch.tensor(
            lin_range,
            dtype=torch.float32,
            device=self.device,
        ).contiguous()
        self.ang_range = torch.tensor(
            ang_range,
            dtype=torch.float32,
            device=self.device,
        ).contiguous()
        self.ik_max_iters = int(ik_max_iters)
        self.ik_damping = float(ik_damping)

        self._link = self._get_end_effector_link()
        self._link_idx = self._link.idx_local

        self._origin_pos: torch.Tensor | None = None  # (N,3), contiguous
        self._origin_quat: torch.Tensor | None = None  # (N,4) wxyz, contiguous

    def action_space(self) -> spaces.Box:
        """Return the controller's Gymnasium action space.

        Returns:
            A spaces.Box of shape (6,).

            - If normalized is True, bounds are always [-1, 1].
            - If normalized is False, bounds are [-lin_range, lin_range] for
              translation and [-ang_range, ang_range] for rotation.
        """
        if self.normalized:
            return spaces.Box(low=-1.0, high=1.0, shape=(6,), dtype=np.float32)
        lin = self.lin_range.detach().cpu().numpy().astype(np.float32)
        ang = self.ang_range.detach().cpu().numpy().astype(np.float32)
        low = np.concatenate([-lin, -ang])
        high = -low
        return spaces.Box(low=low, high=high, dtype=np.float32)

    @torch.no_grad()
    def _apply_cmd(self, vec_2d: torch.Tensor) -> None:
        """Apply an offset-from-origin end-effector pose command.

        Args:
            vec_2d: Action tensor with shape (6,) or (n_envs, 6).
        """
        if self._origin_pos is None or self._origin_quat is None:
            self._origin_pos, self._origin_quat = self._fk_pos_quat_2d(self._link_idx)

        v = self._expect_2d(vec_2d, 6).contiguous()
        dp = v[:, :3].contiguous()
        dr = v[:, 3:].contiguous()

        # Scaling/clip at action level
        if self.normalized:
            if self.clip:
                dp = dp.clamp(-1.0, 1.0)
                dr = dr.clamp(-1.0, 1.0)
            dp = dp * self.lin_range
            dr = dr * self.ang_range
        else:
            if self.clip:
                dp = torch.min(torch.max(dp, -self.lin_range), self.lin_range)
                dr = torch.min(torch.max(dr, -self.ang_range), self.ang_range)

        pos_tgt = (self._origin_pos + dp).contiguous()

        # Delta RPY -> delta quaternion (wxyz), then compose with origin:
        # q_tgt = qd ⊗ q_origin
        qd = rpy_to_quat_wxyz_torch(dr).contiguous()
        quat_tgt = quat_mul_wxyz_torch(qd, self._origin_quat).contiguous()
        quat_tgt = quat_normalize_torch(quat_tgt).contiguous()

        iq = self.entity.get_dofs_position().contiguous()

        q = self._ik(
            link=self._link,
            pos=pos_tgt,
            quat=quat_tgt,
            init_qpos=iq,
            max_solver_iters=self.ik_max_iters,
            damping=self.ik_damping,
        )
        self._control_position(self._q_to_ctrl(q).contiguous())
