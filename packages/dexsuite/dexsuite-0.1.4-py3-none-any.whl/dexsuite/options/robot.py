"""Configuration options for robot hardware, controllers, and layout."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from dexsuite.utils.options_utils import load_defaults, resolve_workspace_strict

from .layout import LayoutOptions, PoseOptions
from .options import Vec3


# --------------------------------------------------------------------- #
# Internal helpers
# --------------------------------------------------------------------- #
def _load_controller_defaults() -> tuple[str, str, dict[str, dict[str, Any]]]:
    """Load default controller names and configurations from YAML files.

    Returns:
        A tuple containing the default manipulator controller name, the default
        gripper controller name, and a dictionary of all available controller
        specifications.

    Raises:
        ValueError: If the controllers.yaml file is missing required
            sections or is improperly formatted.
    """
    cfg = load_defaults("controllers")
    if not isinstance(cfg, dict):
        raise ValueError("controllers.yaml must be a mapping.")
    if "defaults" not in cfg or "controllers" not in cfg:
        raise ValueError(
            "controllers.yaml must contain 'defaults' and 'controllers' sections.",
        )
    dflt = cfg["defaults"]
    ctrls = cfg["controllers"]
    if "manipulator" not in dflt or "gripper" not in dflt:
        raise ValueError(
            "controllers.yaml.defaults must have 'manipulator' and 'gripper'.",
        )
    if not isinstance(ctrls, dict):
        raise ValueError(
            "controllers.yaml.controllers must be a mapping of controller_name -> params.",
        )
    return str(dflt["manipulator"]), str(dflt["gripper"]), ctrls


_DEFAULT_MANIP_CTRL, _DEFAULT_GRIP_CTRL, _CTRL_SPECS = _load_controller_defaults()


@dataclass(slots=True)
class AABBOptions:
    """An axis-aligned bounding box (AABB) in the arm's base frame.

    Attributes:
        min: The (x, y, z) coordinates of the minimum corner of the box.
        max: The (x, y, z) coordinates of the maximum corner of the box.
    """

    min: Vec3 = (0.0, 0.0, 0.0)
    max: Vec3 = (1.0, 1.0, 1.0)

    def __post_init__(self) -> None:
        if len(self.min) != 3 or len(self.max) != 3:
            raise ValueError("AABB must have 3D min and max.")
        for v in (*self.min, *self.max):
            if not isinstance(v, (int, float)):
                raise TypeError("AABB coordinates must be numeric.")
        if any(lo > hi for lo, hi in zip(self.min, self.max, strict=False)):
            raise ValueError("AABBOptions: each min[i] must be <= max[i].")


@dataclass(slots=True)
class ControllerOptions:
    """Specifications for a controller and its configuration.

    Attributes:
        name: The name of the controller, which must be registered in the
            controller registry.
        config: A dictionary of parameters to be passed to the controller's
            __init__ method during instantiation.
    """

    name: str
    config: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ArmOptions:
    """Specifications for a single robotic arm, including its gripper and controllers.

    This class specifies the hardware models for a manipulator and an optional
    gripper, as well as the controllers used to operate them. For modular
    arms, a gripper model must be specified. For integrated arms, the gripper
    field should be None or "builtin".

    Attributes:
        manipulator: The registered name of the manipulator model.
        gripper: The registered name of the gripper model, if applicable.
        manipulator_controller: The controller configuration for the arm.
        gripper_controller: The controller configuration for the gripper.
        workspace: An optional AABB defining the robot's operational workspace.
    """

    manipulator: str = field(
        default_factory=lambda: str(load_defaults("arms")["manipulator"]),
    )
    gripper: str | None = field(
        default_factory=lambda: load_defaults("arms")["gripper"],
    )

    manipulator_controller: ControllerOptions = field(
        default_factory=lambda: ControllerOptions(
            name=_DEFAULT_MANIP_CTRL,
            config=dict(_CTRL_SPECS.get(_DEFAULT_MANIP_CTRL, {})),
        ),
    )
    gripper_controller: ControllerOptions | None = field(
        default_factory=lambda: ControllerOptions(
            name=_DEFAULT_GRIP_CTRL,
            config=dict(_CTRL_SPECS.get(_DEFAULT_GRIP_CTRL, {})),
        ),
    )

    workspace: AABBOptions | None = None

    def __post_init__(self) -> None:
        if self.workspace is None:
            try:
                spec = resolve_workspace_strict(self.manipulator)
            except ValueError:
                # Allow constructing options for unknown manipulators so errors can
                # be raised at build time (registry lookup) rather than at options
                # construction time.
                return
            self.workspace = AABBOptions(min=tuple(spec["min"]), max=tuple(spec["max"]))


@dataclass(slots=True)
class RobotOptions:
    """The complete robot configuration for an environment.

    This class supports both single-arm and bimanual setups. For bimanual
    robots, left and right arm options must be provided, along with a layout
    preset. For single-arm robots, only the single arm option is used.

    Attributes:
        type_of_robot: The robot configuration type, either 'single' or
            'bimanual'.
        single: The configuration for a single-arm robot.
        left: The configuration for the left arm of a bimanual robot.
        right: The configuration for the right arm of a bimanual robot.
        layout: The placement options for the robot(s) in the world.
        visualize_tcp: If True, renders a visual marker for the Tool Center
            Point (TCP).
        visualize_aabb: If True, renders a visual marker for the workspace
            bounding box (AABB).
    """

    type_of_robot: Literal["single", "bimanual"] = field(
        default_factory=lambda: str(load_defaults("robots")["type_of_robot"]),
    )
    single: ArmOptions | None = None
    left: ArmOptions | None = None
    right: ArmOptions | None = None

    layout: LayoutOptions = field(default_factory=LayoutOptions)

    visualize_tcp: bool = field(
        default_factory=lambda: bool(load_defaults("robots")["visualize_tcp"]),
    )
    visualize_aabb: bool = field(
        default_factory=lambda: bool(load_defaults("robots")["visualize_aabb"]),
    )

    def __post_init__(self) -> None:
        if self.type_of_robot == "single":
            if self.single is None:
                self.single = ArmOptions()
            # Ensure a pose object exists for single-arm
            if self.layout.single is None:
                self.layout.single = PoseOptions()
            if self.layout.preset is not None:
                raise ValueError(
                    "Single-arm robots do not use layout presets (set 'single' pose explicitly if needed).",
                )
            return

        if self.type_of_robot == "bimanual":
            # If user didn't pass arms, create defaults so type_of_robot is enough.
            if self.left is None:
                self.left = ArmOptions()
            if self.right is None:
                self.right = ArmOptions()

            user_left = self.layout.left is not None
            user_right = self.layout.right is not None

            # If both sides are explicitly provided, keep them and ignore any preset.
            if user_left and user_right:
                return

            # Fill any missing side from a preset.
            if not self.layout.preset:
                # Default preset only when we need to fill something.
                self.layout.preset = "side_by_side"

            L_preset, R_preset = self.layout.resolve_bimanual(
                self.left.manipulator,
                self.right.manipulator,
            )

            if not user_left:
                self.layout.left = L_preset
            if not user_right:
                self.layout.right = R_preset
            return

        raise ValueError(f"Unknown type_of_robot '{self.type_of_robot}'.")
