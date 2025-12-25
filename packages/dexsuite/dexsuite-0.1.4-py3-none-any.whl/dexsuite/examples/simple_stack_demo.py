from __future__ import annotations

import argparse
import sys

import torch

import dexsuite as ds


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="DexSuite quick sanity demo (loads an env and steps it).",
    )
    p.add_argument("--task", type=str, default="stack", help="Task name (e.g. stack).")
    p.add_argument("--manipulator", type=str, default="franka", help="Manipulator key.")
    p.add_argument("--gripper", type=str, default="robotiq", help="Gripper key.")
    p.add_argument(
        "--arm-control",
        type=str,
        default="osc_pose",
        help="Arm controller key.",
    )
    p.add_argument(
        "--gripper-control",
        type=str,
        default="joint_position",
        help="Gripper controller key.",
    )
    p.add_argument("--steps", type=int, default=300, help="Number of env steps.")
    p.add_argument(
        "--render-mode",
        choices=("human", "rgb_array", "none"),
        default="human",
        help="Render mode for ds.make().",
    )
    p.add_argument("--seed", type=int, default=0, help="Random seed for env.reset().")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    render_mode = None if args.render_mode == "none" else args.render_mode

    env = ds.make(
        args.task,
        manipulator=args.manipulator,
        gripper=args.gripper,
        arm_control=args.arm_control,
        gripper_control=args.gripper_control,
        render_mode=render_mode,
    )

    try:
        env.reset(seed=args.seed)
        act_dim = int(env.action_space.shape[0])
        device = getattr(getattr(env, "robot", None), "device", torch.device("cpu"))
        action = torch.zeros((act_dim,), dtype=torch.float32, device=device)

        for _ in range(int(args.steps)):
            _, _, _, _, info = env.step(action)
            success = info.get("success")
            if (
                torch.is_tensor(success)
                and success.numel() == 1
                and bool(success.item())
            ):
                break

        print("Dexsuite is good to go!")
        return 0
    finally:
        env.close()


if __name__ == "__main__":
    raise SystemExit(main())
