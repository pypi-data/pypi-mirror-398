"""Abstract base class for arm and gripper component models."""

from __future__ import annotations

from abc import ABC
from collections.abc import Sequence

import torch

from dexsuite.utils import get_device


class RigidBodyModel(ABC):
    """Abstract base class for arm and gripper component models.

    Attributes:
        model_path: The path to the component's model file (e.g., MJCF).
        dof: The number of degrees of freedom for the component.
        device: The torch device (e.g., 'cuda' or 'cpu') for tensors.
        kp: Proportional gains for the controller.
        kv: Derivative gains for the controller.
        force_range: Effort limits for the actuators.
        q_lo: Lower joint limits.
        q_hi: Upper joint limits.
    """

    model_path: str
    dof: int
    control_dofs_index: list[int] | None = None
    kp: float | Sequence[float] | torch.Tensor | None = None
    kv: float | Sequence[float] | torch.Tensor | None = None
    force_range: float | Sequence[float] | torch.Tensor | None = None
    q_lo: float | Sequence[float] | torch.Tensor | None = None
    q_hi: float | Sequence[float] | torch.Tensor | None = None

    def __init__(self) -> None:
        """Initialize the RigidBodyModel.

        This constructor validates that required class attributes are defined
        and broadcasts any scalar controller properties (e.g., kp, kv) to
        torch.Tensors matching the component's degrees of freedom.

        Raises:
            NotImplementedError: If model_path or dof are not defined in the subclass.
        """
        if self.model_path is None or self.dof is None:
            raise NotImplementedError("model_path and dof must be defined")

        self.device = get_device()

        self.kp = self._process_param(self.kp, self.dof, self.device, "kp")
        self.kv = self._process_param(self.kv, self.dof, self.device, "kv")
        self.force_range = self._process_param(
            self.force_range,
            self.dof,
            self.device,
            "force_range",
        )
        self.q_lo = self._process_param(self.q_lo, self.dof, self.device, "q_lo")
        self.q_hi = self._process_param(self.q_hi, self.dof, self.device, "q_hi")

    def _process_param(
        self,
        value: float | Sequence[float] | torch.Tensor | None,
        size: int,
        device: torch.device,
        name: str,
    ) -> torch.Tensor | None:
        """Helper to convert/broadcast a parameter to a torch.Tensor."""
        if value is None:
            return None

        if isinstance(value, torch.Tensor):
            t = value.to(device)
        elif isinstance(value, (float, int)):
            t = torch.full((size,), float(value), device=device, dtype=torch.float32)
        elif isinstance(value, Sequence):
            t = torch.tensor(value, device=device, dtype=torch.float32)
        else:
            raise TypeError(f"Unsupported type for {name}: {type(value)}")

        if t.numel() == 1 and size > 1:
            return t.expand(size)
        if t.shape != (size,):
            raise ValueError(
                f"{name} has wrong shape. Expected ({size},) or scalar, "
                f"but got {t.shape}",
            )
        return t

    def default_qpos(self) -> torch.Tensor:
        """Return the default joint configuration for the component.

        By default, this returns a zero vector on the component's device.
        Subclasses may override this method to provide a more specific
        default pose (e.g., a 'home' position).

        Returns:
            A torch.Tensor of shape (dof,) representing the default joint
            positions.
        """
        return torch.zeros(self.dof, device=self.device, dtype=torch.float32)
