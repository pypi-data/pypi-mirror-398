"""Models for the Kuka LBR iiwa 14 manipulator."""

from __future__ import annotations

from pathlib import Path

import torch

from dexsuite.core.components import ModularManipulatorModel
from dexsuite.core.registry import register_manipulator

ASSETS: Path = Path(__file__).parent / "assets"


@register_manipulator("kuka")
class Kuka(ModularManipulatorModel):
    """Kuka LBR iiwa 14 arm (modular, no gripper)."""

    model_path: str = str(ASSETS / "iiwa14.xml")
    dof: int = 7
    root_link: str = "base"
    end_link: str = "link7"
    home_q: torch.Tensor = torch.tensor(
        [0.0, 0.785398, 0.0, -1.5708, 0.0, 0.0, 0.0],
        dtype=torch.float32,
    )
