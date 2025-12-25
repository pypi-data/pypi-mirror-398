"""User-facing simulation configuration options."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SimOptions:
    """User-configurable simulation parameters.

    Attributes:
        control_hz: The frequency (in Hz) at which control actions are applied.
        performance_mode: A flag to enable or disable performance-optimizing
            settings within the simulation.
    """

    control_hz: int = 20
    performance_mode: bool = False
    n_envs: int = 1

    def __post_init__(self) -> None:
        """Validate the control frequency."""
        if self.control_hz <= 0:
            raise ValueError("Sim.control_hz must be a positive integer.")
        if self.n_envs <= 0:
            raise ValueError("Sim.n_envs must be >= 1.")
