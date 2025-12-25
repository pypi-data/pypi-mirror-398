"""Non-curses fallback builder (plain stdin prompts).

This exists primarily for platforms where curses is unavailable.
"""

from __future__ import annotations

from .defaults import default_spec
from .registry_scan import (
    available_controllers,
    available_grippers,
    available_manipulators,
    available_tasks,
    manipulator_infos,
    supported_grippers_for_manipulator,
)
from .spec import ArmSpec, BuilderSpec


def _choose(prompt: str, options: list[str], *, default: str | None = None) -> str:
    if not options:
        raise ValueError(f"No options available for {prompt!r}")
    idx_default = options.index(default) if (default in options) else 0
    while True:
        print(f"\n{prompt}")
        for i, opt in enumerate(options, start=1):
            mark = "*" if (i - 1) == idx_default else " "
            print(f"  {mark} {i:2d}) {opt}")
        raw = input(f"Select [1-{len(options)}] (default {idx_default + 1}): ").strip()
        if raw == "":
            return options[idx_default]
        try:
            k = int(raw)
        except ValueError:
            continue
        if 1 <= k <= len(options):
            return options[k - 1]


def run_simple_builder() -> BuilderSpec:
    """Run a basic prompt-based builder and return a BuilderSpec."""
    spec = default_spec()

    tasks = available_tasks()
    if tasks:
        spec.task = _choose(
            "Task",
            tasks,
            default=spec.task if spec.task in tasks else None,
        )

    spec.type_of_robot = _choose(
        "Robot type",
        ["single", "bimanual"],
        default=spec.type_of_robot,
    )  # type: ignore[assignment]

    manip_kinds = {i.key: i.kind for i in manipulator_infos()}
    manipulators = available_manipulators()
    grippers = available_grippers()
    controllers = available_controllers()

    def edit_arm(label: str, arm: ArmSpec | None) -> ArmSpec:
        if arm is None:
            arm = ArmSpec(
                manipulator=manipulators[0] if manipulators else "franka",
                gripper=grippers[0] if grippers else None,
                arm_control="osc_pose",
                gripper_control="joint_position",
            )

        arm.manipulator = _choose(
            f"{label} manipulator",
            manipulators,
            default=arm.manipulator,
        )
        if manip_kinds.get(arm.manipulator) == "integrated":
            arm.gripper = None
        else:
            supported = supported_grippers_for_manipulator(arm.manipulator)
            grip_opts = supported if supported else grippers
            if grip_opts:
                arm.gripper = _choose(
                    f"{label} gripper",
                    grip_opts,
                    default=arm.gripper,
                )

        arm.arm_control = _choose(
            f"{label} arm controller",
            controllers,
            default=arm.arm_control,
        )
        grip_ctrls = [c for c in controllers if c.startswith("joint_")]
        if grip_ctrls:
            arm.gripper_control = _choose(
                f"{label} gripper controller",
                grip_ctrls,
                default=arm.gripper_control,
            )
        return arm

    if spec.type_of_robot == "single":
        spec.single = edit_arm("Single", spec.single)
        spec.left = None
        spec.right = None
    else:
        spec.left = edit_arm("Left", spec.left)
        spec.right = edit_arm("Right", spec.right)
        spec.single = None

    # Sim params
    raw = input(f"\nControl Hz (current {spec.control_hz}): ").strip()
    if raw:
        spec.control_hz = int(raw)
    raw = input(f"n_envs (current {spec.n_envs}): ").strip()
    if raw:
        spec.n_envs = int(raw)
    raw = input(
        f"performance_mode (0/1, current {int(spec.performance_mode)}): ",
    ).strip()
    if raw:
        spec.performance_mode = bool(int(raw))

    raw = input(
        f"input_device [keyboard|spacemouse|vive_controller|vive_tracker|none] (current {spec.input_device}): ",
    ).strip()
    if raw:
        spec.input_device = raw
    return spec
