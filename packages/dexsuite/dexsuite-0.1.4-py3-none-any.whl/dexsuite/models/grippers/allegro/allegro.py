"""Allegro Hand gripper models (left and right)."""

from __future__ import annotations

from pathlib import Path

import torch

from dexsuite.core.components import GripperModel
from dexsuite.core.registry import register_gripper

ASSETS: Path = Path(__file__).parent / "assets"


class _AllegroBase(GripperModel):
    """Common Allegro hand settings."""

    dof: int = 16
    root_link: str = "palm"
    tcp_pose: torch.Tensor = torch.tensor(
        [-0.04, 0.0, 0.02, 0.0, torch.pi, torch.pi / 2],
        dtype=torch.float32,
    )

    GRASP_TIPS: tuple[str, ...] = ("ff_tip", "mf_tip", "rf_tip", "th_tip")
    PINCH_PAIRS: tuple[tuple[str, str], ...] = (
        ("ff_tip", "th_tip"),
        ("mf_tip", "th_tip"),
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
        ],
        dtype=torch.float32,
    )


@register_gripper("allegro_right")
@register_gripper("allegro")
class AllegroRight(_AllegroBase):
    """Allegro Hand (Right) gripper model."""

    model_path = str(ASSETS / "right_hand.xml")


@register_gripper("allegro_left")
class AllegroLeft(_AllegroBase):
    """Allegro Hand (Left) gripper model."""

    model_path = str(ASSETS / "left_hand.xml")
