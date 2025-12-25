"""Link6 modular manipulator model.

This module registers a 6-DoF arm model defined in an MJCF file.
"""

from __future__ import annotations

from pathlib import Path

import torch

from dexsuite.core.components import ModularManipulatorModel
from dexsuite.core.registry import register_manipulator

HERE: Path = Path(__file__).parent
MODEL_PATH: Path = HERE / "link6_best.xml"


@register_manipulator("link6")
class Link6(ModularManipulatorModel):
    """Link6 arm (modular, no gripper)."""

    model_path: str = str(MODEL_PATH)
    dof: int = 6

    root_link: str = "base_link"
    end_link: str = "end_effector_link"
    home_q: torch.Tensor = torch.tensor(
        [0.0, 0.0, 1.571, 0.0, 0.0, 0.0],
        dtype=torch.float32,
    )
