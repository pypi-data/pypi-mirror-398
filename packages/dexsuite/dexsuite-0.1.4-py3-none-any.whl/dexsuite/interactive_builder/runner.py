"""Environment runner for builder specs (torch-only actions).

This module intentionally keeps teleoperation support minimal and strict:
- The environment is always stepped with a torch.Tensor action.
- Device adapters return a flat action vector matching env.action_space.

Device support:
- keyboard: Uses dexsuite.devices.Keyboard when available (pynput-based).
- spacemouse: Uses dexsuite.devices.Spacemouse (requires evdev on Linux, or hidapi
  on macOS/Windows).
- vive_controller / vive_tracker: Uses Vive devices (requires openvr).
- none: Sends zero actions.

Notes:
    This runner focuses on single-arm teleop. For bimanual robots you can still
    run the environment with --input none (or extend this module to drive each
    arm independently).
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Protocol

import torch

from .spec import BuilderSpec


class ActionSource(Protocol):
    """Produce torch actions for env.step(action)."""

    def next_action(self) -> torch.Tensor: ...

    def close(self) -> None: ...


def run_from_spec(spec: BuilderSpec, *, input_device: str | None = None) -> int:
    """Build an environment from spec and run a teleop loop.

    Args:
        spec: Builder spec.
        input_device: Teleoperation device name.

    Returns:
        Exit code (0 success).
    """
    import dexsuite as ds

    input_device = spec.input_device if input_device is None else str(input_device)

    if spec.type_of_robot == "bimanual" and input_device != "none":
        raise ValueError(
            "Teleop input is currently implemented for single-arm robots only. "
            "Use --input none for bimanual (or extend runner.py).",
        )

    kw = spec.to_make_kwargs()
    env = ds.make(spec.task, **kw)
    try:
        env.reset()
        src = _make_action_source(env, spec, input_device=str(input_device))
        try:
            _loop(env, spec, src)
        finally:
            src.close()
    finally:
        env.close()
    return 0


def _loop(env, spec: BuilderSpec, src: ActionSource) -> None:
    dt = 1.0 / float(max(1, spec.control_hz))
    n_envs = int(getattr(env, "n_envs", 1) or 1)

    last = time.time()
    try:
        while True:
            a = src.next_action()
            if not torch.is_tensor(a):
                raise TypeError("ActionSource must return a torch.Tensor.")
            if a.dtype != torch.float32:
                a = a.to(dtype=torch.float32)

            if n_envs > 1 and a.ndim == 1:
                a = a.unsqueeze(0).repeat(n_envs, 1)

            with torch.no_grad():
                obs, reward, terminated, truncated, info = env.step(a)

            # Best-effort done handling across scalar/tensor returns.
            done = _as_bool_any(terminated) or _as_bool_any(truncated)
            if done:
                env.reset()

            # Frame pacing (best-effort)
            now = time.time()
            sleep = dt - (now - last)
            if sleep > 0:
                time.sleep(sleep)
            last = now
    except KeyboardInterrupt:
        return None


def _as_bool_any(x: Any) -> bool:
    if torch.is_tensor(x):
        if x.numel() == 1:
            return bool(x.item())
        return bool(torch.any(x).item())
    return bool(x)


def _robot_device(env) -> torch.device:
    dev = getattr(getattr(env, "robot", None), "device", None)
    if isinstance(dev, torch.device):
        return dev
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


@dataclass(frozen=True)
class _LayoutInfo:
    arm_dim: int
    grip_dim: int


def _layout_info(env) -> _LayoutInfo:
    robot = getattr(env, "robot", None)
    layout = getattr(robot, "_layout", None)
    if layout is None or not getattr(layout, "segments", None):
        raise RuntimeError("Robot action layout not available (robot._layout missing).")

    def _w(seg) -> int:
        return int(seg.stop - seg.start)

    segs = list(layout.segments)
    # Single-arm convention: [manipulator, gripper?]
    arm_dim = _w(segs[0]) if segs else 0
    grip_dim = _w(segs[1]) if len(segs) > 1 else 0
    return _LayoutInfo(arm_dim=arm_dim, grip_dim=grip_dim)


def _pack_single_action(
    env,
    *,
    pose: torch.Tensor | None,
    gripper: torch.Tensor | None,
) -> torch.Tensor:
    info = _layout_info(env)
    dev = _robot_device(env)
    if pose is None:
        pose = torch.zeros(info.arm_dim, dtype=torch.float32, device=dev)
    pose = pose.to(device=dev, dtype=torch.float32).flatten()
    if pose.numel() != info.arm_dim:
        raise ValueError(
            f"arm action dim mismatch: expected {info.arm_dim}, got {pose.numel()}",
        )

    if info.grip_dim == 0:
        return pose.contiguous()

    if gripper is None:
        grip = torch.zeros(info.grip_dim, dtype=torch.float32, device=dev)
    else:
        grip = gripper.to(device=dev, dtype=torch.float32).flatten()
        if grip.numel() == 1 and info.grip_dim > 1:
            grip = grip.repeat(info.grip_dim)
        if grip.numel() != info.grip_dim:
            raise ValueError(
                f"gripper action dim mismatch: expected {info.grip_dim}, got {grip.numel()}",
            )
    return torch.cat([pose, grip], dim=0).contiguous()


class _ZeroSource:
    def __init__(self, env) -> None:
        self._env = env
        self._dev = _robot_device(env)
        self._dim = int(getattr(env.action_space, "shape", (0,))[0])

    def next_action(self) -> torch.Tensor:
        return torch.zeros(self._dim, dtype=torch.float32, device=self._dev)

    def close(self) -> None:
        return None


class _DexsuiteDictDeviceSource:
    """Wrap a dexsuite.devices device instance and pack its dict actions into a tensor."""

    def __init__(self, env, *, device_obj) -> None:
        self._env = env
        self._dev_obj = device_obj

    def next_action(self) -> torch.Tensor:
        d = self._dev_obj.get_action()
        pose = d.get("pose")
        grip = d.get("gripper")
        pose_t = None if pose is None else torch.as_tensor(pose, dtype=torch.float32)
        grip_t = None if grip is None else torch.as_tensor(grip, dtype=torch.float32)
        return _pack_single_action(self._env, pose=pose_t, gripper=grip_t)

    def close(self) -> None:
        if hasattr(self._dev_obj, "close"):
            try:
                self._dev_obj.close()
            except Exception:
                pass


def _make_action_source(env, spec: BuilderSpec, *, input_device: str) -> ActionSource:
    input_device = str(input_device).lower()
    if input_device == "none":
        return _ZeroSource(env)

    # Determine expected arm action dimensionality to validate device compatibility.
    dims = _layout_info(env)

    if input_device == "keyboard":
        if dims.arm_dim != 6:
            raise ValueError(
                "keyboard device currently supports only 6D pose controllers "
                f"(got arm_dim={dims.arm_dim}).",
            )
        try:
            from dexsuite.devices import Keyboard  # type: ignore
        except Exception as e:  # pragma: no cover
            raise RuntimeError(
                "Keyboard teleop requires 'pynput' (pip install pynput).",
            ) from e
        # The device uses its own controller name convention ("OSCPose").
        dev = Keyboard(
            controller="OSCPose",
            normalized=True,
            gripper=(dims.grip_dim > 0),
        )
        return _DexsuiteDictDeviceSource(env, device_obj=dev)

    if input_device == "spacemouse":
        if dims.arm_dim != 6:
            raise ValueError(
                "spacemouse teleop currently supports only 6D pose controllers "
                f"(got arm_dim={dims.arm_dim}).",
            )
        from dexsuite.devices import Spacemouse  # type: ignore

        try:
            dev = Spacemouse(
                path_or_ids=None,
                controller="OSCPose",
                normalized=True,
                gripper=(dims.grip_dim > 0),
            )
        except Exception as e:  # pragma: no cover
            raise RuntimeError(
                "Spacemouse teleop requires dexsuite[spacemouse] and OS access to the device "
                "(/dev/input on Linux, or HIDAPI on macOS/Windows).",
            ) from e
        return _DexsuiteDictDeviceSource(env, device_obj=dev)

    if input_device == "vive_controller":
        if dims.arm_dim != 7:
            raise ValueError(
                "vive_controller teleop currently supports only 7D pose controllers "
                f"(got arm_dim={dims.arm_dim}).",
            )
        try:
            from dexsuite.devices import ViveController  # type: ignore
        except Exception as e:  # pragma: no cover
            raise RuntimeError("Vive controller teleop requires 'openvr'.") from e
        dev = ViveController(side="left")
        return _DexsuiteDictDeviceSource(env, device_obj=dev)

    if input_device == "vive_tracker":
        if dims.arm_dim != 7:
            raise ValueError(
                "vive_tracker teleop currently supports only 7D pose controllers "
                f"(got arm_dim={dims.arm_dim}).",
            )
        try:
            from dexsuite.devices import ViveTracker  # type: ignore
        except Exception as e:  # pragma: no cover
            raise RuntimeError("Vive tracker teleop requires 'openvr'.") from e
        dev = ViveTracker(side="center")
        return _DexsuiteDictDeviceSource(env, device_obj=dev)

    raise ValueError(f"Unknown input_device: {input_device!r}")
