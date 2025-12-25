"""Shadow Hand gripper models (left and right)."""

from __future__ import annotations

from pathlib import Path

import torch

from dexsuite.core.components import GripperModel
from dexsuite.core.registry import register_gripper

ASSETS: Path = Path(__file__).parent / "assets"


@register_gripper("shadow_right")
@register_gripper("shadow")
class ShadowRight(GripperModel):
    """Shadow Hand (Right) gripper model."""

    model_path: str = str(ASSETS / "right_hand.xml")
    dof: int = 24
    root_link: str = "rh_forearm"
    tcp_pose: torch.Tensor = torch.tensor(
        [0.07, 0.01, 0.285, 0.0, 0.0, 0.0],
        dtype=torch.float32,
    )

    home_q: torch.Tensor = torch.tensor(
        [
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
        ],
        dtype=torch.float32,
    )

    q_hi: torch.Tensor = torch.tensor(
        [
            0.0,
            0.0,
            0.15,
            1.00,
            0.25,
            0.80,
            0.70,
            0.0,
            1.20,
            2.5,
            0.0,
            1.20,
            2.5,
            0.0,
            1.20,
            2.5,
            0.0,
            0.0,
            1.20,
            2.5,
            0.0,
            0.0,
            1.20,
            2.5,
        ],
        dtype=torch.float32,
    )

    q_lo: torch.Tensor = torch.tensor(
        [
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
        ],
        dtype=torch.float32,
    )


@register_gripper("shadow_left")
class ShadowLeft(GripperModel):
    """Shadow Hand (Left) gripper model."""

    model_path: str = str(ASSETS / "left_hand.xml")
    dof: int = 20
    root_link: str = "lh_forearm"
    home_q: torch.Tensor = torch.zeros((20,), dtype=torch.float32)
    tcp_pose: torch.Tensor = torch.tensor(
        [0.0, -0.035, 0.09, 0.0, 0.0, 0.0],
        dtype=torch.float32,
    )
