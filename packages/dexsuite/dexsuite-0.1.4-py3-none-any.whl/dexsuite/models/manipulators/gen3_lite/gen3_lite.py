"""Models for the Kinova Gen3 Lite manipulator."""

from __future__ import annotations

from pathlib import Path

import torch

from dexsuite.core.components import IntegratedManipulatorModel
from dexsuite.core.registry import register_manipulator

ASSETS = Path(__file__).parent / "assets"


@register_manipulator("gen3_lite")
class Gen3Lite(IntegratedManipulatorModel):
    """Kinova Gen3 Lite manipulator with integrated gripper."""

    model_path: str = str(ASSETS / "gen3_lite.xml")
    dof: int = 7
    root_link: str = "base_link"
    end_link: str = "gripper_base_link"
    control_dofs_index: list[int] = [0, 1, 2, 3, 4, 5]
    home_q: torch.Tensor = torch.tensor(
        [
            0.0,
            0.0,
            1.5708,
            1.5708,
            1.5708,
            1.5708,
        ],
        dtype=torch.float32,
    )
    builtin_gripper_dof: int = 1
    builtin_gripper_control_dofs_index: list[int] = [6]
    builtin_gripper_home_q: torch.Tensor = torch.tensor([0.0], dtype=torch.float32)
    builtin_gripper_root_link: str = "gripper_base_link"
    builtin_gripper_tcp_pose: torch.Tensor | None = None
