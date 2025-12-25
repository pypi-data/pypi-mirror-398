"""Models for the SO-100 manipulator."""

from __future__ import annotations

from pathlib import Path

import torch

from dexsuite.core.components import IntegratedManipulatorModel
from dexsuite.core.registry import register_manipulator

ASSETS = Path(__file__).parent / "assets"


@register_manipulator("so_100")
class SO100(IntegratedManipulatorModel):
    """SO Arm 100 with rotary single-jaw gripper."""

    model_path: str = str(ASSETS / "so_arm100.xml")
    dof: int = 6

    control_dofs_index: list[int] = [0, 1, 2, 3, 4]

    root_link: str = "Base"

    end_link: str = "Moving_Jaw"

    home_q: torch.Tensor = torch.tensor(
        [0.0, -1.57, 1.57, 1.57, -1.57],
        dtype=torch.float32,
    )

    builtin_gripper_dof: int = 1

    builtin_gripper_control_dofs_index: list[int] = [5]
    builtin_gripper_root_link: str = "Fixed_Jaw"

    builtin_gripper_q_lo: torch.Tensor = torch.tensor([-0.174], dtype=torch.float32)
    builtin_gripper_q_hi: torch.Tensor = torch.tensor([1.75], dtype=torch.float32)
    builtin_gripper_home_q: torch.Tensor = torch.tensor([1.75], dtype=torch.float32)
    builtin_gripper_tcp_pose: torch.Tensor = torch.tensor(
        [0.012, -0.08, 0.0, 0.0, 0.0, 0.0],
        dtype=torch.float32,
    )
