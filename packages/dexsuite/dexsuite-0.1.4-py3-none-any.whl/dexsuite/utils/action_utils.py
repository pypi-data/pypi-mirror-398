"""Utilities for defining, validating, and dispatching multi-component actions.

This module provides structures for managing compound action spaces, such as
those combining multiple robot arms and grippers, by logically partitioning a
single flat action vector into segments for individual controllers.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

import numpy as np
import torch
from gymnasium import spaces


@dataclass(frozen=True)
class ActionSegment:
    """Defines a single contiguous section within a flat action vector."""

    start: int
    stop: int
    ctrl: Any  # Any controller with .action_space() and .step()
    name: tuple[str, ...]  # Stable hierarchical name, e.g. ("left", "manipulator")

    def width(self) -> int:
        """Returns the dimensionality of this action segment.

        Returns:
            int: The number of dimensions covered by the segment.
        """
        return int(self.stop - self.start)


@dataclass
class ActionLayout:
    """Manages the overall structure of a flat, composite action vector.

    This class provides tools to validate the contiguity of action segments,
    generate the unified Gymnasium action space, and slice incoming action
    tensors for dispatching to individual controllers.
    """

    segments: tuple[ActionSegment, ...]
    total_dim: int

    def __post_init__(self) -> None:
        """Performs validation checks and pre-calculates flat keys."""
        self._validate_contiguity()
        self._validate_dims()
        self._flat_keys = tuple(".".join(seg.name) for seg in self.segments)

    def as_box(self) -> spaces.Box:
        """Generate a unified Gymnasium Box for the full action layout.

        Returns:
            spaces.Box: Concatenated action space with shape (total_dim,).

        Raises:
            TypeError: If any segment controller does not return spaces.Box.
        """
        lows: list[np.ndarray] = []
        highs: list[np.ndarray] = []
        for seg in self.segments:
            sp = seg.ctrl.action_space()
            if not isinstance(sp, spaces.Box):
                raise TypeError(
                    f"Controller {type(seg.ctrl).__name__} must return spaces.Box",
                )
            # Ensure the low/high vectors are flat
            low = np.asarray(sp.low, dtype=np.float32).reshape(-1)
            high = np.asarray(sp.high, dtype=np.float32).reshape(-1)
            lows.append(low)
            highs.append(high)
        low_cat = np.concatenate(lows, axis=0)
        high_cat = np.concatenate(highs, axis=0)

        return spaces.Box(
            low=low_cat,
            high=high_cat,
            shape=(self.total_dim,),
            dtype=np.float32,
        )

    def flat_keys(self) -> tuple[str, ...]:
        """Returns the unique, flat hierarchical name for each action segment.

        For a bimanual setup, keys look like:
        ("left.manipulator", "left.gripper", ...).

        Returns:
            tuple[str, ...]: The unique keys for each segment.
        """
        return self._flat_keys

    def views(self, action_2d: torch.Tensor) -> Iterable[torch.Tensor]:
        """Yield per-segment views into a flat action tensor.

        The returned tensors are views (zero-copy) into the last dimension of
        the input.

        Args:
            action_2d: Flat action tensor with shape (D,) for a single environment or
                (N, D) for batched environments, where D is total_dim.

        Yields:
            torch.Tensor: A view into the action tensor corresponding to a segment.

        Raises:
            ValueError: If the action tensor is not 1D or 2D.
        """
        # Accept (D,) or (N, D); we only slice the last dimension.
        if action_2d.ndim == 1:
            for seg in self.segments:
                yield action_2d[seg.start : seg.stop]
        elif action_2d.ndim == 2:
            for seg in self.segments:
                yield action_2d[:, seg.start : seg.stop]
        else:
            raise ValueError(f"Action must be 1D or 2D; got {action_2d.ndim}D")

    # --------- internal checks ----------
    def _validate_contiguity(self) -> None:
        """Checks that all action segments are sequential and completely fill the total dimension.

        Raises:
            ValueError: If segments are non-contiguous, invalid, or don't match total_dim.
        """
        cur = 0
        for seg in self.segments:
            if seg.start != cur:
                raise ValueError(
                    f"Non-contiguous layout: expected start {cur}, got {seg.start}",
                )
            if seg.stop <= seg.start:
                raise ValueError(
                    f"Empty/invalid segment {seg.name}: [{seg.start},{seg.stop})",
                )
            cur = seg.stop
        if cur != self.total_dim:
            raise ValueError(f"Layout covers 0..{cur}, but total_dim={self.total_dim}")

    def _validate_dims(self) -> None:
        """Checks that the segment width matches the controller's action space dimension.

        Raises:
            ValueError: If a segment's declared width does not match the controller's required dimension.
        """
        for seg in self.segments:
            sp = seg.ctrl.action_space()
            need = seg.width()
            got = int(np.prod(sp.shape))
            if need != got:
                raise ValueError(
                    f"Segment {seg.name}: width {need} != controller action dim {got}",
                )


# -----------------------------
# Builders
# -----------------------------
def _dims(ctrl: Any) -> int:
    """Helper to get the flattened dimension of a controller's action space."""
    sp = ctrl.action_space()
    return int(np.prod(sp.shape))


def build_single_layout(*, arm_ctrl: Any, grip_ctrl: Any | None) -> ActionLayout:
    """Construct an ActionLayout for a single arm and optional gripper.

    The segment order is: arm, then gripper (if present).

    Args:
        arm_ctrl: Controller for the manipulator arm.
        grip_ctrl: Controller for the gripper, or None.

    Returns:
        ActionLayout: The constructed layout object.
    """
    segs: list[ActionSegment] = []
    cur = 0

    w = _dims(arm_ctrl)
    segs.append(
        ActionSegment(start=cur, stop=cur + w, ctrl=arm_ctrl, name=("manipulator",)),
    )
    cur += w

    if grip_ctrl is not None:
        w = _dims(grip_ctrl)
        segs.append(
            ActionSegment(start=cur, stop=cur + w, ctrl=grip_ctrl, name=("gripper",)),
        )
        cur += w

    return ActionLayout(segments=tuple(segs), total_dim=cur)


def build_bimanual_layout(
    *,
    left_arm: Any,
    left_grip: Any | None,
    right_arm: Any,
    right_grip: Any | None,
) -> ActionLayout:
    """Construct an ActionLayout for a bimanual setup.

    The segment order is: left arm, left gripper, right arm, then right gripper.

    Args:
        left_arm: Controller for the left manipulator arm.
        left_grip: Controller for the left gripper, or None.
        right_arm: Controller for the right manipulator arm.
        right_grip: Controller for the right gripper, or None.

    Returns:
        ActionLayout: The constructed layout object.
    """
    segs: list[ActionSegment] = []
    cur = 0

    # LEFT ARM
    wl = _dims(left_arm)
    segs.append(
        ActionSegment(
            start=cur,
            stop=cur + wl,
            ctrl=left_arm,
            name=("left", "manipulator"),
        ),
    )
    cur += wl

    # LEFT GRIPPER
    if left_grip is not None:
        wlg = _dims(left_grip)
        segs.append(
            ActionSegment(
                start=cur,
                stop=cur + wlg,
                ctrl=left_grip,
                name=("left", "gripper"),
            ),
        )
        cur += wlg

    # RIGHT ARM
    wr = _dims(right_arm)
    segs.append(
        ActionSegment(
            start=cur,
            stop=cur + wr,
            ctrl=right_arm,
            name=("right", "manipulator"),
        ),
    )
    cur += wr

    # RIGHT GRIPPER
    if right_grip is not None:
        wrg = _dims(right_grip)
        segs.append(
            ActionSegment(
                start=cur,
                stop=cur + wrg,
                ctrl=right_grip,
                name=("right", "gripper"),
            ),
        )
        cur += wrg

    return ActionLayout(segments=tuple(segs), total_dim=cur)


# -----------------------------
# Dispatcher (zero-logic forward)
# -----------------------------
@torch.no_grad()
def dispatch(layout: ActionLayout, action: torch.Tensor) -> None:
    """Dispatches action slices to their respective controller step methods.

    This is a strict, zero-copy dispatch. It slices the input action along its
    last dimension and forwards each view to the owning controller's step method.

    Args:
        layout: ActionLayout defining how the action vector is partitioned.
        action: Flat action tensor with shape (D,) for a single environment or
            (N, D) for batched environments, where D is layout.total_dim.
    """
    offs = 0
    for seg in layout.segments:
        # action[..., offs : seg.stop] is the fastest way to slice the last dim
        view = action[..., offs : seg.stop]  # offs is always equal to seg.start
        seg.ctrl.step(view)
        offs = seg.stop
