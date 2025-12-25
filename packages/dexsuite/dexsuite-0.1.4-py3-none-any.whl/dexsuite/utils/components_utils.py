"""Utilities for component models."""

from __future__ import annotations

from pathlib import Path

import yaml


def extract_grippermount_yaml(path: Path) -> dict:
    """Loads an adapter or gripper-mount configuration YAML file.

    This utility loads the YAML and returns the raw data. It is intended for
    configuration files where fields like positional and rotational vectors
    are represented as lists.

    Args:
        path: The absolute or relative path to the YAML configuration file.

    Returns:
        dict: A dictionary containing the parsed YAML data. Pose vectors
        are returned as lists.

    Raises:
        FileNotFoundError: If the file specified by path does not exist.
        yaml.YAMLError: If the file contains invalid YAML syntax.
    """
    with open(path) as f:
        data = yaml.safe_load(f) or {}

    # We no longer convert to numpy here. We return the raw lists.
    # The GripperMount.__init__ is responsible for converting these
    # lists to torch.Tensors on the correct device.
    return data
