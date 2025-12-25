"""Models for the Franka Emika Panda manipulator (arm only)."""

from __future__ import annotations

from pathlib import Path

import torch

from dexsuite.core.components import ModularManipulatorModel
from dexsuite.core.registry import register_manipulator

ASSETS: Path = Path(__file__).parent / "assets"


@register_manipulator("franka")
class FrankaArm(ModularManipulatorModel):
    """Franka Emika Panda arm (modular, no gripper)."""

    model_path: str = str(ASSETS / "panda_nohand.xml")
    dof: int = 7

    root_link: str = "link0"
    end_link: str = "attachment"

    home_q: torch.Tensor = torch.tensor(
        [0.0, -0.785, 0.0, -2.356, 0.0, 1.571, -0.785],
        dtype=torch.float32,
    )
