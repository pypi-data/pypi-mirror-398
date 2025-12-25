"""Robotiq 2F-85 gripper model."""

from __future__ import annotations

from pathlib import Path

import torch

from dexsuite.core.components import GripperModel
from dexsuite.core.registry import register_gripper

ASSETS: Path = Path(__file__).parent / "assets"


@register_gripper("robotiq")
class Robotiq85(GripperModel):
    """Robotiq 2F-85 gripper model."""

    model_path: str = str(ASSETS / "2f85.xml")
    dof: int = 1

    root_link: str = "base"
    tcp_pose: torch.Tensor = torch.tensor(
        [0.0, 0.0, 0.16, 0.0, 0.0, 0.0],
        dtype=torch.float32,
    )

    q_lo: torch.Tensor = torch.tensor([0.0], dtype=torch.float32)
    q_hi: torch.Tensor = torch.tensor([0.85], dtype=torch.float32)
    home_q: torch.Tensor = torch.tensor([0.85], dtype=torch.float32)

    GRASP_TIPS: tuple[str, ...] = ("left_pad", "right_pad")
    PINCH_PAIRS: tuple[tuple[str, str], ...] = (("left_pad", "right_pad"),)
