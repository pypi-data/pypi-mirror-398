from __future__ import annotations

import contextlib
import time
from collections.abc import Callable
from typing import Any

import numpy as np

try:
    import openvr  # type: ignore
except Exception as _e:  # pragma: no cover
    openvr = None  # type: ignore[assignment]
    _OPENVR_IMPORT_ERROR: Exception | None = _e
else:  # pragma: no cover
    _OPENVR_IMPORT_ERROR = None

from .device import Device
from .triad_utils import TriadLocalPose as tlp, triad_openvr


def _require_openvr():  # pragma: no cover
    if openvr is None:
        raise RuntimeError(
            "Vive controller support requires 'openvr' (pip install openvr) and a working "
            "SteamVR installation.",
        ) from _OPENVR_IMPORT_ERROR
    return openvr


class ViveController(Device):
    """Minimal Vive controller reader.

    - Pose: returns local position (x, y, z) and quaternion (w, x, y, z)
    - Recalibrate: press GRIP (resets both orientation and position)
    - Gripper action (optional callback):
        - trigger > 0.90: +1 (close)
        - trigger < 0.10: -1 (open)
        - otherwise: 0 (no-op)
    """

    def __init__(
        self,
        controller_id: str = "controller_1",
        side: str = "left",
        *,
        source: str = "auto",
        reorthonormalize: bool = True,
        gripper_callback: Callable[[int], None] | None = None,
        haptics: bool = True,
    ) -> None:
        """Initializes the Vive Controller reader.

        Connects to OpenVR, finds the specified controller based on side or ID,
        and sets up calibration and gripper action parameters.

        Args:
            controller_id: The OpenVR device ID to fall back on
                (e.g., "controller_1").
            side: The preferred controller role ("left" or "right").
            source: Pose source (e.g., "auto").
            reorthonormalize: Whether to force rotation matrices to be
                orthonormal, correcting for potential drift.
            gripper_callback: An optional function to call with the
                gripper action (-1 for open, +1 for close).
            haptics: Whether to enable haptic feedback on calibration
                and gripper actions.
        """
        _require_openvr()
        super().__init__(controller="OSCPose_abs_quat", normalized=False, gripper=True)
        self.vr = triad_openvr()
        self.vrsystem = self.vr.vrsystem

        self.side = side.lower()
        self.controller_id = controller_id
        self.source = source
        self.reorthonormalize = reorthonormalize
        self.haptics = haptics
        self._gripper_cb = gripper_callback

        # Resolve device
        self.dev = self._resolve_controller(self.side, self.controller_id)
        self.name = self._device_name(self.dev)

        # Calibration state (R0, p0)
        self.R0 = np.eye(3)
        self.p0 = np.zeros(3)
        self._has_cal = False

        # Input edge state
        self._grip_prev = False
        self._trigger_zone = 0  # -1=open, 0=mid, 1=close

        # Initial calibration
        self.recalibrate()

    # -------------------- device discovery --------------------

    def _device_name(self, dev) -> str:
        """Finds the human-readable name of the OpenVR device.

        Args:
            dev: The OpenVR device object.

        Returns:
            A string name for the device.
        """
        for name, d in self.vr.devices.items():
            if getattr(d, "index", None) == getattr(dev, "index", None):
                return name
        return f"controller@{getattr(dev, 'index', '?')}"

    def _resolve_controller(self, side: str, fallback_id: str):
        """Finds and returns the OpenVR device object for the controller.

        Tries to find the device by its designated role (left/right hand).
        If that fails, it falls back to the provided fallback_id, and
        if that also fails, it returns the first available controller.

        Args:
            side: The preferred role ("left" or "right").
            fallback_id: The device ID to check if the role-based
                search fails.

        Returns:
            The resolved OpenVR device object.

        Raises:
            RuntimeError: If no controller device is found.
        """
        side = (side or "").lower()
        ov = _require_openvr()
        try:
            target_role = {
                "left": ov.TrackedControllerRole_LeftHand,
                "right": ov.TrackedControllerRole_RightHand,
            }.get(side)
        except Exception:
            target_role = None

        # Prefer role match
        if target_role is not None:
            for dev in self.vr.devices.values():
                if getattr(dev, "device_class", "") != "Controller":
                    continue
                try:
                    role = self.vrsystem.getControllerRoleForTrackedDeviceIndex(
                        dev.index,
                    )
                    if role == target_role:
                        return dev
                except Exception:
                    pass

        # Fallback by id, else first controller
        if fallback_id in self.vr.devices:
            return self.vr.devices[fallback_id]
        for dev in self.vr.devices.values():
            if getattr(dev, "device_class", "") == "Controller":
                return dev

        raise RuntimeError("No Vive controllers found. Is SteamVR running.")

    # -------------------- calibration --------------------

    def recalibrate(self) -> None:
        """Resets the (R0, p0) calibration origin.

        This method attempts to read the controller's current world pose and
        sets that as the new origin. (R0, p0) is stored as the "zero" pose, and
        subsequent read calls will return poses relative to this one.
        """
        deadline = time.time() + 1.0
        Rw_pw: tuple[np.ndarray, np.ndarray] | None = None
        while Rw_pw is None and time.time() < deadline:
            Rw_pw = tlp.read_pose(self.dev, self.source)
            if Rw_pw is None:
                time.sleep(0.002)
        if Rw_pw is None:
            return

        Rw, pw = Rw_pw
        if self.reorthonormalize:
            Rw = tlp.orthonormalize(Rw)

        self.R0 = Rw.copy()
        self.p0 = pw.copy()
        self._has_cal = True

        print(f"\n[CONTROLLER] {self.name} {self.side} recalibrated.", flush=True)
        if self.haptics:
            with contextlib.suppress(Exception):
                self.dev.trigger_haptic_pulse(duration_micros=900, axis_id=0)

    # -------------------- inputs -> actions --------------------

    def _parse_actions(self, buttons: dict[str, Any] | None) -> list[int]:
        """Parses button inputs to trigger recalibration or gripper actions.

        - Grip button: A rising edge (press) triggers recalibrate().
        - Trigger:
            - Crossing a high threshold (0.90) returns a +1 (close) action.
            - Crossing a low threshold (0.10) returns a -1 (open) action.
            - Calls the _gripper_cb callback with the action.
            - Triggers haptics if enabled.

        Args:
            buttons: A dictionary of button states from OpenVR.

        Returns:
            The gripper action: +1 (close), -1 (open), or 0 (no-op).
        """
        if not buttons:
            return [0]

        # Grip edge -> recalibrate
        grip_pressed = bool(
            buttons.get("grip_button", False) or buttons.get("grip", False),
        )

        if (not self._grip_prev) and grip_pressed:
            self.recalibrate()
        self._grip_prev = grip_pressed

        # Trigger zoning -> gripper callback
        trig = float(buttons.get("trigger", 0.0))
        new_zone = 1 if trig > 0.90 else (-1 if trig < 0.10 else 0)

        action = 0
        if new_zone != self._trigger_zone:
            self._trigger_zone = new_zone
            if new_zone in (-1, 1):
                action = new_zone
                if self._gripper_cb is not None:
                    with contextlib.suppress(Exception):
                        self._gripper_cb(action)
                if self.haptics:
                    with contextlib.suppress(Exception):
                        self.dev.trigger_haptic_pulse(duration_micros=600, axis_id=0)
        return [action]

    # -------------------- main read --------------------

    def read(self) -> dict[str, Any]:
        """Reads the latest pose, buttons, and gripper action from the controller.

        This is the main data polling method. It performs several steps:
        1. If not calibrated, returns a neutral pose.
        2. Reads the current world pose (Rw, pw) from OpenVR.
        3. Calculates the local pose (Rloc, ploc) relative to (R0, p0).
        4. Remaps the local axes (x=forward, y=left, z=up).
        5. Converts the local rotation to a quaternion (w, x, y, z).
        6. Reads button states.
        7. Parses button states for gripper or recalibration actions.

        Returns:
            A dictionary containing the pose, button state, gripper action,
            and metadata:
            {
                "pose": [px, py, pz, qw, qx, qy, qz],
                "buttons": { ... button states ... },
                "gripper": List[int],
                "meta": {"id": str, "side": str, "t": float}
            }
        """
        if not self._has_cal:
            return {
                "pose": [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
                "buttons": {},
                "gripper": [0],
                "meta": {"id": self.name, "side": self.side, "t": time.time()},
            }

        # World pose
        Rw_pw = tlp.read_pose(self.dev, self.source)
        if Rw_pw is None:
            return {
                "pose": [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
                "buttons": {},
                "gripper": [0],
                "meta": {"id": self.name, "side": self.side, "t": time.time()},
            }

        Rw, pw = Rw_pw
        if self.reorthonormalize:
            Rw = tlp.orthonormalize(Rw)

        # Local pose (relative to calibration)
        Rloc = self.R0.T @ Rw
        ploc = self.R0.T @ (pw - self.p0)

        # Axis remap (Genesis axes: x=forward, y=left, z=up)
        S = np.array([[0, -1, 0], [-1, 0, 0], [0, 0, -1]], dtype=float)
        Rloc = S @ Rloc @ S.T
        ploc = S @ ploc

        # Quaternion (w, x, y, z) to avoid Euler singularities
        qw, qx, qy, qz = tlp.quat_wxyz_from_R(Rloc)

        # Inputs
        try:
            buttons = self.dev.get_controller_inputs() or {}
        except Exception:
            buttons = {}

        if self.gripper:
            gripper_action = self._parse_actions(buttons)

            return {
                "pose": [
                    float(ploc[0]),
                    float(ploc[1]),
                    float(ploc[2]),
                    qw,
                    qx,
                    qy,
                    qz,
                ],
                "buttons": buttons,
                "gripper": gripper_action,
                "meta": {"id": self.name, "side": self.side, "t": time.time()},
            }
        else:
            return {
                "pose": [
                    float(ploc[0]),
                    float(ploc[1]),
                    float(ploc[2]),
                    qw,
                    qx,
                    qy,
                    qz,
                ],
                "buttons": buttons,
                "gripper": [0],
                "meta": {"id": self.name, "side": self.side, "t": time.time()},
            }

    def get_action(self):
        return self.read()
