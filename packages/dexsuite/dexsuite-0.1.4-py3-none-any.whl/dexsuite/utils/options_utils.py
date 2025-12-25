"""Utilities for loading and managing configuration files and layout presets."""

from __future__ import annotations

from pathlib import Path

import yaml
from cattrs import GenConverter

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

# The absolute path to the 'config' directory, calculated relative to this file.
_CONFIG_ROOT = (Path(__file__).resolve().parents[1] / "config").resolve()


def load_defaults(file: str) -> dict:
    """Loads a default environment configuration file.

    Args:
        file: The basename of the YAML file (without .yaml) to load
        from the 'env_configs' directory.

    Returns:
        The configuration dictionary loaded from the YAML file.
        Returns an empty dictionary if the file is empty.

    Raises:
        FileNotFoundError: If the specified config file does not exist.
        yaml.YAMLError: If the file is a malformed YAML.
    """
    config_path = _CONFIG_ROOT / "env_configs" / f"{file}.yaml"

    try:
        with open(config_path) as f:
            data = yaml.safe_load(f)
            # Ensure an empty file returns an empty dict rather than None
            return data if data else {}
    except FileNotFoundError as err:
        raise FileNotFoundError(
            f"Default config file not found at {config_path}",
        ) from err
    except Exception as e:
        raise Exception(f"Error loading YAML from {config_path}: {e}") from e


def load_layout_preset(model: str) -> dict:
    """Loads a layout preset from the 'presets' directory.

    This function attempts to load the YAML file matching the model name.
    If the specified model file does not exist, is empty, or contains a
    'name' key that does not match the model name, it will fall back
    and load the 'defaults.yaml' preset instead.

    Args:
        model: The name of the model preset to load (e.g., "franka").
        This corresponds to the YAML filename.

    Returns:
        The layout preset dictionary.

    Raises:
        FileNotFoundError: If the 'defaults.yaml' preset file itself
            is missing, as it's the required fallback.
        ValueError: If the 'defaults.yaml' file is empty or invalid.
        yaml.YAMLError: If any YAML file fails to parse.
    """
    preset_path = _CONFIG_ROOT / "presets" / f"{model}.yaml"

    if not preset_path.exists():
        if model == "defaults":
            # Critical error: The fallback 'defaults.yaml' is missing.
            raise FileNotFoundError(
                f"The 'defaults' preset file cannot be found at: {preset_path}",
            )
        # The requested model file is missing, fall back to defaults.
        return load_layout_preset("defaults")

    try:
        with open(preset_path) as f:
            layout = yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading preset YAML from {preset_path}: {e}")
        if model == "defaults":
            # If 'defaults' itself fails to load, we cannot recover.
            raise ValueError(f"Failed to load 'defaults' preset: {e}") from e
        # Any other failed load should fall back to defaults.
        return load_layout_preset("defaults")

    # Check for empty files (which load as None) or invalid YAML.
    is_valid_dict = isinstance(layout, dict)

    if model == "defaults":
        if not is_valid_dict:
            raise ValueError(
                f"The 'defaults' preset file is invalid or empty: {preset_path}",
            )
        return layout

    # For a specific model: fall back if the file was empty
    # or the 'name' key doesn't match.
    if not is_valid_dict or layout.get("name") != model:
        return load_layout_preset("defaults")

    return layout


def _read_workspaces_yaml() -> dict[str, dict]:
    """Loads and parses the 'workspaces.yaml' config file.

    This function reads 'dexsuite/config/workspaces.yaml' and returns
    the core manipulator-to-AABB (Axis-Aligned Bounding Box) mapping.
    It's flexible and accepts the mapping at the top level of the YAML
    or nested under a 'workspaces' key.

    Returns:
        A dictionary mapping manipulator names (str) to their
        workspace definitions (dict).

    Example:
            {
                'manip_name': {'min': [x,y,z], 'max': [x,y,z]},
                ...
            }

    Raises:
        FileNotFoundError: If 'workspaces.yaml' is not found at the expected path.
        ValueError: If the file is not a valid YAML mapping, is empty,
                    or has an incorrect structure (e.g., no 'workspaces'
                    key and no top-level mapping).
        yaml.YAMLError: If the file is malformed and cannot be parsed.
    """
    config_path = _CONFIG_ROOT / "workspaces.yaml"

    try:
        with open(config_path) as f:
            data = yaml.safe_load(f)
    except FileNotFoundError as err:
        raise FileNotFoundError(
            f"workspaces.yaml not found at {config_path}. "
            "Define per-manipulator AABBs there.",
        ) from err
    except Exception as e:
        raise ValueError(f"Error loading or parsing {config_path}: {e}") from e

    if not isinstance(data, dict):
        raise ValueError(f"{config_path} must be a mapping.")

    w = data.get("workspaces", data)
    if not isinstance(w, dict) or not w:
        raise ValueError(
            f"{config_path} must define a non-empty 'workspaces' mapping "
            "or a top-level mapping of {manip: {min,max}}.",
        )
    return w


def resolve_workspace_strict(manip_name: str) -> dict:
    """Finds and validates the workspace for a specific manipulator.

    This performs a strict, exact-match lookup in the 'workspaces.yaml'
    file. No fallbacks are used. If the manipulator is not found or
    its definition is invalid, this function will raise an error.

    Args:
        manip_name: The name of the manipulator to look up (e.g.,
                    "franka").

    Returns:
        A dictionary containing the validated workspace AABB, with
        'min' and 'max' keys mapping to 3-element float lists.

    Example:
            {'min': [0.1, 0.2, 0.3], 'max': [0.4, 0.5, 0.6]}

    Raises:
        FileNotFoundError: If 'workspaces.yaml' cannot be found
        (raised by _read_workspaces_yaml).
        ValueError: If the manipulator manip_name is not found in the
                    file, or if its entry is malformed (e.g., missing
                    'min'/'max' keys, non-numeric values, lists are
                    not length 3, or any min value > max value).
        yaml.YAMLError: If 'workspaces.yaml' is malformed
                        (raised by _read_workspaces_yaml).
    """
    wmap = _read_workspaces_yaml()
    if manip_name not in wmap:
        raise ValueError(
            f"No workspace AABB specified for manipulator '{manip_name}' "
            "in workspaces.yaml.",
        )

    spec = wmap[manip_name]
    if not (isinstance(spec, dict) and "min" in spec and "max" in spec):
        raise ValueError(
            f"workspaces.yaml: entry '{manip_name}' must be a dict "
            "with 'min' and 'max' keys.",
        )

    try:
        mn = list(map(float, spec["min"]))
        mx = list(map(float, spec["max"]))
    except (TypeError, ValueError) as e:
        # Catches errors if spec["min"] is not a list or elements are not numbers
        raise ValueError(
            f"workspaces.yaml: entry '{manip_name}' min/max values "
            "must be lists of numbers.",
        ) from e

    if len(mn) != 3 or len(mx) != 3:
        raise ValueError(
            f"workspaces.yaml: entry '{manip_name}' min/max must be 3-length lists.",
        )
    if any(lo > hi for lo, hi in zip(mn, mx, strict=False)):
        raise ValueError(f"workspaces.yaml: entry '{manip_name}' has min[i] > max[i].")

    return {"min": mn, "max": mx}


def get_ds_converter() -> GenConverter:
    """Creates and returns a GenConverter instance with custom hooks.

    This function configures a GenConverter to handle specific data types,
    such as tuples and dictionaries, for serialization and deserialization.

    Returns:
        GenConverter: A configured instance of GenConverter.
    """
    c = GenConverter()
    # Tuples (Vec3, Quat, ResHW, modalities) <-> JSON lists
    c.register_unstructure_hook(tuple, lambda v: list(v))
    c.register_structure_hook(tuple, lambda v, _: tuple(v))
    # Allow dict[str, object] used in LayoutOptions.params
    c.register_structure_hook(object, lambda v, _: v)
    return c
