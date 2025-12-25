"""Models for the Universal Robots UR10e manipulator."""

from __future__ import annotations

from pathlib import Path

import torch

from dexsuite.core.components import ModularManipulatorModel
from dexsuite.core.registry import register_manipulator

ASSETS: Path = Path(__file__).parent / "assets"


@register_manipulator("ur10")
class Ur10(ModularManipulatorModel):
    """UR10e arm only (no built-in gripper)."""

    model_path: str = str(ASSETS / "ur10e.xml")
    dof: int = 6

    root_link: str = "base"
    end_link: str = "wrist_3_link"

    home_q: torch.Tensor = torch.tensor(
        [0, -1.5708, -1.5708, -1.5708, 1.5708, 0.0],
        dtype=torch.float32,
    )
