"""Models for the Trossen WX250S manipulator."""

from __future__ import annotations

from pathlib import Path

import torch

from dexsuite.core.components import IntegratedManipulatorModel
from dexsuite.core.registry import register_manipulator

ASSETS = Path(__file__).parent / "assets"


@register_manipulator("trossen_wx250s")
class TrossenWX250S(IntegratedManipulatorModel):
    """Trossen WX250S manipulator with integrated gripper."""

    model_path: str = str(ASSETS / "wx250s.xml")
    dof: int = 7
    root_link: str = "wx250s/base_link"
    end_link: str = "wx250s/gripper_link"
    home_q: torch.Tensor = torch.tensor(
        [0.0, -0.96, 1.16, 0.0, -0.3, 0.0],
        dtype=torch.float32,
    )
    control_dofs_index: list[int] = [0, 1, 2, 3, 4, 5]
    builtin_gripper_dof: int = 1
    builtin_gripper_control_dofs_index: list[int] = [6]
    builtin_gripper_root_link: str = "wx250s/gripper_link"
    builtin_gripper_q_lo: torch.Tensor = torch.tensor([0.015], dtype=torch.float32)
    builtin_gripper_q_hi: torch.Tensor = torch.tensor([0.037], dtype=torch.float32)
    builtin_gripper_home_q: torch.Tensor = torch.tensor([0.015], dtype=torch.float32)
    builtin_gripper_tcp_pose: torch.Tensor | None = None
