"""LEAP Hand gripper models (left and right)."""

from __future__ import annotations

from pathlib import Path

import torch

from dexsuite.core.components import GripperModel
from dexsuite.core.registry import register_gripper

ASSETS: Path = Path(__file__).parent / "assets"


@register_gripper("leap_right")
@register_gripper("leap")
class LeapRight(GripperModel):
    """LEAP Hand (Right) gripper model."""

    model_path: str = str(ASSETS / "right_hand.xml")
    dof: int = 16
    root_link: str = "palm"
    tcp_pose: torch.Tensor = torch.tensor(
        [0.0, -0.035, 0.09, 0.0, 0.0, 0.0],
        dtype=torch.float32,
    )
    home_q: torch.Tensor = torch.zeros((16,), dtype=torch.float32)


@register_gripper("leap_left")
class LeapLeft(GripperModel):
    """LEAP Hand (Left) gripper model."""

    model_path: str = str(ASSETS / "left_hand.xml")
    dof: int = 16
    root_link: str = "palm"
    tcp_pose: torch.Tensor = torch.tensor(
        [0.0, -0.035, 0.09, 0.0, 0.0, 0.0],
        dtype=torch.float32,
    )
    home_q: torch.Tensor = torch.zeros((16,), dtype=torch.float32)
