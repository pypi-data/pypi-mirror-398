"""Models for the Kinova Gen3 manipulator."""

from __future__ import annotations

from pathlib import Path

import torch

from dexsuite.core.components import ModularManipulatorModel
from dexsuite.core.registry import register_manipulator

ASSETS: Path = Path(__file__).parent / "assets"


@register_manipulator("gen3")
class Gen3(ModularManipulatorModel):
    """Kinova Gen3 arm (modular, no gripper)."""

    model_path: str = str(ASSETS / "gen3.xml")
    dof: int = 7
    root_link: str = "base_link"
    end_link: str = "bracelet_link"
    home_q: torch.Tensor = torch.tensor(
        [0.0, 0.0, 0.0, 1.5708, 0.0, 1.5708, -1.5708],
        dtype=torch.float32,
    )
