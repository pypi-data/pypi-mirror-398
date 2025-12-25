from __future__ import annotations

import contextlib
import math
import time
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
from .reset_helper import ResetHelper
from .triad_utils import TriadLocalPose as tlp, triad_openvr


def _require_openvr():  # pragma: no cover
    if openvr is None:
        raise RuntimeError(
            "Vive tracker support requires 'openvr' (pip install openvr) and a working "
            "SteamVR installation.",
        ) from _OPENVR_IMPORT_ERROR
    return openvr


class ViveTracker(Device):
    """Vive Tracker reader (pose + auto recalibration on stillness).

    - Pose: local XYZ + quaternion (w, x, y, z)
    - Auto recalibrate: if the tracker hasn't moved (pos/angle deltas below thresholds)
      for still_time_sec, we reset (R0, p0) to the current world pose.
    - No gripper actions.
    """

    def __init__(
        self,
        tracker_id: str = "tracker_1",
        side: str = "center",
        *,
        source: str = "auto",
        reorthonormalize: bool = True,
        haptics: bool = True,
        # --- stillness auto-cal params ---
        still_time_sec: float = 5.0,
        still_lin_thresh_m: float = 0.003,  # 3 mm
        still_ang_thresh_deg: float = 1.0,  # 1 degree
        gripper: bool = True,
        reset_key: int = "r",
    ) -> None:
        """Initializes the Vive Tracker reader.

        Connects to OpenVR, finds the specified tracker, and sets up
        parameters for stillness-based auto-recalibration.

        Args:
            tracker_id: The OpenVR device ID to look for (e.g., "tracker_1").
            side: A string identifier for the tracker's role (e.g., "center").
            source: Pose source (e.g., "auto").
            reorthonormalize: Whether to force rotation matrices to be
                orthonormal, correcting for potential drift.
            haptics: Whether to enable haptic feedback on (re)calibration.
            still_time_sec: Duration of stillness (in seconds) required
                to trigger an auto-recalibration.
            still_lin_thresh_m: The maximum linear movement (in meters)
                allowed to be considered "still".
            still_ang_thresh_deg: The maximum angular movement (in degrees)
                allowed to be considered "still".
            gripper: Whether this device provides gripper (passed to super).
        """
        _require_openvr()
        super().__init__(
            controller="OSCPOSE_abs_quat",
            normalized=False,
            gripper=gripper,
        )
        self.vr = triad_openvr()
        self.vrsystem = self.vr.vrsystem

        self.side = side.lower()
        self.tracker_id = tracker_id
        self.source = source
        self.reorthonormalize = reorthonormalize
        self.haptics = haptics

        # Resolve device (GenericTracker)
        self.dev = self._resolve_tracker(self.tracker_id)
        self.name = self._device_name(self.dev)

        # Calibration state (R0, p0)
        self.R0 = np.eye(3)
        self.p0 = np.zeros(3)
        self._has_cal = False

        # --- stillness detection state ---
        self.still_time_sec = float(still_time_sec)
        self.still_lin_thresh = float(still_lin_thresh_m)
        self.still_ang_thresh_rad = math.radians(float(still_ang_thresh_deg))

        self._last_world_Rw: np.ndarray | None = None
        self._last_world_pw: np.ndarray | None = None
        self._last_motion_t: float = time.time()
        self._auto_calib_armed: bool = True  # recalibrate once per still period

        self.reset_helper = ResetHelper(reset_key)
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
        return f"tracker@{getattr(dev, 'index', '?')}"

    def _resolve_tracker(self, fallback_id: str):
        """Finds and returns the OpenVR device object for the tracker.

        Tries to find the device in the following order:
        1. By the exact fallback_id.
        2. The first device with a matching device class (e.g., "GenericTracker").
        3. The first device matching the OpenVR TrackedDeviceClass.

        Args:
            fallback_id: The preferred device ID to check first.

        Returns:
            The resolved OpenVR device object.

        Raises:
            RuntimeError: If no tracker device is found.
        """
        if fallback_id in self.vr.devices:
            return self.vr.devices[fallback_id]
        for dev in self.vr.devices.values():
            if getattr(dev, "device_class", "") in (
                "GenericTracker",
                "Tracker",
                "ViveTracker",
            ):
                return dev
        for dev in self.vr.devices.values():
            try:
                idx = getattr(dev, "index", None)
                if idx is None:
                    continue
                if (
                    self.vrsystem.getTrackedDeviceClass(idx)
                    == _require_openvr().TrackedDeviceClass_GenericTracker
                ):
                    return dev
            except Exception:
                pass
        raise RuntimeError("No Vive Trackers found. Is SteamVR running?")

    # -------------------- calibration --------------------

    def _set_calibration(self, Rw: np.ndarray, pw: np.ndarray) -> None:
        """Internal helper to set the (R0, p0) calibration pose.

        This pose (R0, p0) is stored as the "origin" or "zero" pose.
        Subsequent read calls will return poses relative to this one.

        Args:
            Rw: The world-space rotation matrix (3x3 np.ndarray) to set as R0.
            pw: The world-space position vector (3-element np.ndarray) to set as p0.
        """
        if self.reorthonormalize:
            Rw = tlp.orthonormalize(Rw)
        self.R0 = Rw.copy()
        self.p0 = pw.copy()
        self._has_cal = True
        print(f"\n[TRACKER] {self.name} {self.side} recalibrated.", flush=True)
        if self.haptics:
            with contextlib.suppress(Exception):
                self.dev.trigger_haptic_pulse(duration_micros=900, axis_id=0)

    def recalibrate(
        self,
        Rw: np.ndarray | None = None,
        pw: np.ndarray | None = None,
    ) -> None:
        """Resets the (R0, p0) calibration origin.

        If (Rw, pw) are provided, they are used as the new origin.
        If not, this method attempts to read the tracker's current
        world pose and sets that as the new origin.

        Args:
            Rw: Optional world-space rotation matrix (3x3 np.ndarray).
            pw: Optional world-space position vector (3-element np.ndarray).
        """
        if Rw is None or pw is None:
            deadline = time.time() + 1.0
            Rw_pw: tuple[np.ndarray, np.ndarray] | None = None
            while Rw_pw is None and time.time() < deadline:
                Rw_pw = tlp.read_pose(self.dev, self.source)
                if Rw_pw is None:
                    time.sleep(0.002)
            if Rw_pw is None:
                return
            Rw, pw = Rw_pw
        self._set_calibration(Rw, pw)

    def _auto_recalibrate(self, Rw: np.ndarray, pw: np.ndarray, tnow: float) -> None:
        """Monitors tracker stillness and triggers recalibration if needed.

        If the tracker's world pose (Rw, pw) remains within the linear and
        angular thresholds (still_lin_thresh, still_ang_thresh_rad) for
        still_time_sec, this method triggers recalibrate()
        using the current pose.

        This is "armed" and will only trigger once per still period.
        It re-arms after movement is detected.

        Args:
            Rw: The current world-space rotation matrix (3x3 np.ndarray).
            pw: The current world-space position vector (3-element np.ndarray).
            tnow: The current time (from time.time()).
        """
        if self._last_world_pw is None or self._last_world_Rw is None:
            self._last_world_pw = pw.copy()
            self._last_world_Rw = Rw.copy()
            self._last_motion_t = tnow
            self._auto_calib_armed = True
            return

        lin = float(np.linalg.norm(pw - self._last_world_pw))
        ang = float(tlp._angle_between_R(self._last_world_Rw, Rw))

        moved = (lin > self.still_lin_thresh) or (ang > self.still_ang_thresh_rad)
        if moved:
            self._last_motion_t = tnow
            self._auto_calib_armed = True

        # Update history every frame
        self._last_world_pw = pw.copy()
        self._last_world_Rw = Rw.copy()

        # Trigger once after still_time_sec
        if (
            self._auto_calib_armed
            and (tnow - self._last_motion_t) >= self.still_time_sec
        ):
            self.recalibrate(Rw, pw)  # use the *current* pose; non-blocking
            self._auto_calib_armed = False  # don't spam; re-arm after next movement

    # -------------------- main read --------------------

    def read(self) -> dict[str, Any]:
        """Reads the latest pose and button data from the tracker.

        This is the main data polling method. It performs several steps:
        1. Reads the current world pose (Rw, pw) from OpenVR.
        2. Feeds this pose into the _auto_recalibrate stillness detector.
        3. If not calibrated (_has_cal is False), returns a neutral pose.
        4. Calculates the local pose (Rloc, ploc) relative to (R0, p0).
        5. Remaps the local axes (x=forward, y=left, z=up).
        6. Converts the local rotation to a quaternion (w, x, y, z).
        7. Reads button states (if any).

        Returns:
            A dictionary containing the pose, button state, and metadata:
            {
                "pose": [px, py, pz, qw, qx, qy, qz],
                "event": { ... button states ... },
                "meta": {"id": str, "side": str, "t": float}
            }
        """
        # World pose
        Rw_pw = tlp.read_pose(self.dev, self.source)
        if Rw_pw is None:
            return {
                "pose": [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
                "event": {},
                "meta": {"id": self.name, "side": self.side, "t": time.time()},
            }

        tnow = time.time()
        Rw, pw = Rw_pw
        if self.reorthonormalize:
            Rw = tlp.orthonormalize(Rw)

        if self.reset_helper.key_pressed():
            self.recalibrate(Rw, pw)

        if not self._has_cal:
            # Not calibrated yet (e.g., first frames); return neutral pose
            return {
                "pose": [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
                "event": {},
                "meta": {"id": self.name, "side": self.side, "t": tnow},
            }

        # Local pose (relative to calibration)
        Rloc = self.R0.T @ Rw
        ploc = self.R0.T @ (pw - self.p0)

        # Axis remap (x=forward, y=left, z=up)
        S = np.array([[0, -1, 0], [-1, 0, 0], [0, 0, -1]], dtype=float)
        Rloc = S @ Rloc @ S.T
        ploc = S @ ploc

        # Quaternion (w, x, y, z)
        qw, qx, qy, qz = tlp.quat_wxyz_from_R(Rloc)

        # Best-effort button snapshot (often empty on trackers)
        try:
            buttons = self.dev.get_controller_inputs() or {}
        except Exception:
            buttons = {}

        return {
            "pose": [float(ploc[0]), float(ploc[1]), float(ploc[2]), qw, qx, qy, qz],
            "event": buttons,
            "meta": {"id": self.name, "side": self.side, "t": tnow},
        }

    def get_action(self):
        return self.read()
