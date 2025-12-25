"""Model definition for a robotic hand or parallel gripper."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Union

import torch

from dexsuite.core.components.base import RigidBodyModel

JointSel = Union[slice, Sequence[int]]


class GripperModel(RigidBodyModel):
    """A concrete description of a robotic hand or parallel gripper.

    Attributes:
        root_link: The name of the link where the gripper attaches to an arm.
        tcp_pose: The pose of the tool center point (TCP) relative to the
            root_link, if any.
        JOINT_MAP: A dictionary mapping logical finger names to their
            corresponding joint indices or slices.
        GRASP_TIPS: A list of link names considered to be grasp contact points.
        PINCH_PAIRS: A list of link name pairs used for pinch grasp helpers.
    """

    root_link: str
    tcp_pose: torch.Tensor | None = None
    JOINT_MAP: dict[str, JointSel] = {}

    GRASP_TIPS: Sequence[str] | None = None
    PINCH_PAIRS: Sequence[tuple[str, str]] | None = None

    def decompose_state(
        self,
        qpos: torch.Tensor,
        qvel: torch.Tensor,
        qtau: torch.Tensor,
    ) -> dict[str, dict[str, torch.Tensor]]:
        """Decomposes flat state tensors into a per-finger dictionary.

        This method uses the JOINT_MAP to split the gripper's full joint
        position, velocity, and torque tensors into a structured dictionary,
        making it easier to access the state of individual fingers. This is
        intended for observation processing, not action parsing.

        Args:
            qpos: A tensor of joint positions.
            qvel: A tensor of joint velocities.
            qtau: A tensor of joint torques/efforts.

        Returns:
            A nested dictionary where keys are finger names from JOINT_MAP and
            values are dictionaries containing qpos, qvel, and qtorque tensors
            for that finger. Returns an empty dictionary if JOINT_MAP is not
            defined.
        """
        if not self.JOINT_MAP:
            return {}
        out: dict[str, dict[str, torch.Tensor]] = {}
        for name, sel in self.JOINT_MAP.items():
            out[name] = {"qpos": qpos[sel], "qvel": qvel[sel], "qtorque": qtau[sel]}
        return out
