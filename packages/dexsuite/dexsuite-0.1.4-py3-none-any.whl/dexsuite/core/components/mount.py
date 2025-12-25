"""Defines a mount for attaching a gripper to a robotic arm."""

from __future__ import annotations

from collections.abc import Sequence

import torch

from dexsuite.utils import get_device


class GripperMount:
    """Represents the pose and geometry of an arm-to-gripper adapter.

    Attributes:
        mount_type: A string identifier for the mount type (e.g., 'invisible').
        mount_pos: The position of the mount relative to the arm's flange.
        mount_quat: The orientation (quaternion) of the mount relative to the
            arm's flange.
        geometry: A dictionary describing the visual or collision geometry of
            the mount.
        gripper_pos: The position of the gripper's root relative to the mount.
        gripper_quat: The orientation (quaternion) of the gripper's root
            relative to the mount.
        device: The torch device (e.g., 'cuda' or 'cpu') for tensors.
    """

    def __init__(
        self,
        mount_type: str = "invisible",
        mount_pos: Sequence[float] | torch.Tensor = (0.0, 0.0, 0.0),
        mount_quat: Sequence[float] | torch.Tensor = (0.0, 0.0, 0.0, 1.0),
        geometry: dict | None = None,
        gripper_pos: Sequence[float] | torch.Tensor = (0.0, 0.0, 0.0),
        gripper_quat: Sequence[float] | torch.Tensor = (0.0, 0.0, 0.0, 1.0),
    ):
        """Initialize the GripperMount.

        Args:
            mount_type: A string identifier for the mount type. Defaults to
                'invisible'.
            mount_pos: The [x, y, z] position of the mount relative to the
                arm's flange. Defaults to (0, 0, 0).
            mount_quat: The [x, y, z, w] orientation of the mount relative to
                the arm's flange. Defaults to (0, 0, 0, 1).
            geometry: An optional dictionary describing the mount's geometry.
                Defaults to None.
            gripper_pos: The [x, y, z] position of the gripper's root relative
                to the mount. Defaults to (0, 0, 0).
            gripper_quat: The [x, y, z, w] orientation of the gripper's root
                relative to the mount. Defaults to (0, 0, 0, 1).
        """
        self.device = get_device()
        self.mount_type = mount_type
        self.mount_pos = torch.tensor(
            mount_pos,
            device=self.device,
            dtype=torch.float32,
        )
        self.mount_quat = torch.tensor(
            mount_quat,
            device=self.device,
            dtype=torch.float32,
        )
        self.geometry = geometry or {}

        self.gripper_pos = torch.tensor(
            gripper_pos,
            device=self.device,
            dtype=torch.float32,
        )
        self.gripper_quat = torch.tensor(
            gripper_quat,
            device=self.device,
            dtype=torch.float32,
        )
