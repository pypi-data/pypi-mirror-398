"""Global run-time constants shared across DexSuite.

This module defines global constants and accessor/mutator functions to manage
fundamental environment parameters like the default PyTorch device and the
number of parallel environments.

Only the DEVICE variable is public, everything else should import
get_device() rather than hard-coding “cuda:0”.
"""

from __future__ import annotations

import torch

# The global PyTorch device used for tensors and models throughout DexSuite.
# It initializes to CUDA if available, otherwise to CPU.
_DEVICE: torch.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# The global number of parallel environments/workers (e.g., in an RL setup).
_N_ENVS: int = 1


def set_device(device: str | torch.device) -> None:
    """Globally override the torch / Genesis device.

    Args:
        device: The new device to use (e.g., "cpu", "cuda:0", torch.device("cuda")).
    """
    global _DEVICE
    _DEVICE = torch.device(device)


def get_device() -> torch.device:
    """Return the global device used throughout DexSuite.

    Returns:
        The globally configured torch.device.
    """
    return _DEVICE


def set_n_envs(n: int) -> None:
    """Globally override the number of parallel environments.

    Args:
        n: The new number of environments. Must be a positive integer.
    """
    global _N_ENVS
    _N_ENVS = int(n)


def get_n_envs() -> int:
    """Return the global number of parallel environments.

    Returns:
        The globally configured integer number of environments.
    """
    return _N_ENVS
