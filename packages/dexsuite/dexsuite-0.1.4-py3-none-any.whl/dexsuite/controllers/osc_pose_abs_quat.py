"""Operational Space Control (OSC) for absolute pose offsets (quaternion).

This controller is the quaternion variant of osc_pose_abs. It accepts a
translation offset and a delta quaternion relative to a captured origin pose
and converts them into joint position targets using inverse kinematics (IK).

The action is interpreted as:

[dx, dy, dz, dq_w, dq_x, dq_y, dq_z]

where translation is in meters and the quaternion uses wxyz ordering.
"""

from __future__ import annotations

import numpy as np
import torch
from gymnasium import spaces

from dexsuite.core.registry import register_controller
from dexsuite.utils.orientation_utils import (
    quat_mul_wxyz_torch,
    quat_normalize_torch,
)

from .base_controller import Controller


@register_controller("osc_pose_abs_quat")
class OSCPoseAbsoluteQuatController(Controller):
    """Absolute OSC pose controller (offset-from-origin, quaternion rotation).

    This controller captures an origin end-effector pose once and interprets
    actions as offsets from that origin. Orientation offsets are provided as a
    quaternion delta, which is normalized at runtime.

    Action semantics:

    - The action is 7D: [dx, dy, dz, dq_w, dq_x, dq_y, dq_z] (wxyz).
    - If normalized is True:
      - Values are expected in [-1, 1].
      - When clip is True translation and quaternion components are clamped to
        [-1, 1].
      - Translation is scaled per-axis by lin_range.
      - The quaternion is normalized to unit length (always).
    - If normalized is False:
      - Translation is interpreted directly in meters. When clip is True it is
        clamped to [-lin_range, lin_range].
      - Quaternion components are still clamped to [-1, 1] when clip is True
        and always renormalized.

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
        # kept for config compatibility; not used in quaternion mode
        ang_range: tuple[float, float, float] | None = None,
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
            ang_range: Deprecated (ignored). Kept for configuration compatibility.
            ik_max_iters: Maximum IK solver iterations.
            ik_damping: Damping factor for the IK solver.
            kw: Additional keyword arguments for the base controller.

        Raises:
            ValueError: If required parameters are missing or invalid.
        """
        super().__init__(entity=entity, model=model, **kw)
        # ang_range is intentionally ignored for quaternion-mode, but kept in the
        # signature so configs can reuse osc_pose_abs fields without breaking.
        if ang_range is not None:
            pass
        if normalized is None or clip is None or lin_range is None:
            raise ValueError(
                "osc_pose_abs_quat: 'normalized', 'clip', and 'lin_range' are "
                "required.",
            )
        if (
            len(lin_range) != 3
            or not all(np.isfinite(lin_range))
            or any(v <= 0.0 for v in lin_range)
        ):
            raise ValueError(
                "osc_pose_abs_quat: lin_range must be finite, length-3, and > 0.",
            )

        if not (isinstance(ik_max_iters, int) and ik_max_iters > 0):
            raise ValueError(
                "osc_pose_abs_quat: ik_max_iters must be > 0 int; "
                f"got {ik_max_iters!r}.",
            )
        if not (
            isinstance(ik_damping, (int, float))
            and np.isfinite(ik_damping)
            and ik_damping >= 0.0
        ):
            raise ValueError(
                f"osc_pose_abs_quat: ik_damping must be >= 0, got {ik_damping!r}.",
            )

        self.normalized = bool(normalized)
        self.clip = bool(clip)
        self.lin_range = torch.tensor(
            lin_range,
            dtype=torch.float32,
            device=self.device,
        ).contiguous()
        self.ik_max_iters = int(ik_max_iters)
        self.ik_damping = float(ik_damping)

        self._link = self._get_end_effector_link()
        self._link_idx = self._link.idx_local
        self._origin_pos: torch.Tensor | None = None  # (N,3)
        self._origin_quat: torch.Tensor | None = None  # (N,4) wxyz

    def action_space(self) -> spaces.Box:
        """Return the controller's Gymnasium action space.

        Returns:
            A spaces.Box of shape (7,) matching [dx, dy, dz, dq_w, dq_x, dq_y, dq_z].

            - If normalized is True, bounds are always [-1, 1].
            - If normalized is False, translation bounds are derived from
              lin_range and quaternion components are bounded by [-1, 1].
        """
        if self.normalized:
            # Controller will renormalize the quaternion; Box just bounds inputs.
            return spaces.Box(low=-1.0, high=1.0, shape=(7,), dtype=np.float32)
        lin = self.lin_range.detach().cpu().numpy().astype(np.float32)
        # Note: quaternion is 4D (wxyz). The action space bounds components to
        # [-1, 1] and the controller normalizes at runtime.
        quat_bounds = np.ones(4, dtype=np.float32)
        low = np.concatenate([-lin, -quat_bounds])  # -> shape (7,)
        high = -low
        return spaces.Box(low=low, high=high, dtype=np.float32)

    @torch.no_grad()
    def _apply_cmd(self, vec_2d: torch.Tensor) -> None:
        """Apply an offset-from-origin end-effector pose command.

        Args:
            vec_2d: Action tensor with shape (7,) or (n_envs, 7).
        """
        if self._origin_pos is None or self._origin_quat is None:
            self._origin_pos, self._origin_quat = self._fk_pos_quat_2d(self._link_idx)
        v = self._expect_2d(vec_2d, 7).contiguous()
        dp = v[:, :3].contiguous()
        dq = v[:, 3:7].contiguous()  # wxyz
        # Scaling/clip at action level
        if self.normalized:
            if self.clip:
                dp = dp.clamp(-1.0, 1.0)
                dq = dq.clamp(-1.0, 1.0)
            dp = dp * self.lin_range
        else:
            if self.clip:
                dp = torch.min(torch.max(dp, -self.lin_range), self.lin_range)
                dq = dq.clamp(-1.0, 1.0)
        # Normalize quaternion inputs to unit
        dq = quat_normalize_torch(dq)
        pos_tgt = (self._origin_pos + dp).contiguous()
        # Compose delta with origin orientation: q_tgt = dq ⊗ q_origin
        quat_tgt = quat_mul_wxyz_torch(dq, self._origin_quat)
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
