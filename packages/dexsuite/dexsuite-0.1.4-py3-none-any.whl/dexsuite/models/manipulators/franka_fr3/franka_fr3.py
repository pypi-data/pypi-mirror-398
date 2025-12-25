"""Models for the Franka Emika FR3 manipulator."""

from __future__ import annotations

from pathlib import Path

import torch

from dexsuite.core.components import ModularManipulatorModel
from dexsuite.core.registry import register_manipulator

ASSETS: Path = Path(__file__).parent / "assets"


@register_manipulator("franka_fr3")
class FrankaFR3(ModularManipulatorModel):
    """Franka Emika FR3 arm (modular, no gripper)."""

    model_path: str = str(ASSETS / "fr3.xml")
    dof: int = 7
    root_link: str = "fr3_link0"
    end_link: str = "fr3_link7"
    home_q: torch.Tensor = torch.tensor(
        [0.0, 0.0, 0.0, -1.57079, 0.0, 1.57079, -0.7853],
        dtype=torch.float32,
    )
