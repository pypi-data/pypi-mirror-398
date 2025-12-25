from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from dexsuite.utils import extract_grippermount_yaml

_HERE = Path(__file__).parent


def _load_yaml(name: str) -> dict:
    p = _HERE / name
    if not p.exists():
        return {}
    return extract_grippermount_yaml(p)


def load_workspaces() -> dict[str, dict[str, list[float]]]:
    """Schema:
    workspaces:
      franka:
        min: [x,y,z]   # relative to arm base
        max: [x,y,z]
      franka_with_gripper:
        min: [...]
        max: [...].
    """
    data = _load_yaml("workspaces.yaml")
    w = data.get("workspaces", {})
    out: dict[str, dict[str, list[float]]] = {}
    for k, v in w.items():
        if isinstance(v, dict) and "min" in v and "max" in v:
            out[k] = {
                "min": list(map(float, v["min"])),
                "max": list(map(float, v["max"])),
            }
    return out
