from robomimic.envs.env_base import EnvBase

import dexsuite as ds
from dexsuite.options import (
    AABBOptions,
    ArmOptions,
    CamerasOptions,
    ControllerOptions,
    DynamicCamOptions,
    LayoutOptions,
    PoseOptions,
    RobotOptions,
    SimOptions,
    StaticCamOptions,
)


def _t2(x):
    return (int(x[0]), int(x[1]))


def _t3(x):
    return (float(x[0]), float(x[1]), float(x[2]))


def _t4(x):
    return (float(x[0]), float(x[1]), float(x[2]), float(x[3]))


def _ctrl(d: dict) -> ControllerOptions:
    return ControllerOptions(name=d["name"], config=dict(d.get("config", {})))


def _aabb(d: dict) -> AABBOptions:
    return AABBOptions(min=_t3(d["min"]), max=_t3(d["max"]))


def _arm(d: dict) -> ArmOptions:
    return ArmOptions(
        manipulator=d["manipulator"],
        gripper=d.get("gripper"),
        manipulator_controller=_ctrl(d["manipulator_controller"]),
        gripper_controller=(
            _ctrl(d["gripper_controller"]) if d.get("gripper_controller") else None
        ),
        workspace=(_aabb(d["workspace"]) if d.get("workspace") else None),
    )


def _pose(d: dict | None) -> PoseOptions | None:
    if d is None:
        return None
    return PoseOptions(
        pos=_t3(d["pos"]),
        yaw_rad=float(d.get("yaw_rad", 0.0)),
        quat=(None if d.get("quat") is None else _t4(d["quat"])),
    )


def _layout(d: dict | None) -> LayoutOptions:
    if d is None:
        return LayoutOptions()
    return LayoutOptions(
        preset=d.get("preset"),
        params=dict(d.get("params", {})),
        single=_pose(d.get("single")),
        left=_pose(d.get("left")),
        right=_pose(d.get("right")),
    )


def _cams(d: dict) -> CamerasOptions:
    # static entries can be preset strings OR full dicts -> StaticCamOptions
    static = {
        name: (
            val
            if isinstance(val, str)
            else StaticCamOptions(
                pos=_t3(val["pos"]),
                lookat=_t3(val["lookat"]),
                fov=float(val.get("fov", 55.0)),
                res=_t2(val.get("res", (224, 224))),
            )
        )
        for name, val in (d.get("static") or {}).items()
    }

    # dynamic entries can be preset strings OR full dicts -> DynamicCamOptions
    dynamic = {
        name: (
            val
            if isinstance(val, str)
            else DynamicCamOptions(
                link=val.get("link"),
                pos_offset=_t3(val.get("pos_offset", (0.0, 0.0, 0.0))),
                quat_offset=_t4(val.get("quat_offset", (1.0, 0.0, 0.0, 0.0))),
                fov=float(val.get("fov", 60.0)),
                res=_t2(val.get("res", (224, 224))),
            )
        )
        for name, val in (d.get("dynamic") or {}).items()
    }

    return CamerasOptions(
        static=static,
        dynamic=dynamic,
        modalities=tuple(d.get("modalities", ("rgb",))),
    )


def _extract_env_options(blob: dict) -> tuple[SimOptions, RobotOptions, CamerasOptions]:
    opts = blob.get("options", blob)

    # Sim
    sim = SimOptions(
        control_hz=int(opts["sim"]["control_hz"]),
        performance_mode=bool(opts["sim"]["performance_mode"]),
        n_envs=int(opts["sim"]["n_envs"]),
    )

    r = opts["robot"]
    robot = RobotOptions(
        type_of_robot=r["type_of_robot"],
        single=_arm(r["single"]) if r.get("single") else None,
        left=_arm(r["left"]) if r.get("left") else None,
        right=_arm(r["right"]) if r.get("right") else None,
        layout=_layout(r.get("layout")),
        visualize_tcp=bool(r.get("visualize_tcp", False)),
        visualize_aabb=bool(r.get("visualize_aabb", False)),
    )

    cameras = _cams(opts["cameras"])

    return sim, robot, cameras


class EnvDexsuite(EnvBase):
    """Dexsuite wrapper around Robomimic."""

    # EnvBase
    def __init__(
        self,
        env_name,
        render=False,
        render_offscreen=False,
        use_image_obs=False,
        use_depth_obs=False,
        **kwargs,
    ):
        """Initialize the Dexsuite environment wrapper."""
        super().__init__(
            env_name,
            render,
            render_offscreen,
            use_image_obs,
            use_depth_obs,
            **kwargs,
        )

        self.env_config = kwargs
        self.task = kwargs.get("task")
        self.render_mode = "human" if render_offscreen else "rgb_array"
        self.sim_options, self.robot_options, self.cameras_options = (
            _extract_env_options(self.env_config)
        )
        print(self.cameras_options)
        self.env = ds.make(
            self.task,
            sim=self.sim_options,
            robot=self.robot_options,
            cameras=self.cameras_options,
            render_mode=self.render_mode,
        )
