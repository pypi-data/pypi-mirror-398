"""DClaw gripper model."""

from __future__ import annotations

from pathlib import Path

import torch

from dexsuite.core.components import GripperModel
from dexsuite.core.registry import register_gripper

ASSETS: Path = Path(__file__).parent / "assets"


@register_gripper("dclaw")
class Dclaw(GripperModel):
    """DClaw gripper model."""

    model_path: str = str(ASSETS / "dclaw_gripper_glb.urdf")
    dof: int = 9
    root_link: str = "base"
    home_q: torch.Tensor = torch.zeros((9,), dtype=torch.float32)
    tcp_pose: torch.Tensor = torch.tensor(
        [0.0, -0.035, 0.09, 0.0, 0.0, 0.0],
        dtype=torch.float32,
    )
