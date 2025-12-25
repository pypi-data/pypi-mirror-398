"""Schunk SVH hand gripper model."""

from __future__ import annotations

from pathlib import Path

import torch

from dexsuite.core.components import GripperModel
from dexsuite.core.registry import register_gripper

ASSETS: Path = Path(__file__).parent / "assets"


@register_gripper("schunk")
class Schunk(GripperModel):
    """Schunk SVH Hand (Right) gripper model."""

    model_path: str = str(ASSETS / "schunk_svh_hand_right.urdf")
    dof: int = 9
    root_link: str = "base_link"
    home_q: torch.Tensor = torch.zeros((9,), dtype=torch.float32)
    tcp_pose: torch.Tensor = torch.tensor(
        [0.0, -0.035, 0.09, 0.0, 0.0, 0.0],
        dtype=torch.float32,
    )
    control_dofs_index: list[int] = [1, 3, 5, 6, 7, 8, 9, 10, 12]
