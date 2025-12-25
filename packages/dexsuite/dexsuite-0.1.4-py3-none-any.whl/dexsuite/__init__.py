from __future__ import annotations

import importlib
import pkgutil

__version__ = "0.1.4"
# ----------------------------------------------------------------------
# public surface (core functions)
# ----------------------------------------------------------------------
from .api import make  # re-export

# ----------------------------------------------------------------------
# public surface (configuration options)
# These are imported from the subpackage to be available directly under dexsuite.
# ----------------------------------------------------------------------
from .options import (
    AABBOptions,
    ArmOptions,
    CamerasOptions,
    ControllerOptions,
    DynamicCamOptions,
    EnvOptions,
    LayoutOptions,
    PoseOptions,
    RobotOptions,
    SimOptions,
    StaticCamOptions,
)
from .utils import get_device, set_device

__all__ = [
    # Core Exports
    "make",
    "set_device",
    "get_device",
    # Options Exports
    "CamerasOptions",
    "StaticCamOptions",
    "DynamicCamOptions",
    "EnvOptions",
    "LayoutOptions",
    "PoseOptions",
    "RobotOptions",
    "AABBOptions",
    "ArmOptions",
    "ControllerOptions",
    "SimOptions",
]


# ----------------------------------------------------------------------
# auto-import sub-packages so that the registries are populated
# ----------------------------------------------------------------------
def _autoimport(pkg_name: str) -> None:
    """Recursively imports all submodules under a given package name."""
    pkg = importlib.import_module(pkg_name)
    for mod in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."):
        importlib.import_module(mod.name)


_autoimport(__name__ + ".models")
_autoimport(__name__ + ".environments")
