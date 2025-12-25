"""Franka Emika Panda model with an integrated 2F gripper.

This module provides a single, integrated manipulator model that includes both
the 7-DoF Panda arm and its 2-DoF parallel gripper in one MJCF file.
"""

from __future__ import annotations

from pathlib import Path

import torch

from dexsuite.core.components import IntegratedManipulatorModel
from dexsuite.core.registry import register_manipulator

ASSETS: Path = Path(__file__).parent / "assets"


@register_manipulator("franka_with_gripper")
class FrankaWithGripper(IntegratedManipulatorModel):
    """Franka Emika Panda manipulator with its built-in parallel gripper.

    Notes:
        - dof is the total DoF of the integrated entity (arm + gripper).
        - home_q is the arm-only home pose and matches control_dofs_index.
        - The gripper joints are expected to be the last DoFs of the entity.
        - builtin_gripper_tcp_pose, if provided, follows the DexSuite TCP anchor
          convention: [x, y, z, roll, pitch, yaw] (meters and radians) expressed
          in the builtin_gripper_root_link frame.
    """

    model_path: str = str(ASSETS / "panda.xml")
    dof: int = 9

    root_link: str = "link0"
    end_link: str = "link7"

    control_dofs_index: list[int] = [0, 1, 2, 3, 4, 5, 6]
    home_q: torch.Tensor = torch.tensor(
        [0.0, -0.785, 0.0, -2.356, 0.0, 1.571, -0.785],
        dtype=torch.float32,
    )
    builtin_gripper_dof: int = 2
    builtin_gripper_control_dofs_index: list[int] = [7, 8]
    builtin_gripper_root_link: str = "hand"
    builtin_gripper_q_lo: torch.Tensor = torch.tensor([0.0, 0.0], dtype=torch.float32)
    builtin_gripper_q_hi: torch.Tensor = torch.tensor(
        [0.04, 0.04],
        dtype=torch.float32,
    )
    builtin_gripper_home_q: torch.Tensor = torch.tensor(
        [0.04, 0.04],
        dtype=torch.float32,
    )
    builtin_gripper_grasp_tips: tuple[str, ...] = ("left_finger", "right_finger")
    builtin_gripper_pinch_pairs: tuple[tuple[str, str], ...] = (
        ("left_finger", "right_finger"),
    )
    builtin_gripper_tcp_pose: torch.Tensor | None = None
