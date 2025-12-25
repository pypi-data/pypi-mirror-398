"""BarrettHand gripper model."""

from __future__ import annotations

from pathlib import Path

import torch

from dexsuite.core.components import GripperModel
from dexsuite.core.registry import register_gripper

ASSETS: Path = Path(__file__).parent / "assets"


@register_gripper("barrett")
class Barrett(GripperModel):
    """BarrettHand gripper model."""

    model_path: str = str(ASSETS / "bhand_model.urdf")
    dof: int = 8
    root_link: str = "base_link"
    home_q: torch.Tensor = torch.zeros((8,), dtype=torch.float32)
    tcp_pose: torch.Tensor = torch.tensor(
        [0.0, -0.035, 0.09, 0.0, 0.0, 0.0],
        dtype=torch.float32,
    )
