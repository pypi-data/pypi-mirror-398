"""Position and orientation randomizers (torch-native, batched).

This module provides torch-based samplers for positions and simple
orientations, designed for fast task resets.

Batch semantics:
- If get_n_envs() == 1 and env_idx is None, functions return 1D tensors such as
  (3,) for positions.
- Otherwise, functions return batched tensors with shape (B, 3), where B is
  len(env_idx) (if provided) or get_n_envs().

Sampling always happens on the active torch device returned by get_device().
Determinism is controlled by the global torch RNG and seed.

Examples:
    >>> box = AABB.from_lists([0.1, -0.4, -0.1], [0.65, 0.4, 0.4])
    >>> pos = sample_in_aabb_uniform(box, env_idx=None, margin=0.0)
    >>> pos2 = sample_in_aabb_center_xy_band(box, band_xy=0.10, mode="circle")
    >>> pos3 = sample_around_point_xy([0.40, 0.0], band_xy=(0.08, 0.05), z=0.20)
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Union

import numpy as np  # only for Gymnasium spaces metadata
import torch
from gymnasium import spaces

from dexsuite.utils.aabb import AABB
from dexsuite.utils.globals import get_device, get_n_envs

# Orientation (kept here for future composable pose samplers)
from dexsuite.utils.orientation_utils import (
    quat_mul_wxyz_torch,
    rpy_to_quat_wxyz_torch,
    yaw_quat_wxyz_torch,
)

TensorLike = Union[Sequence[float], torch.Tensor]


# --------------------------------------------------------------------- #
# Internal helpers
# --------------------------------------------------------------------- #


def _resolve_B_and_1d(
    env_idx: Sequence[int] | torch.Tensor | None,
) -> tuple[int, bool]:
    """Infer batch size and whether to return a 1D vector.

    Rules:
        - If env_idx is provided, B = len(env_idx) and return_1d is False.
        - Otherwise, B = get_n_envs() and return_1d is True when B == 1.

    Args:
        env_idx: Optional sequence/tensor of indices being reset.

    Returns:
        Tuple[int, bool]: (B, return_1d).
    """
    if env_idx is not None:
        if isinstance(env_idx, torch.Tensor):
            B = int(env_idx.numel())
        else:
            try:
                B = len(env_idx)
            except Exception:
                B = 1
        return B, False
    B = int(get_n_envs())
    return B, (B == 1)


def _maybe_1d(x: torch.Tensor, return_1d: bool) -> torch.Tensor:
    """Return (3,) if return_1d and x is (1, 3); otherwise return x unchanged."""
    if return_1d and x.ndim == 2 and x.shape[0] == 1:
        return x.squeeze(0)
    return x


def _as_tensor3(x: TensorLike, device: torch.device) -> torch.Tensor:
    """Convert input to a (3,) float32 tensor on device."""
    t = torch.as_tensor(x, dtype=torch.float32, device=device)
    if t.numel() != 3:
        raise ValueError(f"Expected 3 numbers for a point, got shape {tuple(t.shape)}")
    return t.reshape(3)


def _parse_band(band: float | Sequence[float]) -> tuple[float, float]:
    """Normalize band argument to (bx, by)."""
    if isinstance(band, (int, float)):
        return float(band), float(band)
    bx, by, *_ = list(band) + [band[-1]] * (2 - len(band))
    return float(bx), float(by)


# --------------------------------------------------------------------- #
# Position randomizers (plane and box)
# --------------------------------------------------------------------- #


class TwoDPosRandomizer:
    """Uniform (x, y) sampler with optional bands around a center.

    This sampler produces planar positions and attaches a fixed z coordinate.

    Args:
        x_range: Inclusive (x_low, x_high) in meters for box-mode sampling.
        y_range: Inclusive (y_low, y_high) in meters for box-mode sampling.
        z: Fixed z height in meters if not overridden at call time.

    Example:
        >>> r2d = TwoDPosRandomizer((0.1, 0.65), (-0.4, 0.4), z=0.2)
        >>> r2d.sample(env_idx=None).shape     # if get_n_envs()==1
        torch.Size([3])
        >>> r2d.sample(env_idx=[0,1,2]).shape  # subset of a vectorized scene
        torch.Size([3, 3])
    """

    def __init__(
        self,
        x_range: tuple[float, float],
        y_range: tuple[float, float],
        *,
        z: float = 0.0,
    ) -> None:
        self._x_lo, self._x_hi = map(float, x_range)
        self._y_lo, self._y_hi = map(float, y_range)
        self._z = float(z)
        self._device = get_device()

    def sample(
        self,
        *,
        env_idx: Sequence[int] | torch.Tensor | None = None,
        around_xy: TensorLike | None = None,
        band_xy: float | Sequence[float] | None = None,
        mode: str = "square",
        clamp_to: AABB | None = None,
        z: float | None = None,
    ) -> torch.Tensor:
        """Sample positions on the plane.

        If around_xy and band_xy are provided, sample inside the band around
        the center. Otherwise sample uniformly inside the configured x/y ranges.

        Args:
            env_idx: Optional subset of env indices; controls batch size and 1D/2D return.
            around_xy: Optional (2,) center [x, y] to sample offsets around.
            band_xy: Half-width(s) in meters; scalar or (bx, by).
            mode: "square" or "circle" (area-uniform disk/ellipse when "circle").
            clamp_to: Optional AABB to clamp outputs into.
            z: Optional z override (meters).

        Returns:
            torch.Tensor: (3,) if single-env/no subset; otherwise (B, 3).
        """
        B, return_1d = _resolve_B_and_1d(env_idx)
        dev = self._device
        z_val = float(self._z if z is None else z)

        if around_xy is not None and band_xy is not None:
            cx, cy, _ = _as_tensor3([*around_xy, 0.0], dev)
            bx, by = _parse_band(band_xy)

            if mode == "square":
                offs = (torch.rand(B, 2, device=dev) * 2.0 - 1.0) * torch.tensor(
                    [bx, by],
                    device=dev,
                )
                xy = torch.stack([cx, cy]).unsqueeze(0) + offs
            elif mode == "circle":
                theta = 2 * torch.pi * torch.rand(B, device=dev)
                r = torch.rand(B, device=dev).sqrt()  # area-uniform
                rx = bx * r
                xy = torch.stack(
                    [
                        cx + rx * torch.cos(theta),
                        cy + (by / max(bx, 1e-8)) * rx * torch.sin(theta),
                    ],
                    dim=1,
                )
            else:
                raise ValueError("mode must be 'square' or 'circle'")
        else:
            x = self._x_lo + torch.rand(B, device=dev) * (self._x_hi - self._x_lo)
            y = self._y_lo + torch.rand(B, device=dev) * (self._y_hi - self._y_lo)
            xy = torch.stack([x, y], dim=1)

        pos = torch.cat([xy, torch.full((B, 1), z_val, device=dev)], dim=1)
        if clamp_to is not None:
            pos = clamp_to.clamp(pos)
        return _maybe_1d(pos, return_1d)

    __call__ = sample


class ThreeDPosRandomizer:
    """Uniform (x, y, z) sampler in a rectangular box.

    Args:
        x_range: Inclusive (x_low, x_high) in meters.
        y_range: Inclusive (y_low, y_high) in meters.
        z_range: Inclusive (z_low, z_high) in meters.

    Example:
        >>> r3d = ThreeDPosRandomizer(x_range=(0.1, 0.65), y_range=(-0.4, 0.4), z_range=(0.0, 0.4))
        >>> r3d.sample(env_idx=None).shape      # if get_n_envs()==1
        torch.Size([3])
        >>> r3d.sample(env_idx=[2, 4, 7]).shape # subset of a vectorized scene
        torch.Size([3, 3])
    """

    def __init__(
        self,
        *,
        x_range: tuple[float, float],
        y_range: tuple[float, float],
        z_range: tuple[float, float],
    ):
        self._x_lo, self._x_hi = map(float, x_range)
        self._y_lo, self._y_hi = map(float, y_range)
        self._z_lo, self._z_hi = map(float, z_range)
        self._device = get_device()

    def sample(
        self,
        *,
        env_idx: Sequence[int] | torch.Tensor | None = None,
        freeze_axes: Sequence[str] | None = None,
        freeze_values: TensorLike | None = None,
    ) -> torch.Tensor:
        """Uniform sample inside the configured ranges.

        Args:
            env_idx: Optional subset of env indices; controls batch size and 1D/2D return.
            freeze_axes: Optional iterable of axes to hold constant, e.g., ("z",).
            freeze_values: (3,) values used when freezing axes; defaults to zeros.

        Returns:
            torch.Tensor: (3,) if single-env/no subset; otherwise (B, 3).
        """
        B, return_1d = _resolve_B_and_1d(env_idx)
        dev = self._device
        x = self._x_lo + torch.rand(B, device=dev) * (self._x_hi - self._x_lo)
        y = self._y_lo + torch.rand(B, device=dev) * (self._y_hi - self._y_lo)
        z = self._z_lo + torch.rand(B, device=dev) * (self._z_hi - self._z_lo)
        pos = torch.stack([x, y, z], dim=1)

        if freeze_axes:
            axes = {"x": 0, "y": 1, "z": 2}
            fv = _as_tensor3(
                freeze_values if freeze_values is not None else [0, 0, 0],
                dev,
            )
            for a in freeze_axes:
                pos[:, axes[a]] = fv[axes[a]]

        return _maybe_1d(pos, return_1d)

    __call__ = sample


# --------------------------------------------------------------------- #
# Rotation sampler (yaw delta)
# --------------------------------------------------------------------- #


class YawRandomizer:
    """Uniform sampler for yaw deltas using torch RNG (device-aware)."""

    def __init__(self, yaw_range: tuple[float, float] = (-torch.pi, torch.pi)) -> None:
        self._yaw_lo, self._yaw_hi = yaw_range
        self._device = get_device()
        self._yaw_width = self._yaw_hi - self._yaw_lo

    def sample_yaw(
        self,
        *,
        env_idx: Sequence[int] | torch.Tensor | None = None,
    ) -> torch.Tensor:
        """Sample yaw angle(s) uniformly in yaw_range.

        Returns:
            torch.Tensor: Scalar if get_n_envs() == 1 and env_idx is None;
            otherwise a (B,) tensor.
        """
        B, return_1d = _resolve_B_and_1d(env_idx)
        y = self._yaw_lo + torch.rand(B, device=self._device) * self._yaw_width
        return y.squeeze(0) if return_1d else y

    def __call__(self) -> torch.Tensor:
        y = self.sample_yaw()
        z = torch.zeros((), dtype=torch.float32, device=self._device)
        return torch.stack([z, z, y], dim=-1)  # (3,)

    def delta_quat(
        self,
        yaw: float | torch.Tensor | None = None,
        *,
        env_idx: Sequence[int] | torch.Tensor | None = None,
    ) -> torch.Tensor:
        """Return a pure-yaw quaternion delta in WXYZ convention.

        Shape rules match other randomizers:
            - single env + no env_idx -> (4,)
            - otherwise               -> (B, 4)
        """
        B, return_1d = _resolve_B_and_1d(env_idx)
        if yaw is None:
            yaw_t = self.sample_yaw(env_idx=env_idx)
        else:
            yaw_t = torch.as_tensor(yaw, dtype=torch.float32, device=self._device)
            if yaw_t.ndim == 0:
                yaw_t = yaw_t.expand(B)
            else:
                yaw_t = yaw_t.reshape(-1)
                if yaw_t.numel() == 1 and B > 1:
                    yaw_t = yaw_t.expand(B)
                elif yaw_t.numel() != B:
                    raise ValueError(
                        f"yaw must have {B} elements for env_idx batch, got {yaw_t.numel()}",
                    )

        dq = yaw_quat_wxyz_torch(yaw_t.reshape(-1))
        return dq.squeeze(0) if return_1d else dq

    def quat(
        self,
        *,
        base_euler: TensorLike | None = None,
        base_quat: TensorLike | None = None,
        yaw: float | torch.Tensor | None = None,
        frame: str = "world",
        env_idx: Sequence[int] | torch.Tensor | None = None,
    ) -> torch.Tensor:
        """Apply a random (or provided) yaw on top of an optional base rotation.

        Args:
            base_euler: Optional base roll/pitch/yaw (radians), shape (3,) or (B,3).
            base_quat: Optional base quaternion in WXYZ, shape (4,) or (B,4).
            yaw: Optional yaw override (radians), scalar or (B,).
            frame: "world" (post-multiply) or "local" (pre-multiply).
            env_idx: Optional subset of env indices; controls batch size and 1D/2D return.

        Returns:
            torch.Tensor: (4,) if single-env/no subset; otherwise (B, 4).
        """
        if (base_euler is not None) and (base_quat is not None):
            raise ValueError("Provide at most one of base_euler or base_quat.")

        B, return_1d = _resolve_B_and_1d(env_idx)

        if base_euler is None and base_quat is None:
            base_quat_t = torch.tensor(
                [1.0, 0.0, 0.0, 0.0],
                dtype=torch.float32,
                device=self._device,
            )
        elif base_euler is not None:
            e = torch.as_tensor(
                list(base_euler),
                dtype=torch.float32,
                device=self._device,
            )
            base_quat_t = rpy_to_quat_wxyz_torch(e)
        else:
            base_quat_t = torch.as_tensor(
                list(base_quat),
                dtype=torch.float32,
                device=self._device,
            )

        # Ensure shapes are (B,4) for consistent broadcasting and return semantics.
        base_quat_t = base_quat_t.to(dtype=torch.float32, device=self._device)
        if base_quat_t.ndim == 1:
            base_quat_t = base_quat_t.unsqueeze(0).expand(B, 4)
        elif base_quat_t.ndim == 2:
            if base_quat_t.shape[0] == 1 and B > 1:
                base_quat_t = base_quat_t.expand(B, 4)
            elif base_quat_t.shape[0] != B:
                raise ValueError(
                    f"base quaternion batch mismatch: expected {B} rows, got {base_quat_t.shape[0]}",
                )
        else:
            raise ValueError(
                f"base quaternion must have shape (4,) or (B,4), got {tuple(base_quat_t.shape)}",
            )

        dq = self.delta_quat(yaw, env_idx=env_idx).reshape(B, 4)
        frame = frame.lower()
        if frame == "world":
            out = quat_mul_wxyz_torch(base_quat_t, dq)
        elif frame == "local":
            out = quat_mul_wxyz_torch(dq, base_quat_t)
        else:
            raise ValueError("frame must be 'world' or 'local'.")

        return out.squeeze(0) if return_1d else out


# --------------------------------------------------------------------- #
# AABB-based samplers (now delegating to pose randomizers)
# --------------------------------------------------------------------- #


def sample_in_aabb_uniform(
    box: AABB,
    *,
    env_idx: Sequence[int] | torch.Tensor | None = None,
    margin: float | Sequence[float] = 0.0,
) -> torch.Tensor:
    """Sample uniformly inside an AABB (delegates to ThreeDPosRandomizer).

    This is the recommended API for task resets in Dexsuite.

    Args:
        box: AABB defining the sampling region (world frame).
        env_idx: Optional subset of env indices to sample for. If provided,
            the function returns a (B, 3) tensor even when B == 1.
        margin: Scalar or (mx, my, mz) shrink applied to both sides of the box
            before sampling. Positive margin shrinks; negative expands.

    Returns:
        torch.Tensor: (3,) if single-env/no subset; otherwise (B, 3).

    Example:
        >>> box = AABB.from_lists([0.1,-0.4,-0.1], [0.65,0.4,0.4])
        >>> p = sample_in_aabb_uniform(box, env_idx=None)           # (3,) if n_envs==1
        >>> P = sample_in_aabb_uniform(box, env_idx=[0,1,7,9])      # (4,3)
    """
    dev = box.device
    if isinstance(margin, (int, float)):
        m = torch.tensor([margin, margin, margin], dtype=torch.float32, device=dev)
    else:
        m = torch.as_tensor(margin, dtype=torch.float32, device=dev).reshape(3)

    lo = (box.min + m).to(dev)
    hi = (box.max - m).to(dev)
    lo, hi = torch.minimum(lo, hi), torch.maximum(lo, hi)

    r3d = ThreeDPosRandomizer(
        x_range=(float(lo[0]), float(hi[0])),
        y_range=(float(lo[1]), float(hi[1])),
        z_range=(float(lo[2]), float(hi[2])),
    )
    return r3d.sample(env_idx=env_idx)


def sample_in_aabb_center(
    box: AABB,
    *,
    env_idx: Sequence[int] | torch.Tensor | None = None,
) -> torch.Tensor:
    """Return the center point(s) of an AABB.

    Args:
        box: AABB defining the region.
        env_idx: Optional subset of env indices to produce (B, 3) output.

    Returns:
        torch.Tensor: (3,) if single-env/no subset; otherwise (B, 3).
    """
    B, return_1d = _resolve_B_and_1d(env_idx)
    c = box.center().reshape(1, 3).expand(B, 3)
    return _maybe_1d(c, return_1d)


def sample_in_aabb_center_xyz_band(
    box: AABB,
    *,
    band_xyz: float | Sequence[float] = 0.0,
    mode: str = "box",  # "box" (cuboid) or "ellipsoid" (uniform volume)
    range_x: tuple[float, float] | None = None,
    range_y: tuple[float, float] | None = None,
    range_z: tuple[float, float] | None = None,
    env_idx: Sequence[int] | torch.Tensor | None = None,
    margin: float | Sequence[float] = 0.0,
    clamp: bool = True,
) -> torch.Tensor:
    """Sample around an AABB center in XYZ, with optional per-axis ranges.

    Sampling can be specified in two ways:

    1. Bands around the center (default):
       - band_xyz provides scalar or (bx, by, bz) half-widths in meters.
       - mode="box" samples uniformly in a center-aligned cuboid.
       - mode="ellipsoid" samples uniformly by volume in a center-aligned ellipsoid.
       - Bands are limited by the AABB half-extents (after applying margin).

    2. Explicit per-axis ranges:
       - range_x, range_y, range_z are absolute world-coordinate ranges.
       - Each provided axis is sampled uniformly from the intersection between the
         given range and the margin-adjusted AABB.
       - Any axis with an explicit range uses that range instead of band_xyz and mode.

    Batch semantics:
    - If get_n_envs() == 1 and env_idx is None, returns a tensor with shape (3,).
    - Otherwise returns a tensor with shape (B, 3), where B is len(env_idx) or n_envs.

    Args:
        box: AABB defining the region (world frame).
        band_xyz: Scalar or (bx, by, bz) half-widths in meters around the AABB center.
        mode: "box" (cuboid) or "ellipsoid" (uniform volume). Ignored on axes with
            explicit ranges.
        range_x: Optional (low, high) world range for the x-axis.
        range_y: Optional (low, high) world range for the y-axis.
        range_z: Optional (low, high) world range for the z-axis.
        env_idx: Optional subset of environment indices; controls batch size and
            1D or 2D return shape.
        margin: Scalar or (mx, my, mz) shrink applied to the AABB before sampling.
        clamp: If True, clamp final samples back into the margin-adjusted AABB.

    Returns:
        torch.Tensor: Sampled position(s) with shape (3,) or (B, 3).
    """
    dev = box.device
    B, return_1d = _resolve_B_and_1d(env_idx)

    # --- margin shrink ---
    if isinstance(margin, (int, float)):
        m = torch.tensor([margin, margin, margin], dtype=torch.float32, device=dev)
    else:
        m = torch.as_tensor(margin, dtype=torch.float32, device=dev).reshape(3)

    lo = box.min + m
    hi = box.max - m
    # guard order
    lo = torch.minimum(lo, hi)
    hi = torch.maximum(lo, hi)
    cen = 0.5 * (lo + hi)

    # --- small local helper for band parsing ---
    def _parse_band3(b: float | Sequence[float]) -> tuple[float, float, float]:
        if isinstance(b, (int, float)):
            f = float(b)
            return f, f, f
        vals = list(b)
        if len(vals) == 1:
            f = float(vals[0])
            return f, f, f
        if len(vals) == 2:
            bx, by = float(vals[0]), float(vals[1])
            return bx, by, max(bx, by)
        return float(vals[0]), float(vals[1]), float(vals[2])

    # --- explicit per-axis ranges (axis-wise box sampling) ---
    use_range = [range_x is not None, range_y is not None, range_z is not None]
    rngs = [range_x, range_y, range_z]

    final_lo = lo.clone()
    final_hi = hi.clone()

    if any(use_range):
        # set explicit ranges with intersection; fill others from bands
        bx, by, bz = _parse_band3(band_xyz)
        half_ext = torch.minimum(cen - lo, hi - cen)  # (3,)
        radii = torch.minimum(
            torch.tensor([bx, by, bz], device=dev),
            half_ext,
        ).clamp_min(0.0)

        for i, has_r in enumerate(use_range):
            if has_r:
                r_lo, r_hi = float(rngs[i][0]), float(rngs[i][1])
                a_lo = max(r_lo, float(lo[i]))
                a_hi = min(r_hi, float(hi[i]))
                if a_lo > a_hi:
                    # collapse to center if invalid
                    a_lo = a_hi = float(cen[i])
                final_lo[i] = a_lo
                final_hi[i] = a_hi
            else:
                final_lo[i] = float(cen[i] - radii[i])
                final_hi[i] = float(cen[i] + radii[i])

        u = torch.rand(B, 3, device=dev)
        pos = final_lo + u * (final_hi - final_lo)  # (B,3)
        if clamp:
            pos = torch.minimum(torch.maximum(pos, lo), hi)
        return _maybe_1d(pos, return_1d)

    # No explicit ranges: sample within band_xyz using the selected geometry.
    bx, by, bz = _parse_band3(band_xyz)
    half_ext = torch.minimum(cen - lo, hi - cen)
    radii = torch.minimum(torch.tensor([bx, by, bz], device=dev), half_ext).clamp_min(
        0.0,
    )

    mode = mode.lower()
    if mode == "box":
        u = torch.rand(B, 3, device=dev) * 2.0 - 1.0  # [-1, 1]^3
        offs = u * radii.reshape(1, 3)
        pos = cen.reshape(1, 3) + offs
    elif mode == "ellipsoid":
        # uniform in ellipsoid: n ~ N(0,1)^3, unit = n/||n||; r ~ U(0,1)^(1/3)
        n = torch.randn(B, 3, device=dev)
        unit = n / torch.linalg.norm(n, dim=1, keepdim=True).clamp_min(1e-9)
        r = torch.rand(B, 1, device=dev).pow(1.0 / 3.0)
        offs = r * unit * radii.reshape(1, 3)
        pos = cen.reshape(1, 3) + offs
    else:
        raise ValueError("mode must be 'box' or 'ellipsoid'")

    if clamp:
        pos = torch.minimum(torch.maximum(pos, lo), hi)
    return _maybe_1d(pos, return_1d)


def sample_around_point_xy(
    anchor_xy: TensorLike,
    *,
    band_xy: float | Sequence[float],
    z: float,
    mode: str = "square",
    env_idx: Sequence[int] | torch.Tensor | None = None,
    clamp_to: AABB | None = None,
) -> torch.Tensor:
    """Sample around an arbitrary XY anchor with a given band; Z fixed.

    Internally uses TwoDPosRandomizer to generate XY.

    Args:
        anchor_xy: (2,) center [x, y] in meters.
        band_xy: Scalar or (bx, by) half-widths in meters.
        z: Fixed z value in meters.
        mode: "square" or "circle" (area-uniform disk/ellipse).
        env_idx: Optional subset of env indices to produce (B, 3) output.
        clamp_to: Optional AABB to clamp outputs into.

    Returns:
        torch.Tensor: (3,) if single-env/no subset; otherwise (B, 3).
    """
    dev = clamp_to.device if clamp_to is not None else get_device()
    # wide ranges; we rely on band sampling, then optionally clamp
    r2d = TwoDPosRandomizer(x_range=(-1e3, 1e3), y_range=(-1e3, 1e3), z=z)
    pos = r2d.sample(
        env_idx=env_idx,
        around_xy=anchor_xy,
        band_xy=band_xy,
        mode=mode,
        clamp_to=clamp_to,
        z=z,
    )
    return pos


def sample_in_aabb_center_xy_band(
    box: AABB,
    *,
    band_xy: float | Sequence[float],
    mode: str = "square",
    z: str | float = "center",
    z_range: tuple[float, float] | None = None,
    env_idx: Sequence[int] | torch.Tensor | None = None,
    margin: float | Sequence[float] = 0.0,
) -> torch.Tensor:
    """Sample around the AABB center in XY with a band.

    Batch semantics:
    - If get_n_envs() == 1 and env_idx is None, returns a tensor with shape (3,).
    - Otherwise returns a tensor with shape (B, 3), where B is len(env_idx) (if
      provided) or get_n_envs().

    Args:
        box: AABB region to sample within (world frame).
        band_xy: Scalar or (bx, by) half-widths in meters around the AABB center.
        mode: "square" (uniform in rectangle) or "circle" (area-uniform ellipse).
        z: One of:
            - float: fixed z height.
            - "center": use the (margin-adjusted) AABB center z.
            - "uniform": uniform z in z_range (or the margin-adjusted box z-range).
        z_range: Optional (z_low, z_high) if z == "uniform".
        env_idx: Optional subset of env indices; controls batch size and 1D/2D return.
        margin: Shrink AABB by this margin before sampling (scalar or (mx, my, mz)).

    Returns:
        torch.Tensor: Sampled position(s) on box.device, shape (3,) or (B, 3).
    """
    dev = box.device
    if isinstance(margin, (int, float)):
        m = torch.tensor([margin, margin, margin], dtype=torch.float32, device=dev)
    else:
        m = torch.as_tensor(margin, dtype=torch.float32, device=dev).reshape(3)

    lo = box.min + m
    hi = box.max - m
    # Order bounds to be safe even under extreme margins
    lo, hi = torch.minimum(lo, hi), torch.maximum(lo, hi)

    cen = 0.5 * (lo + hi)

    # Z selection
    if isinstance(z, (int, float)):
        z_val: float | None = float(z)
        z_vec: torch.Tensor | None = None
    elif isinstance(z, str) and z.lower() == "center":
        z_val, z_vec = float(cen[2]), None
    elif isinstance(z, str) and z.lower() == "uniform":
        zl, zh = (
            (float(lo[2]), float(hi[2]))
            if z_range is None
            else (z_range[0], z_range[1])
        )
        B, _ = _resolve_B_and_1d(env_idx)
        z_vec = zl + torch.rand(B, device=dev) * (zh - zl)
        z_val = None
    else:
        raise ValueError("z must be a float, 'center', or 'uniform'.")

    # XY via TwoDPosRandomizer (uniform in square; or area-uniform ellipse when mode='circle')
    r2d = TwoDPosRandomizer(
        (float(lo[0]), float(hi[0])),
        (float(lo[1]), float(hi[1])),
        z=float(cen[2]),
    )

    if z_vec is None:
        pos = r2d.sample(
            env_idx=env_idx,
            around_xy=cen[:2],
            band_xy=band_xy,
            mode=mode,
            z=z_val,
        )
    else:
        tmp = r2d.sample(
            env_idx=env_idx,
            around_xy=cen[:2],
            band_xy=band_xy,
            mode=mode,
            z=float(cen[2]),
        )
        tmp = tmp if tmp.ndim == 2 else tmp.unsqueeze(0)
        tmp[:, 2] = z_vec
        pos = tmp

    # Final clamp into the valid box
    pos = torch.minimum(torch.maximum(pos, lo), hi)
    return _maybe_1d(pos, _resolve_B_and_1d(env_idx)[1])


def sample_xy_k_noncolliding(
    box: AABB,
    *,
    k: int,
    band_xy: float | Sequence[float],
    z: float | str = "center",
    min_sep: float,
    max_sep: float = np.inf,
    env_idx: Sequence[int] | torch.Tensor | None = None,
    mode: str = "square",
    margin: float | Sequence[float] = 0.0,
    max_tries: int = 12,
) -> tuple[torch.Tensor, ...]:
    """Return K planar placements around the AABB center with pairwise XY >= min_sep.

    Uses TwoDPosRandomizer; preserves (3,) vs (B,3) semantics per env_idx/get_n_envs.
    """
    if k < 1:
        raise ValueError("k must be >= 1")

    dev = box.device
    B, return_1d = _resolve_B_and_1d(env_idx)

    # bounds (ordered) after margin
    if isinstance(margin, (int, float)):
        m = torch.tensor([margin, margin, margin], dtype=torch.float32, device=dev)
    else:
        m = torch.as_tensor(margin, dtype=torch.float32, device=dev).reshape(3)
    lo = box.min + m
    hi = box.max - m
    lo, hi = torch.minimum(lo, hi), torch.maximum(lo, hi)

    def _one(env_subset=None) -> torch.Tensor:
        p = sample_in_aabb_center_xy_band(
            box,
            band_xy=band_xy,
            mode=mode,
            z=z,
            env_idx=env_subset,
            margin=margin,
        )
        return p.reshape(-1, 3)

    # initial draws
    poses = [_one(env_idx) for _ in range(k)]  # each (B,3)

    def _collide_mask(ps: list[torch.Tensor]) -> torch.Tensor:
        xy = torch.stack([p[:, :2] for p in ps], dim=1)  # (B,K,2)
        d = torch.norm(xy.unsqueeze(2) - xy.unsqueeze(1), dim=-1)  # (B,K,K)
        diag = torch.eye(k, device=dev, dtype=torch.bool).unsqueeze(0)

        # Ignore self-distances for the min/max checks by masking the diagonal.
        d_no_diag_for_min = torch.where(diag, torch.full_like(d, torch.inf), d)
        too_close = (d_no_diag_for_min < min_sep).any(dim=(1, 2))

        if np.isinf(float(max_sep)):
            too_far = torch.zeros_like(too_close)
        else:
            d_no_diag_for_max = torch.where(diag, torch.zeros_like(d), d)
            too_far = (d_no_diag_for_max > max_sep).any(dim=(1, 2))

        return too_close | too_far

    bad = _collide_mask(poses)
    tries = 0
    while bad.any().item() and tries < max_tries:
        idx = bad.nonzero(as_tuple=False).squeeze(1)
        for i in range(k):
            poses[i][idx] = _one(idx)
        bad = _collide_mask(poses)
        tries += 1

    # Final safety: small XY jitter + clamp for any remaining collisions
    if bad.any().item():
        print("NOT ABLE TO FIND SATISFYING POSITIONS")
        idx = bad.nonzero(as_tuple=False).squeeze(1)
        jitter = (torch.rand(idx.numel(), k, 2, device=dev) * 2 - 1) * (0.25 * min_sep)
        for i in range(k):
            poses[i][idx, :2] += jitter[:, i, :]
            # keep inside bounds after jitter
            poses[i][idx] = torch.minimum(torch.maximum(poses[i][idx], lo), hi)

    # restore per-output shapes
    out: list[torch.Tensor] = []
    for p in poses:
        out.append(p.squeeze(0) if (return_1d and p.shape[0] == 1) else p)

    return tuple(out)


def sample_xy_pair_center_annulus(
    box: AABB,
    *,
    r_min: float,
    r_max: float,
    band_xy: float | Sequence[float],
    cube_z: float | str = "center",
    goal_z: float | str = "same_as_cube",
    env_idx: Sequence[int] | torch.Tensor | None = None,
    margin: float | Sequence[float] = 0.0,
    max_tries: int = 12,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Return (cube_pos, goal_pos) s.t. ||goal_xy - cube_xy|| ∈ [r_min, r_max] (area-uniform annulus)."""
    dev = box.device
    B, return_1d = _resolve_B_and_1d(env_idx)

    if isinstance(margin, (int, float)):
        m = torch.tensor([margin, margin, margin], dtype=torch.float32, device=dev)
    else:
        m = torch.as_tensor(margin, dtype=torch.float32, device=dev).reshape(3)
    lo = box.min + m
    hi = box.max - m
    lo, hi = torch.minimum(lo, hi), torch.maximum(lo, hi)

    # sample cube around center
    cube = sample_in_aabb_center_xy_band(
        box,
        band_xy=band_xy,
        mode="square",
        z=cube_z,
        env_idx=env_idx,
        margin=margin,
    ).reshape(B, 3)

    # goal by area-uniform annulus around cube: r ~ sqrt(U*(R^2 - r^2) + r^2), theta ~ U[0,2π]
    def _goal_for(rows: torch.Tensor) -> torch.Tensor:
        u = torch.rand(rows.numel(), device=dev)
        r = torch.sqrt(u * (r_max * r_max - r_min * r_min) + r_min * r_min)
        theta = 2 * torch.pi * torch.rand(rows.numel(), device=dev)
        off = torch.stack([r * torch.cos(theta), r * torch.sin(theta)], dim=1)  # (n,2)
        g = cube[rows].clone()
        g[:, :2] = g[:, :2] + off
        # clamp XY into box (distortion handled by resample loop)
        g[:, 0] = g[:, 0].clamp(lo[0], hi[0])
        g[:, 1] = g[:, 1].clamp(lo[1], hi[1])
        return g

    goal = _goal_for(torch.arange(B, device=dev))

    def _bad(g: torch.Tensor) -> torch.Tensor:
        d = torch.norm(g[:, :2] - cube[:, :2], dim=1)
        return (d < r_min) | (d > r_max)

    bad = _bad(goal)
    tries = 0
    while bad.any().item() and tries < max_tries:
        idx = bad.nonzero(as_tuple=False).squeeze(1)
        goal[idx] = _goal_for(idx)
        bad = _bad(goal)
        tries += 1

    # Z for goal
    if goal_z == "same_as_cube":
        goal[:, 2] = cube[:, 2]
    elif isinstance(goal_z, (int, float)):
        goal[:, 2] = float(goal_z)
    elif goal_z in ("center", "uniform"):
        ztmp = sample_in_aabb_center_xy_band(
            box,
            band_xy=band_xy,
            z=goal_z,
            env_idx=env_idx,
            margin=margin,
        ).reshape(B, 3)[:, 2]
        goal[:, 2] = ztmp
    else:
        raise ValueError(
            "goal_z must be float | 'same_as_cube' | 'center' | 'uniform'.",
        )

    # final clamp inside box
    goal = torch.minimum(torch.maximum(goal, lo), hi)

    # restore shape semantics
    cube = cube.squeeze(0) if (return_1d and cube.shape[0] == 1) else cube
    goal = goal.squeeze(0) if (return_1d and goal.shape[0] == 1) else goal
    return cube, goal


# --------------------------------------------------------------------- #
# Constrain an arbitrary sampler to an AABB
# --------------------------------------------------------------------- #


def sampler_in_aabb(
    base_sampler: Callable[..., torch.Tensor],
    box: AABB,
    *,
    policy: str = "rejection",
    max_tries: int = 64,
) -> Callable[..., torch.Tensor]:
    """Wrap a sampler so its outputs lie within an AABB.

    The wrapper preserves batch semantics:
    - If the underlying sampler returns (3,) and get_n_envs() == 1, the wrapper
      returns (3,).
    - If env_idx is provided, the wrapper returns (B, 3).

    Args:
        base_sampler: Callable returning (3,) or (B, 3) torch tensors; should accept
            env_idx=... in its kwargs to control the batch size.
        box: AABB to enforce.
        policy: One of:
            - "rejection" (default): resample out-of-box rows up to max_tries, then
              clamp any remaining offenders.
            - "clamp": always clamp outputs to the box.
        max_tries: Maximum resampling rounds for "rejection".

    Returns:
        Callable[..., torch.Tensor]: A new sampler with the same signature as base_sampler.

    Example:
        >>> r3d = ThreeDPosRandomizer(x_range=(0,1), y_range=(0,1), z_range=(0,1))
        >>> safe = sampler_in_aabb(r3d.sample, box, policy="rejection")
        >>> P = safe(env_idx=[0, 1, 2])  # (3, 3)
    """
    policy = policy.lower()
    if policy not in ("rejection", "clamp"):
        raise ValueError("policy must be 'rejection' or 'clamp'")

    def _wrapped(*args, **kwargs) -> torch.Tensor:
        dev = box.device
        B, return_1d = _resolve_B_and_1d(kwargs.get("env_idx"))

        if policy == "rejection":
            pos = base_sampler(*args, **kwargs)
            pos = (
                pos
                if torch.is_tensor(pos)
                else torch.as_tensor(pos, dtype=torch.float32, device=dev)
            )
            pos = pos.reshape(B, 3)
            mask = ~box.contains(pos)  # (B,)
            tries = 0
            while mask.any().item() and tries < max_tries:
                resamp = base_sampler(*args, **kwargs)
                resamp = (
                    resamp
                    if torch.is_tensor(resamp)
                    else torch.as_tensor(resamp, dtype=torch.float32, device=dev)
                )
                resamp = resamp.reshape(B, 3)
                pos[mask] = resamp[mask]
                mask = ~box.contains(pos)
                tries += 1
            if mask.any().item():
                pos = box.clamp(pos)
            return _maybe_1d(pos, return_1d)

        # clamp policy
        pos = base_sampler(*args, **kwargs)
        pos = (
            pos
            if torch.is_tensor(pos)
            else torch.as_tensor(pos, dtype=torch.float32, device=dev)
        )
        pos = box.clamp(pos.reshape(B, 3))
        return _maybe_1d(pos, return_1d)

    return _wrapped


# --------------------------------------------------------------------- #
# (Optional) convenience: dict -> spaces (float Boxes)
# --------------------------------------------------------------------- #


def dict_to_space(tree, big=np.inf) -> spaces.Space:
    """Recursively convert a structure to a Gymnasium Space (float32 Boxes).

    Args:
        tree: Nested structure of dict / tensor / array / list / scalar.
        big: Bound magnitude for Boxes (default ±∞).

    Returns:
        spaces.Space: spaces.Dict for dicts; spaces.Box for leaves.
    """
    if isinstance(tree, dict):
        return spaces.Dict({k: dict_to_space(v, big) for k, v in tree.items()})
    if torch.is_tensor(tree):
        shape = tuple(tree.shape)
        return spaces.Box(-big, big, shape, np.float32)
    arr = np.asarray(tree, dtype=np.float32)
    return spaces.Box(-big, big, arr.shape, np.float32)


def sample_index(
    choices: range | tuple[int, int] | Sequence[int] | torch.Tensor,
    env_idx: Sequence[int] | torch.Tensor | None = None,
) -> torch.Tensor:
    """Sample integer indices per environment.

    Args:
        choices: One of:
            - range(start, stop[, step]) (samples from that range)
            - (low, high) integer tuple (samples uniformly from [low, high))
            - Sequence / 1D tensor of explicit integer choices
        env_idx: Optional subset of env indices being reset. If provided, the
            batch size is len(env_idx) and the output is always 2D.

    Returns:
        torch.Tensor: torch.int64 tensor of sampled indices with shape:
            - (1,) if env_idx is None and get_n_envs() == 1
            - (B, 1) otherwise

    Raises:
        ValueError: If choices is empty or invalid.
        TypeError: If (low, high) are not integers.
    """
    if env_idx is not None:
        B = int(torch.as_tensor(env_idx).numel())
        return_scalar_1d = False

    else:
        B = int(get_n_envs())
        return_scalar_1d = B == 1

    if isinstance(choices, range):
        N = len(choices)
        if N <= 0:
            raise ValueError("empty range")
        idx = torch.randint(0, N, (B,))
        vals = choices.start + idx * choices.step
        vals = torch.as_tensor(vals, dtype=torch.int64)

    elif isinstance(choices, tuple) and len(choices) == 2:
        low, high = choices
        if not (isinstance(low, int) and isinstance(high, int)):
            raise TypeError("(low, high) must be ints")
        if high <= low:
            raise ValueError("need high > low for [low, high)")
        vals = torch.randint(low, high, (B,), dtype=torch.int64)

    else:
        arr = torch.as_tensor(choices, dtype=torch.int64)
        if arr.ndim != 1:
            arr = arr.flatten()
        if arr.numel() == 0:
            raise ValueError("empty choices")
        idx = torch.randint(0, arr.numel(), (B,))
        vals = arr[idx]

    return (
        vals.view(
            1,
        )
        if return_scalar_1d
        else vals.view(B, 1)
    )
