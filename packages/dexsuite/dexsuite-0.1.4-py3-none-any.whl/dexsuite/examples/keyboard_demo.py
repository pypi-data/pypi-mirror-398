from __future__ import annotations

import argparse
import sys
import time

import torch

import dexsuite as ds
from dexsuite.devices import Keyboard
from dexsuite.devices.keyboard import MAPPING_AZERTY, MAPPING_QWERTY


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="DexSuite keyboard teleoperation demo (single-arm + osc_pose).",
    )
    p.add_argument("--task", type=str, default="reach", help="Task name (e.g. reach).")
    p.add_argument("--manipulator", type=str, default="franka", help="Manipulator key.")
    p.add_argument("--gripper", type=str, default="robotiq", help="Gripper key.")
    p.add_argument(
        "--arm-control",
        type=str,
        default="osc_pose",
        help="Arm controller key (must be 6D pose).",
    )
    p.add_argument(
        "--gripper-control",
        type=str,
        default="joint_position",
        help="Gripper controller key.",
    )
    p.add_argument(
        "--layout",
        choices=("qwerty", "azerty"),
        default="qwerty",
        help="Keyboard mapping layout preset.",
    )
    p.add_argument("--pos-sens", type=float, default=1.0, help="Position sensitivity.")
    p.add_argument("--rot-sens", type=float, default=1.0, help="Rotation sensitivity.")
    p.add_argument(
        "--render-mode",
        choices=("human", "rgb_array", "none"),
        default="human",
        help="Render mode for ds.make().",
    )
    p.add_argument(
        "--control-hz",
        type=int,
        default=None,
        help="Optional override for SimOptions.control_hz.",
    )
    return p.parse_args(argv)


def _robot_device(env) -> torch.device:
    dev = getattr(getattr(env, "robot", None), "device", None)
    return dev if isinstance(dev, torch.device) else torch.device("cpu")


def _layout_dims(env) -> tuple[int, int]:
    layout = getattr(getattr(env, "robot", None), "_layout", None)
    if layout is None or not getattr(layout, "segments", None):
        raise RuntimeError("Robot action layout not available (robot._layout missing).")
    segs = list(layout.segments)
    arm_dim = int(segs[0].stop - segs[0].start) if segs else 0
    grip_dim = int(segs[1].stop - segs[1].start) if len(segs) > 1 else 0
    return arm_dim, grip_dim


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    render_mode = None if args.render_mode == "none" else args.render_mode

    sim = None
    if args.control_hz is not None:
        sim = ds.SimOptions(control_hz=int(args.control_hz))

    env = ds.make(
        args.task,
        manipulator=args.manipulator,
        gripper=args.gripper,
        arm_control=args.arm_control,
        gripper_control=args.gripper_control,
        sim=sim,
        render_mode=render_mode,
    )

    arm_dim = 0
    grip_dim = 0
    try:
        env.reset()
        arm_dim, grip_dim = _layout_dims(env)
        if arm_dim != 6:
            raise ValueError(
                f"Keyboard demo requires a 6D pose arm controller (arm_dim=6), got {arm_dim}.",
            )

        mapping = MAPPING_QWERTY if args.layout == "qwerty" else MAPPING_AZERTY
        kb = Keyboard(
            controller="OSCPose",
            normalized=True,
            pos_sens=float(args.pos_sens),
            rot_sens=float(args.rot_sens),
            mapping=mapping,
            gripper=(grip_dim > 0),
        )

        dt = 1.0 / float(getattr(getattr(env, "sim_options", None), "control_hz", 20))
        dev = _robot_device(env)
        last = time.time()
        try:
            while True:
                d = kb.get_action()
                pose = torch.as_tensor(
                    d.get("pose", []), dtype=torch.float32, device=dev,
                )
                if pose.numel() != arm_dim:
                    pose = torch.zeros((arm_dim,), dtype=torch.float32, device=dev)

                action = pose
                if grip_dim > 0:
                    grip = torch.as_tensor(
                        d.get("gripper", [0.0]),
                        dtype=torch.float32,
                        device=dev,
                    ).flatten()
                    if grip.numel() == 1 and grip_dim > 1:
                        grip = grip.repeat(grip_dim)
                    if grip.numel() != grip_dim:
                        grip = torch.zeros((grip_dim,), dtype=torch.float32, device=dev)
                    action = torch.cat([pose, grip], dim=0)

                reset = d.get("reset", [0.0])
                if reset and float(reset[0]) != 0.0:
                    env.reset()

                with torch.no_grad():
                    env.step(action)

                now = time.time()
                sleep = dt - (now - last)
                if sleep > 0:
                    time.sleep(sleep)
                last = time.time()
        finally:
            try:
                kb.listener.stop()
            except Exception:
                pass

    finally:
        env.close()


if __name__ == "__main__":
    raise SystemExit(main())
