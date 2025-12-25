"""Models for the Trossen VX300S manipulator."""

from __future__ import annotations

from pathlib import Path

import torch

from dexsuite.core.components import IntegratedManipulatorModel
from dexsuite.core.registry import register_manipulator

ASSETS = Path(__file__).parent / "assets"


@register_manipulator("trossen_vx300s")
class TrossenVX300S(IntegratedManipulatorModel):
    """Trossen VX300S manipulator with integrated gripper."""

    model_path: str = str(ASSETS / "vx300s.xml")

    # Total DoF is arm + gripper. The arm has 6 rotary joints.
    dof: int = 7

    root_link: str = "base_link"
    end_link: str = "gripper_link"

    home_q: torch.Tensor = torch.tensor(
        [0.0, -0.96, 1.16, 0.0, -0.3, 0.0],
        dtype=torch.float32,
    )

    control_dofs_index: list[int] = [0, 1, 2, 3, 4, 5]

    builtin_gripper_dof: int = 1

    builtin_gripper_control_dofs_index: list[int] = [6]

    builtin_gripper_root_link: str = "gripper_link"
    builtin_gripper_home_q: torch.Tensor = torch.tensor([0.021], dtype=torch.float32)
    builtin_gripper_q_lo: torch.Tensor = torch.tensor([0.021], dtype=torch.float32)
    builtin_gripper_q_hi: torch.Tensor = torch.tensor([0.057], dtype=torch.float32)
    builtin_gripper_tcp_pose: torch.Tensor = torch.tensor(
        [0.10, 0.0, 0.0, 0.0, 0.0, 0.0],
        dtype=torch.float32,
    )
