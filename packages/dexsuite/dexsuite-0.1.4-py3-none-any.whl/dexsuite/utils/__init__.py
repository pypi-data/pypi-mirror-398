"""Shared utility helpers for DexSuite.

This package keeps common helpers in one place and re-exports a small,
stable surface area (device globals, randomizers, and a few math utilities).
"""

from __future__ import annotations

from .components_utils import extract_grippermount_yaml
from .globals import get_device, get_n_envs, set_device, set_n_envs
from .models_utils import get_object_path, get_texture_paths
from .orientation_utils import quat_to_rpy, rpy_to_quat
from .randomizers import (
    ThreeDPosRandomizer,
    TwoDPosRandomizer,
    YawRandomizer,
    dict_to_space,
    sampler_in_aabb,
)


def get_robot_morph(*args, **kwargs):
    """Lazy import wrapper for dexsuite.utils.robot_utils.get_robot_morph.

    Importing dexsuite.utils should stay lightweight; Genesis is only needed when
    robot morphs are actually constructed.
    """
    from .robot_utils import get_robot_morph as _get_robot_morph

    return _get_robot_morph(*args, **kwargs)


__all__ = [
    "ThreeDPosRandomizer",
    "TwoDPosRandomizer",
    "YawRandomizer",
    "dict_to_space",
    "extract_grippermount_yaml",
    "get_device",
    "get_n_envs",
    "get_object_path",
    "get_robot_morph",
    "get_texture_paths",
    "quat_to_rpy",
    "rpy_to_quat",
    "sampler_in_aabb",
    "set_device",
    "set_n_envs",
]
