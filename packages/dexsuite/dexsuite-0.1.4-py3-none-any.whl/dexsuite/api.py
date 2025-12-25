from __future__ import annotations

import contextlib
import io
import inspect
import sys
from typing import Any

from dexsuite.core.registry import ENV_REG
from dexsuite.options import (
    ArmOptions,
    CamerasOptions,
    ControllerOptions,
    DynamicCamOptions,
    LayoutOptions,
    RobotOptions,
    SimOptions,
)
from dexsuite.utils import get_device
from dexsuite.utils.options_utils import load_defaults

_GEN_READY = False


@contextlib.contextmanager
def _ensure_stderr_fileno() -> None:
    """Ensure sys.stderr.fileno() works (notebook compatibility).

    Genesis may temporarily redirect libc stderr during MJCF/URDF parsing and
    assumes sys.stderr.fileno() exists. In Jupyter/Colab, sys.stderr is
    often an ipykernel.iostream.OutStream that raises io.UnsupportedOperation.
    """

    def _has_fileno(stream) -> bool:
        try:
            stream.fileno()
            return True
        except Exception:
            return False

    if _has_fileno(sys.stderr):
        yield
        return

    original = sys.stderr
    fallback = getattr(sys, "__stderr__", None)
    if fallback is not None and _has_fileno(fallback):
        sys.stderr = fallback
        try:
            yield
        finally:
            sys.stderr = original
        return

    class _StderrProxy(io.TextIOBase):
        def __init__(self, stream):
            self._stream = stream

        def fileno(self) -> int:  # noqa: D102
            return 2

        def flush(self) -> None:  # noqa: D102
            try:
                self._stream.flush()
            except Exception:
                pass

        def write(self, s: str) -> int:  # noqa: D102
            return self._stream.write(s)

        def __getattr__(self, name: str):  # noqa: D105
            return getattr(self._stream, name)

    sys.stderr = _StderrProxy(original)
    try:
        yield
    finally:
        sys.stderr = original


# Genesis may redirect libc stderr at import-time, which fails in notebooks
# (ipykernel stderr does not implement fileno()).
with _ensure_stderr_fileno():
    import genesis as gs


_MAKE_ALLOWED_KEYS: frozenset[str] = frozenset(
    {
        # Component API (preferred)
        "robot",
        "sim",
        "cameras",
        "layout",
        "render_mode",
        # Flat API (convenience)
        "manipulator",
        "gripper",
        "arm_control",
        "gripper_control",
        "control_hz",
        "performance_mode",
        "n_envs",
        "modalities",
        # Backward-compat / aliases
        "n_env",
    },
)


def _normalize_make_kwargs(kw_in: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize ds.make keyword arguments.

    DexSuite intentionally keeps a small public make surface. Unknown keys raise
    rather than being silently ignored.

    Normalizations:
        - n_env is accepted as an alias for n_envs.
        - cameras="front" is normalized to cameras=("front",).
        - modalities="rgb" is normalized to modalities=("rgb",).
    """
    kw = dict(kw_in)

    def _coerce_pos_int(name: str) -> None:
        if name not in kw or kw[name] is None:
            return
        v = kw[name]
        if isinstance(v, bool):
            raise TypeError(f"{name} must be an int, not a bool.")
        if isinstance(v, float) and not v.is_integer():
            raise TypeError(f"{name} must be an integer value, got {v!r}.")
        try:
            iv = int(v)
        except (TypeError, ValueError) as e:
            raise TypeError(f"{name} must be an int, got {type(v)}.") from e
        if iv <= 0:
            raise ValueError(f"{name} must be > 0, got {iv}.")
        kw[name] = iv

    if "n_env" in kw:
        if "n_envs" in kw:
            raise TypeError("ds.make() got both 'n_env' and 'n_envs'; use only one.")
        kw["n_envs"] = kw.pop("n_env")

    unknown = set(kw) - set(_MAKE_ALLOWED_KEYS)
    if unknown:
        unknown_s = ", ".join(sorted(unknown))
        allowed_s = ", ".join(sorted(k for k in _MAKE_ALLOWED_KEYS if k != "n_env"))
        raise TypeError(
            f"ds.make() got unexpected keyword argument(s): {unknown_s}. "
            f"Allowed: {allowed_s}.",
        )

    if "cameras" in kw and isinstance(kw["cameras"], str):
        kw["cameras"] = (kw["cameras"],)
    if "modalities" in kw and isinstance(kw["modalities"], str):
        kw["modalities"] = (kw["modalities"],)

    layout = kw.get("layout")
    if layout is not None and not isinstance(layout, (LayoutOptions, str)):
        raise TypeError("layout must be a preset string, LayoutOptions, or None.")

    cams = kw.get("cameras")
    if cams is not None and not isinstance(cams, (CamerasOptions, tuple, list)):
        raise TypeError(
            "cameras must be CamerasOptions, a list/tuple of names, a single name, or None.",
        )
    if isinstance(cams, (tuple, list)):
        if len(cams) == 0:
            raise ValueError("cameras must be a non-empty list/tuple (or None).")
        bad = [c for c in cams if not isinstance(c, str)]
        if bad:
            raise TypeError("All camera names must be strings.")

    modalities = kw.get("modalities")
    if modalities is not None and not isinstance(modalities, (tuple, list)):
        raise TypeError(
            "modalities must be a list/tuple of strings or a single string.",
        )
    if isinstance(modalities, (tuple, list)):
        bad = [m for m in modalities if not isinstance(m, str)]
        if bad:
            raise TypeError("All modalities entries must be strings.")

    robot = kw.get("robot")
    if isinstance(robot, RobotOptions):
        flat_robot_keys = ("manipulator", "gripper", "arm_control", "gripper_control")
        bad = [k for k in flat_robot_keys if kw.get(k) is not None]
        if bad:
            raise ValueError(
                "Provide either 'robot=RobotOptions(...)' OR the flat robot keys "
                f"{bad} - not both.",
            )
        if isinstance(kw.get("layout"), str):
            raise ValueError(
                "When passing robot=RobotOptions(...), do not pass layout as a string. "
                "Set robot.layout.preset or pass layout=LayoutOptions(...) instead.",
            )

    sim = kw.get("sim")
    if isinstance(sim, SimOptions):
        flat_sim_keys = ("control_hz", "performance_mode", "n_envs")
        bad = [k for k in flat_sim_keys if kw.get(k) is not None]
        if bad:
            raise ValueError(
                "Provide either 'sim=SimOptions(...)' OR the flat sim keys "
                f"{bad} - not both.",
            )

    if isinstance(cams, CamerasOptions) and kw.get("modalities") is not None:
        raise ValueError(
            "When passing cameras=CamerasOptions(...), set modalities on that object "
            "and do not pass modalities=... separately.",
        )

    # Type sanity for flat scalars (fail early with clear errors).
    _coerce_pos_int("control_hz")
    _coerce_pos_int("n_envs")
    if kw.get("performance_mode") is not None and not isinstance(
        kw["performance_mode"],
        bool,
    ):
        raise TypeError("performance_mode must be a bool.")

    rm = kw.get("render_mode")
    if rm is not None and not isinstance(rm, str):
        raise TypeError("render_mode must be a string or None.")
    if rm is not None and rm not in ("human", "rgb_array"):
        raise ValueError("render_mode must be 'human', 'rgb_array', or None.")

    manip = kw.get("manipulator")
    if manip is not None:
        if isinstance(manip, str):
            pass
        elif isinstance(manip, (tuple, list)):
            if len(manip) not in (1, 2):
                raise ValueError(
                    "manipulator must be a string (single) or a length-2 pair (bimanual).",
                )
            bad = [m for m in manip if not isinstance(m, str)]
            if bad:
                raise TypeError("manipulator entries must be strings.")
        else:
            raise TypeError(
                "manipulator must be a string or a length-2 tuple/list of strings.",
            )

    grip = kw.get("gripper")
    if grip is not None:
        if isinstance(grip, str):
            pass
        elif isinstance(grip, (tuple, list)):
            if len(grip) not in (1, 2):
                raise ValueError(
                    "gripper must be a string/None (replicated) or a length-2 pair for bimanual.",
                )
            bad = [g for g in grip if (g is not None and not isinstance(g, str))]
            if bad:
                raise TypeError("gripper entries must be strings or None.")
        else:
            raise TypeError("gripper must be a string, None, or a tuple/list.")

    for name in ("arm_control", "gripper_control"):
        if kw.get(name) is not None and not isinstance(kw[name], str):
            raise TypeError(f"{name} must be a string or None.")

    return kw


def _lazy_init_genesis() -> None:
    global _GEN_READY
    if _GEN_READY:
        return
    # Genesis' logger may read `genesis._theme` during initialization. Some
    # installs (e.g., mixed/old Genesis packages) can hit an AttributeError if
    # `_theme` hasn't been set yet.
    if not hasattr(gs, "_theme"):
        gs._theme = "dark"
    dev = get_device()
    gs.init(
        backend=(gs.cuda if dev.type == "cuda" else gs.cpu),
        performance_mode=False,
        logging_level="error",
    )
    _GEN_READY = True


__all__ = ["make"]


def _as_tuple(x) -> tuple:
    if x is None:
        return tuple()
    if isinstance(x, (tuple, list)):
        return tuple(x)
    return (x,)


def _resolve_dynamic_preset(
    preset_name: str,
    manip_name: str,
    gripper_name: str | None = None,
) -> DynamicCamOptions:
    cfg = load_defaults("cameras")
    if not isinstance(cfg, dict):
        raise ValueError("config/env_configs/cameras.yaml must be a mapping.")
    dyn = cfg.get("dynamic")
    if not isinstance(dyn, dict):
        raise ValueError("'dynamic' section missing or not a mapping in cameras.yaml.")
    preset = dyn.get(preset_name)
    if not isinstance(preset, dict):
        raise ValueError(f"Dynamic preset '{preset_name}' not found in cameras.yaml.")

    merged: dict[str, object] = {}
    for k in ("fov", "res"):
        if k not in preset:
            raise ValueError(f"Dynamic preset '{preset_name}' missing '{k}'.")
        merged[k] = preset[k]

    default = preset.get("default") or {}
    if not isinstance(default, dict):
        raise ValueError(
            f"Dynamic preset '{preset_name}' must define a 'default' mapping.",
        )
    merged.update(default)

    # accept either "overrides" or "by" (support both for backward-compat)
    raw_map = preset.get("overrides")
    if raw_map is None:
        raw_map = preset.get("by")
    chosen = None
    if isinstance(raw_map, dict):
        # case-insensitive lookup for gripper first, then manip
        keys = {str(k).strip().lower(): v for k, v in raw_map.items()}
        if gripper_name:
            gk = str(gripper_name).strip().lower()
            if gk in keys:
                chosen = keys[gk]
        if chosen is None:
            mk = str(manip_name).strip().lower()
            if mk in keys:
                chosen = keys[mk]
        # simple tolerant fallback: if exact not found, try substring match
        if chosen is None and gripper_name:
            gk = str(gripper_name).strip().lower()
            for k, v in keys.items():
                if k in gk or gk in k:
                    chosen = v
                    break
        if chosen is None:
            mk = str(manip_name).strip().lower()
            for k, v in keys.items():
                if k in mk or mk in k:
                    chosen = v
                    break

    if chosen is not None:
        if not isinstance(chosen, dict):
            raise ValueError(
                f"Dynamic preset '{preset_name}': override must be a mapping.",
            )
        # merge only the fields provided; keep any from default (e.g., quat_offset)
        merged.update(chosen)

    # ensure we have offsets (pull from default if override omitted them)
    merged.setdefault("pos_offset", (0.0, 0.0, 0.0))
    merged.setdefault("quat_offset", (1.0, 0.0, 0.0, 0.0))

    return DynamicCamOptions(
        link=merged.get("link"),
        pos_offset=tuple(merged["pos_offset"]),
        quat_offset=tuple(merged["quat_offset"]),
        fov=float(merged["fov"]),
        res=tuple(merged["res"]),
    )


def _mk_cameras(
    kw: dict,
    existing: CamerasOptions | None,
    robot: RobotOptions,
) -> CamerasOptions:
    if "cameras" in kw and kw["cameras"] is None:
        modalities = kw.get("modalities", ("rgb",))
        if isinstance(modalities, str):
            modalities = (modalities,)
        return CamerasOptions(static={}, dynamic={}, modalities=tuple(modalities))

    if isinstance(existing, CamerasOptions):
        resolved_dynamic: dict[str, DynamicCamOptions] = {}
        for name, val in list(existing.dynamic.items()):
            if isinstance(val, DynamicCamOptions):
                resolved_dynamic[name] = val
            else:
                if robot.type_of_robot == "bimanual":
                    left_manip = str(robot.left.manipulator)
                    right_manip = str(robot.right.manipulator)
                    left_grip = (
                        str(robot.left.gripper)
                        if robot.left.gripper is not None
                        else None
                    )
                    right_grip = (
                        str(robot.right.gripper)
                        if robot.right.gripper is not None
                        else None
                    )
                    resolved_dynamic[f"left_{name}"] = _resolve_dynamic_preset(
                        val,
                        left_manip,
                        left_grip,
                    )
                    resolved_dynamic[f"right_{name}"] = _resolve_dynamic_preset(
                        val,
                        right_manip,
                        right_grip,
                    )
                else:
                    single_manip = str(robot.single.manipulator)
                    single_grip = (
                        str(robot.single.gripper)
                        if robot.single.gripper is not None
                        else None
                    )
                    resolved_dynamic[name] = _resolve_dynamic_preset(
                        val,
                        single_manip,
                        single_grip,
                    )
        return CamerasOptions(
            static=existing.static,
            dynamic=resolved_dynamic,
            modalities=existing.modalities,
        )

    names = kw.get("cameras")
    if names is None:
        names = ("front", "wrist")
    if not isinstance(names, (list, tuple)):
        raise TypeError(
            "cameras must be a list/tuple of names, e.g., ['front','wrist'].",
        )

    modalities = kw.get("modalities", ("rgb",))
    if isinstance(modalities, str):
        modalities = (modalities,)
    if not isinstance(modalities, (list, tuple)):
        raise TypeError("modalities must be a list/tuple (or a single string).")
    modalities = tuple(modalities)
    if "rgb" not in modalities:
        raise ValueError("modalities must include 'rgb'.")

    cfg = load_defaults("cameras")
    if not isinstance(cfg, dict):
        raise ValueError("config/env_configs/cameras.yaml must be a mapping.")
    static_cfg = cfg.get("static")
    if not isinstance(static_cfg, dict):
        raise ValueError("'static' section missing or not a mapping in cameras.yaml.")

    static_map: dict[str, str] = {}
    dynamic_map: dict[str, DynamicCamOptions] = {}

    for nm in names:
        if not isinstance(nm, str):
            raise TypeError(f"Camera name must be str, got {type(nm)}")
        if nm == "wrist":
            if robot.type_of_robot == "bimanual":
                left_manip = str(robot.left.manipulator)
                right_manip = str(robot.right.manipulator)
                left_grip = (
                    str(robot.left.gripper) if robot.left.gripper is not None else None
                )
                right_grip = (
                    str(robot.right.gripper)
                    if robot.right.gripper is not None
                    else None
                )
                dynamic_map["left_wrist"] = _resolve_dynamic_preset(
                    "wrist_cam",
                    left_manip,
                    left_grip,
                )
                dynamic_map["right_wrist"] = _resolve_dynamic_preset(
                    "wrist_cam",
                    right_manip,
                    right_grip,
                )
            else:
                single_manip = str(robot.single.manipulator)
                single_grip = (
                    str(robot.single.gripper)
                    if robot.single.gripper is not None
                    else None
                )
                dynamic_map["wrist"] = _resolve_dynamic_preset(
                    "wrist_cam",
                    single_manip,
                    single_grip,
                )
        else:
            if nm not in static_cfg:
                known = ", ".join(sorted(static_cfg.keys() | {"wrist"}))
                raise ValueError(f"Unknown camera name '{nm}'. Known: {known}")
            static_map[nm] = nm

    return CamerasOptions(static=static_map, dynamic=dynamic_map, modalities=modalities)


def _mk_sim(kw: dict, existing: SimOptions | None) -> SimOptions:
    if isinstance(existing, SimOptions):
        return existing

    ctrl = kw.get("control_hz", SimOptions().control_hz)
    perf = kw.get("performance_mode", SimOptions().performance_mode)

    if "n_envs" in kw:
        nenv = kw["n_envs"]
    else:
        nenv = SimOptions().n_envs

    return SimOptions(
        control_hz=int(ctrl),
        performance_mode=bool(perf),
        n_envs=int(nenv),
    )


def _controller_specs_from_yaml() -> dict:
    """Read controllers.yaml and return the 'controllers' map:
    { controller_name: {param: value, ...}, ... }.
    """
    cfg = load_defaults("controllers")
    if not isinstance(cfg, dict):
        raise ValueError("controllers.yaml must be a mapping.")
    ctrls = cfg.get("controllers")
    if not isinstance(ctrls, dict):
        raise ValueError("controllers.yaml must contain a 'controllers' mapping.")
    return ctrls


def _materialize_controller_config(ctrl: ControllerOptions) -> ControllerOptions:
    """Merge YAML defaults for ctrl.name into ctrl.config (user wins).
    No aliasing or renaming is performed: YAML keys must match the
    controller __init__ signature exactly.
    """
    specs = _controller_specs_from_yaml()
    yaml_defaults = dict(specs.get(ctrl.name, {}))
    user_cfg = dict(ctrl.config or {})
    merged = {**yaml_defaults, **user_cfg}
    return ControllerOptions(name=ctrl.name, config=merged)


def _materialize_arm_controllers(arm: ArmOptions) -> None:
    if isinstance(arm.manipulator_controller, ControllerOptions):
        arm.manipulator_controller = _materialize_controller_config(
            arm.manipulator_controller,
        )
    if isinstance(arm.gripper_controller, ControllerOptions):
        arm.gripper_controller = _materialize_controller_config(arm.gripper_controller)


def _materialize_robot_controllers(ro: RobotOptions) -> RobotOptions:
    if ro.type_of_robot == "single" and isinstance(ro.single, ArmOptions):
        _materialize_arm_controllers(ro.single)
        return ro

    if ro.type_of_robot == "bimanual":
        if isinstance(ro.left, ArmOptions):
            _materialize_arm_controllers(ro.left)
        if isinstance(ro.right, ArmOptions):
            _materialize_arm_controllers(ro.right)
        return ro

    return ro


def _ctrl_from_name(name: str | None) -> ControllerOptions | None:
    """Build ControllerOptions(name, config) using YAML defaults for that controller.
    If name is None, return None (caller will keep dataclass defaults).
    """
    if name is None:
        return None
    specs = _controller_specs_from_yaml()
    params = dict(specs.get(name, {}))
    return ControllerOptions(name=name, config=params)


def _build_robot_options(kw: dict, existing: RobotOptions | None) -> RobotOptions:
    """Build a RobotOptions object from the flat API kwargs.

    Accepted flat keys:
      - manipulator: str | (str, str)         # REQUIRED
      - gripper:     str | (str, str) | None  # optional; scalar replicates for bimanual
      - arm_control: str | None               # optional; exact name, no aliasing
      - gripper_control: str | None           # optional; exact name, no aliasing
      - layout_preset: str | None             # optional; prefer dataclass defaulting

    Rules:
        - If existing is a RobotOptions instance, it is returned unchanged.
        - manipulator must be present. A pair selects bimanual; a scalar selects single.
        - Layout is stored on robot.layout and is not passed directly to the env.
    """
    if isinstance(existing, RobotOptions):
        return existing

    manip = kw.get("manipulator")
    grip = kw.get("gripper")
    arm_ctrl_name = kw.get("arm_control")
    grip_ctrl_name = kw.get("gripper_control")
    layout_preset = kw.get("layout")
    if manip is None:
        raise ValueError("Missing required 'manipulator' argument.")

    manip_t = _as_tuple(manip)
    defaults = ArmOptions()

    # ---------- SINGLE ----------
    if len(manip_t) == 1:
        # Normalize gripper form if a tuple/list accidentally provided
        if isinstance(grip, (tuple, list)):
            grip = grip[0]
        single = ArmOptions(
            manipulator=str(manip_t[0]),
            gripper=grip,
            manipulator_controller=_ctrl_from_name(arm_ctrl_name)
            or defaults.manipulator_controller,
            gripper_controller=_ctrl_from_name(grip_ctrl_name)
            or defaults.gripper_controller,
        )
        # Layout for single is carried by robot.layout (dataclass default PoseOptions)
        return RobotOptions(type_of_robot="single", single=single)

    # ---------- BIMANUAL ----------
    if len(manip_t) == 2:
        if isinstance(grip, (tuple, list)):
            if len(grip) != 2:
                raise ValueError(
                    "For bimanual, 'gripper' must be a string (replicated) or a length-2 pair.",
                )
            grip_pair = (str(grip[0]), str(grip[1]))
        else:
            grip_pair = (grip, grip)  # replicate None or str

        left = ArmOptions(
            manipulator=str(manip_t[0]),
            gripper=grip_pair[0],
            manipulator_controller=_ctrl_from_name(arm_ctrl_name)
            or defaults.manipulator_controller,
            gripper_controller=_ctrl_from_name(grip_ctrl_name)
            or defaults.gripper_controller,
        )
        right = ArmOptions(
            manipulator=str(manip_t[1]),
            gripper=grip_pair[1],
            manipulator_controller=_ctrl_from_name(arm_ctrl_name)
            or defaults.manipulator_controller,
            gripper_controller=_ctrl_from_name(grip_ctrl_name)
            or defaults.gripper_controller,
        )

        layout = (
            LayoutOptions(preset=layout_preset)
            if isinstance(layout_preset, str)
            else LayoutOptions()
        )

        return RobotOptions(
            type_of_robot="bimanual",
            left=left,
            right=right,
            layout=layout,
        )

    raise ValueError(
        "manipulator must be a string (single) or a length-2 pair (bimanual).",
    )


def _coerce_components(
    kw_in: dict,
) -> tuple[RobotOptions, CamerasOptions, SimOptions, str | None]:
    """Return resolved component options for environment construction.

    Returns:
        Tuple of (robot, cameras, sim, render_mode).

    Precedence: explicit dataclass args > flat values > dataclass defaults.
    """
    kw = dict(kw_in)

    # Pull explicit component dataclasses if present
    robot_in = kw.get("robot")
    cameras_in = kw.get("cameras")
    layout_in = kw.get("layout")
    sim_in = kw.get("sim")

    # Enforce exclusivity: you can pass robot=... OR manipulator/gripper/..., not both
    flat_keys = ("manipulator", "gripper", "arm_control", "gripper_control")
    if isinstance(robot_in, RobotOptions) and any(
        kw.get(k) is not None for k in flat_keys
    ):
        raise ValueError(
            "Provide either 'robot=RobotOptions(...)' OR the flat robot fields "
            "(manipulator, gripper, arm_control, gripper_control) - not both.",
        )

    # Robot (and its layout)
    robot = _build_robot_options(kw, robot_in)
    if isinstance(layout_in, LayoutOptions):
        # Allow caller to override robot.layout via a separate LayoutOptions
        robot.layout = layout_in
        # Re-validate layout constraints (RobotOptions.__post_init__ only runs on construction).
        robot.__post_init__()
    elif isinstance(layout_in, str):
        if robot.type_of_robot == "single":
            raise ValueError(
                "Single-arm robots do not use layout presets. "
                "Use layout=LayoutOptions(single=PoseOptions(...)) or set robot.layout.single.",
            )
        robot.layout = LayoutOptions(preset=layout_in)
        robot.__post_init__()

    robot = _materialize_robot_controllers(robot)

    # Cameras (uses robot to resolve dynamic wrist presets)
    cameras = _mk_cameras(
        kw,
        cameras_in if isinstance(cameras_in, CamerasOptions) else None,
        robot,
    )

    # Sim & render mode
    sim = _mk_sim(kw, sim_in)
    render_mode = kw.get("render_mode")

    return robot, cameras, sim, render_mode


def make(task: str, /, **kw):
    """Two ways to build an environment (options-first):

    1) Flat API (still allowed):
        env = ds.make(
            "stack",
            manipulator="franka", gripper="robotiq",
            arm_control="osc_pose", gripper_control="joint_position",
            cameras=["front","wrist"], modalities=("rgb",),
            render_mode="human"
        )

    2) Component API (preferred):
        env = ds.make(
            "reach",
            sim=SimOptions(control_hz=100),
            robot=RobotOptions(...),   # carries robot.layout internally
            cameras=CamerasOptions(modalities=("rgb",)),
            render_mode="human",
        )
    """  # noqa: D415
    kw = _normalize_make_kwargs(kw)
    _lazy_init_genesis()
    env_cls = ENV_REG[task.lower()]

    robot, cameras, sim, render_mode = _coerce_components(kw)

    # Introspect env signature
    sig = inspect.signature(env_cls)
    accepted = set(sig.parameters.keys())
    call: dict[str, Any] = {}

    # Preferred: pass modern component signature
    if "robot" in accepted:
        call["robot"] = robot
    if "cameras" in accepted:
        call["cameras"] = cameras
    if "sim" in accepted:
        call["sim"] = sim
    if "render_mode" in accepted:
        call["render_mode"] = render_mode

    # If env requires explicit low-level timing knobs (legacy), derive from sim
    if "sim_dt" in accepted and "sim_dt" not in call:
        call["sim_dt"] = 1.0 / float(sim.control_hz)
    if "substeps" in accepted and "substeps" not in call:
        call["substeps"] = 1
    if "horizon" in accepted and "horizon" not in call:
        call["horizon"] = 200

    with _ensure_stderr_fileno():
        return env_cls(**call)
