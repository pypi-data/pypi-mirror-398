"""Input device backends for teleoperation and data collection.

This package contains optional device readers (keyboard, SpaceMouse, Vive, ...).
Some backends depend on extra third-party packages and system drivers:

- Keyboard: pynput
- SpaceMouse:
  - Linux: evdev
  - macOS / Windows: hid (HIDAPI wrapper, see dexsuite[spacemouse])
- Vive: openvr (SteamVR)
- Manus: websockets

Importing dexsuite.devices itself does not require these extras; modules are
imported lazily when you access their classes.
"""

from __future__ import annotations

import importlib
from typing import Any

from .device import Device

__all__ = ["Device", "Keyboard", "Spacemouse", "ViveController", "ViveTracker"]

_LAZY: dict[str, str] = {
    "Keyboard": f"{__name__}.keyboard",
    "Spacemouse": f"{__name__}.spacemouse",
    "ViveController": f"{__name__}.vive_controller",
    "ViveTracker": f"{__name__}.vive_tracker",
}


def __getattr__(name: str) -> Any:  # pragma: no cover
    mod_name = _LAZY.get(name)
    if mod_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    mod = importlib.import_module(mod_name)
    value = getattr(mod, name)
    globals()[name] = value  # cache for subsequent lookups
    return value


def __dir__() -> list[str]:  # pragma: no cover
    return sorted(list(globals().keys()) + list(_LAZY.keys()))
