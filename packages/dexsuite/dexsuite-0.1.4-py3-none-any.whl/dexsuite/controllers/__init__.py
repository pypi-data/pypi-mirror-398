"""A factory for creating robot controllers and lazy-loading them."""

from __future__ import annotations

import inspect
from importlib import import_module
from typing import Any

from dexsuite.core.registry import CONTROLLER_REG

__all__ = ["make"]


def _lazy_ensure(key: str) -> None:
    """Lazily import and register a controller if not already present.

    Args:
        key: The name of the controller to load.

    Raises:
        KeyError: If the controller module cannot be found or if the module
            is found but does not register the controller.
    """
    if key not in CONTROLLER_REG:
        try:
            import_module(f"{__name__}.{key}")
        except ModuleNotFoundError as e:
            raise KeyError(
                f"unknown controller '{key}' (no module {__name__}.{key})",
            ) from e
        if key not in CONTROLLER_REG:
            raise KeyError(
                f"unknown controller '{key}' (module imported but not registered)",
            )


def _allowed_from_init(cls) -> set[str]:
    """Inspect a controller's __init__ to find allowed keyword arguments.

    Args:
        cls: The controller class to inspect.

    Returns:
        A set of string names for the allowed keyword arguments.
    """
    sig = inspect.signature(cls.__init__)
    allowed: set[str] = set()
    for name, p in sig.parameters.items():
        if name in ("self", "entity", "model"):
            continue
        if p.kind in (
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        ):
            allowed.add(name)
    return allowed


def make(cfg, *, entity, model, **kwargs):
    """Create a controller instance from a configuration object.

    This function validates the existence of the requested controller, filters
    and validates the configuration dictionary against parameters accepted by
    the controller's __init__ method, and then instantiates the controller.

    Args:
        cfg: The controller configuration object, typically ControllerOptions.
        entity: The simulation entity the controller will operate on.
        model: The robot component model associated with the entity.
        kwargs: Reserved for future use. Must be empty.

    Returns:
        An instantiated controller object.

    Raises:
        TypeError: If the cfg.config attribute is not a dictionary, contains
            unknown keys, or if extra keyword arguments are provided.
    """
    if kwargs:
        extra = ", ".join(sorted(kwargs.keys()))
        raise TypeError(f"Unexpected keyword arguments to controllers.make(): {extra}.")

    key = str(cfg.name).lower()
    _lazy_ensure(key)
    cls = CONTROLLER_REG[key]
    allowed = _allowed_from_init(cls)

    if not isinstance(cfg.config, dict):
        raise TypeError("ControllerOptions.config must be a dict.")
    unknown = sorted(set(cfg.config) - allowed)
    if unknown:
        allowed_s = ", ".join(sorted(allowed))
        unknown_s = ", ".join(unknown)
        raise TypeError(
            f"Unknown config key(s) for controller '{key}': {unknown_s}. "
            f"Allowed: {allowed_s}.",
        )
    payload: dict[str, Any] = {k: v for k, v in cfg.config.items() if k in allowed}

    return cls(entity=entity, model=model, **payload)
