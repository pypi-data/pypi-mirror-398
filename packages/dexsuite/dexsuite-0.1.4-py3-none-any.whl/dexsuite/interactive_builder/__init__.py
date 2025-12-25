"""Interactive environment builder for DexSuite.

This subpackage provides a small CLI and a curses-based TUI for assembling
- dexsuite.make configurations (task, robot, controllers, cameras, etc.).

Design goals:
- No extra dependencies for the default TUI (standard library only).
- Torch-only actions in the runtime runner: env.step(action) always receives a
  torch.Tensor.
- Keep the builder usable even when optional teleop device dependencies
  (for example, evdev and openvr) are not installed.
"""

from __future__ import annotations

__all__ = ["__version__"]

__version__ = "0.1.0"
