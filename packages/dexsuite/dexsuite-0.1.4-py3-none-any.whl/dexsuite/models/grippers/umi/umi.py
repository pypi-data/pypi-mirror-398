"""Umi gripper model."""

from __future__ import annotations

from pathlib import Path

import torch

from dexsuite.core.components import GripperModel
from dexsuite.core.registry import register_gripper

ASSETS: Path = Path(__file__).parent / "assets"


@register_gripper("umi")
class Umi(GripperModel):
    """Umi gripper model."""

    model_path: str = str(ASSETS / "umi_gripper.xml")
    dof: int = 1
    root_link: str = "umi"

    kp: torch.Tensor = torch.tensor([500.0], dtype=torch.float32)
    home_q: torch.Tensor = torch.zeros((1,), dtype=torch.float32)
    tcp_pose: torch.Tensor = torch.tensor(
        [0.0, -0.035, 0.09, 0.0, 0.0, 0.0],
        dtype=torch.float32,
    )
