"""Camera system integration for DexSuite (Genesis backend).

This module provides the CameraSystem helper used by environments to create and
render static and dynamic cameras. Dynamic cameras can be attached to robot
links (for example, gripper-mounted wrist cameras) and support bimanual robots
by expanding camera names across left and right sides.
"""

from __future__ import annotations

import genesis as gs
import numpy as np
import torch
from gymnasium import spaces

from dexsuite.options import CamerasOptions, DynamicCamOptions, StaticCamOptions
from dexsuite.utils import get_n_envs
from dexsuite.utils.options_utils import load_defaults


class CameraSystem:
    """Manages static and dynamic cameras within the simulation scene.

    This system handles the creation, mounting, and rendering of two types of
    cameras:
    1. Static: Fixed positions and orientations in the world.
    2. Dynamic: Attached to a specific link on the robot, typically the gripper
       root link.

    It automatically detects bimanual robots and mounts dynamic cameras to both
    grippers, expanding names to avoid collisions.

    Attributes:
        scene: The gs.Scene object to which cameras are added.
        robot: The robot model (for example, ModularRobot or IntegratedRobot).
        gui: Whether to create cameras with GUI visualization enabled.
        cam_options: CamerasOptions specifying all camera configurations.
    """

    def __init__(
        self,
        scene: gs.Scene,
        robot,
        cam_options: CamerasOptions,
        gui: bool = False,
    ) -> None:
        """Initializes the CameraSystem.

        Args:
            scene: The gs.Scene object.
            robot: The robot model to attach dynamic cameras to.
            cam_options: Configuration dataclass for static and dynamic cameras.
            gui: Whether to enable camera visualization in the GUI.
        """
        self.scene: gs.Scene = scene
        self.robot = robot
        self.gui = gui
        self.cam_options = cam_options

        # camera name -> (gs.Camera, modality_flags)
        self._cams: dict[str, tuple[gs.Camera, dict[str, bool]]] = {}
        # camera name -> (gs.Camera, DynamicCamOptions, hand_ent, root_link)
        self._dyn_specs: dict[
            str,
            tuple[gs.Camera, DynamicCamOptions, gs.Entity, str],
        ] = {}

    @property
    def num_cameras(self) -> int:
        return len(self._cams)

    # ---------------- helpers: enumerate grippers ----------------

    def _all_grippers(self) -> list[tuple[str, gs.Entity, str, object, object]]:
        """Enumerates all grippers present on the robot.

        Detects bimanual setups (robot.left, robot.right) first,
        then falls back to a single-arm setup (robot.hand_ent).

        - ModularRobot: hand_ent is the separate gripper entity; gripper_obj is a GripperModel.
        - IntegratedRobot: hand_ent == arm_ent; gripper_obj is the _HandProxy.
        - Bimanual: we detect 'left'/'right' sub-robots automatically.

        Returns:
            A list of tuples, where each tuple contains:
            (label, hand_ent, root_link_name, manip_obj, gripper_obj).
            - label (str): 'left', 'right', or 'arm'.
            - hand_ent (gs.Entity): The entity containing the gripper.
            - root_link_name (str): Name of the gripper's root link.
            - manip_obj (object): The manipulator object (e.g., arm).
            - gripper_obj (object): The gripper object.

        Raises:
            RuntimeError: If no grippers could be found on the robot.
        """
        out: list[tuple[str, gs.Entity, str, object, object]] = []

        # Bimanual (preferred if present)
        if hasattr(self.robot, "left") and hasattr(self.robot, "right"):
            for side in ("left", "right"):
                side_obj = getattr(self.robot, side)
                if (
                    hasattr(side_obj, "hand_ent")
                    and hasattr(side_obj, "gripper")
                    and hasattr(side_obj.gripper, "root_link")
                ):
                    out.append(
                        (
                            side,
                            side_obj.hand_ent,
                            side_obj.gripper.root_link,
                            side_obj.manip,
                            side_obj.gripper,
                        ),
                    )

        # Single-arm (modular or integrated) at top-level
        elif (
            hasattr(self.robot, "hand_ent")
            and hasattr(self.robot, "gripper")
            and hasattr(self.robot.gripper, "root_link")
        ):
            out.append(
                (
                    "arm",
                    self.robot.hand_ent,
                    self.robot.gripper.root_link,
                    getattr(self.robot, "manip", None),
                    self.robot.gripper,
                ),
            )

        if not out:
            raise RuntimeError(
                "CameraSystem: could not find any gripper(s) on the robot.",
            )
        return out

    @staticmethod
    def _norm_id(obj, fallback: str) -> str:
        """Gets a normalized string identifier for an object.

        Used for matching camera presets in YAML configuration.
        The identifier is derived first from _registry_name if available,
        otherwise from the object's class name. It is then lowercased
        and stripped of whitespace.

        Args:
            obj: The object to identify.
            fallback: A fallback string if the class name is also unavailable.

        Returns:
            A normalized, lowercase string identifier.
        """
        rid = getattr(obj, "_registry_name", None)
        name = rid or obj.__class__.__name__ or fallback
        return str(name).strip().lower()

    # ---------------- helpers: resolve preset -> DynamicCamOptions ----------------

    @staticmethod
    def _parse_bimanual_side(cam_name: str) -> str | None:
        """Infer bimanual side from a camera name.

        Supports both prefix and suffix conventions:
        - Prefix: left_<name> or right_<name>
        - Suffix: <name>_left or <name>_right

        Args:
            cam_name: Camera name key.

        Returns:
            "left" or "right" if the name is side-specific, otherwise None.
        """
        s = str(cam_name).strip().lower()
        if s.startswith("left_") or s.endswith("_left"):
            return "left"
        if s.startswith("right_") or s.endswith("_right"):
            return "right"
        return None

    def _resolve_dynamic_spec(
        self,
        entry: DynamicCamOptions | str,
        manip_obj,
        gripper_obj,
    ) -> DynamicCamOptions:
        r"""Resolves a dynamic camera entry into a concrete DynamicCamOptions.

        If entry is already a DynamicCamOptions, it is returned directly. If
        entry is a string, it is treated as a preset name and looked up in the
        cameras.yaml defaults.

        The selection logic for presets is:
        1. If modular gripper (has _registry_name): Try preset[\"by\"][gripper_id].
        2. If integrated (no _registry_name): Try preset[\"by\"][manip_id].
        3. Fallback: Use preset[\"default\"].

        Args:
            entry: A DynamicCamOptions instance or a string preset name.
            manip_obj: The manipulator object (for integrated matching).
            gripper_obj: The gripper object (for modular matching).

        Returns:
            A concrete DynamicCamOptions instance with resolved settings.

        Raises:
            TypeError: If entry is not a DynamicCamOptions or a string.
            ValueError: If the preset string is not found or if a
                matching 'by' or 'default' block is missing in the preset.
        """
        if isinstance(entry, DynamicCamOptions):
            return entry  # already concrete

        if not isinstance(entry, str):
            raise TypeError(
                "Dynamic camera entry must be a DynamicCamOptions or a preset string.",
            )

        cfg = load_defaults("cameras")
        dyn = cfg.get("dynamic", {})
        preset = dyn.get(entry)
        if not isinstance(preset, dict):
            raise ValueError(
                f"Dynamic preset '{entry}' not found under 'dynamic' in cameras.yaml.",
            )

        # Read fields
        fov = float(preset.get("fov", 60.0))
        res = tuple(preset.get("res", (224, 224)))

        # Matching keys
        by_map = {
            str(k).strip().lower(): v for k, v in (preset.get("by") or {}).items()
        }
        default = preset.get("default") or {}

        # Decide modular vs integrated
        has_modular_grip_id = hasattr(gripper_obj, "_registry_name")
        choice = None
        if has_modular_grip_id:
            gid = self._norm_id(gripper_obj, "gripper")
            choice = by_map.get(gid)
        else:
            mid = self._norm_id(manip_obj, "manip")
            choice = by_map.get(mid)

        if choice is None:
            choice = default
        if not choice:
            raise ValueError(
                "Dynamic preset must provide either a matching 'by' entry or a 'default' block.",
            )

        pos = tuple(choice.get("pos_offset", (0.0, 0.0, 0.0)))
        quat = tuple(choice.get("quat_offset", (1.0, 0.0, 0.0, 0.0)))

        return DynamicCamOptions(
            link=None,
            pos_offset=pos,
            quat_offset=quat,
            fov=fov,
            res=res,
        )

    # ---------------- lifecycle ----------------

    def create(self) -> None:
        r"""Create all static and dynamic cameras.

        Static cameras are created exactly as defined in cam_options.static.

        Dynamic cameras are attached to discovered grippers:
        - Single-arm: each dynamic entry creates exactly one camera.
        - Bimanual:
          - Generic names (for example, \"wrist\") expand to \"left_wrist\" and
            \"right_wrist\".
          - Side-specific names using a left_ or right_ prefix (or _left/_right
            suffix) are created only for the matching side.
        """
        enabled = set(self.cam_options.modalities)
        flags = {
            "depth": "depth" in enabled,
            "segmentation": "segmentation" in enabled,
            "normal": "normal" in enabled,
        }

        # Static
        for name, spec in self.cam_options.static.items():
            if not isinstance(spec, StaticCamOptions):
                raise TypeError("Static entries must be StaticCamOptions.")
            cam = self.scene.add_camera(
                pos=tuple(spec.pos),
                lookat=tuple(spec.lookat),
                fov=float(spec.fov),
                res=tuple(spec.res),
                GUI=self.gui,
            )
            self._cams[name] = (cam, flags)

        # Dynamic
        grippers = self._all_grippers()
        by_label: dict[str, tuple[gs.Entity, str, object, object]] = {
            label: (hand_ent, root_link, manip_obj, gripper_obj)
            for (label, hand_ent, root_link, manip_obj, gripper_obj) in grippers
        }
        is_bimanual = "left" in by_label and "right" in by_label

        for req_name, entry in self.cam_options.dynamic.items():
            if is_bimanual:
                side = self._parse_bimanual_side(req_name)
                if side in ("left", "right"):
                    targets = [(req_name, side)]
                else:
                    targets = [
                        (f"left_{req_name}", "left"),
                        (f"right_{req_name}", "right"),
                    ]
            else:
                # Single-arm: attach to the only discovered gripper (label is usually "arm")
                targets = [(req_name, grippers[0][0])]

            for name, label in targets:
                if name in self._cams:
                    raise ValueError(f"Duplicate camera name '{name}'.")
                if label not in by_label:
                    raise ValueError(
                        f"Dynamic camera '{name}' targets unknown gripper label '{label}'.",
                    )

                hand_ent, root_link, manip_obj, gripper_obj = by_label[label]
                spec = self._resolve_dynamic_spec(entry, manip_obj, gripper_obj)

                cam = self.scene.add_camera(
                    pos=(0.0, 0.0, 0.0),
                    lookat=(0.0, 0.0, 0.0),
                    fov=float(spec.fov),
                    res=tuple(spec.res),
                    GUI=self.gui,
                )
                self._cams[name] = (cam, flags)
                self._dyn_specs[name] = (cam, spec, hand_ent, root_link)

    def _resolve_gripper_anchor(self, cam_name: str):
        # bimanual
        if hasattr(self.robot, "left") and hasattr(self.robot, "right"):
            side = (
                "left"
                if cam_name.startswith("left_")
                else ("right" if cam_name.startswith("right_") else None)
            )
            if side is None:
                # If someone forgot to prefix, default to 'left' for deterministic behavior
                side = "left"
            side_obj = getattr(self.robot, side)
            hand_ent = side_obj.hand_ent
            root_link = side_obj.gripper.root_link
            return hand_ent, root_link

        # single (modular or integrated)
        hand_ent = self.robot.hand_ent
        root_link = self.robot.gripper.root_link
        return hand_ent, root_link

    @staticmethod
    def _normalize_quat_wxyz(q):
        q = np.asarray(q, dtype=np.float64)
        n = np.linalg.norm(q)
        if not np.isfinite(n) or n <= 0:
            return np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)
        return q / n

    def mount(self) -> None:
        """Attach dynamic cams to the gripper root_link (per env)."""
        B = get_n_envs()

        for _name, (cam, spec, hand_ent, root_link) in self._dyn_specs.items():
            link_obj = hand_ent.get_link(root_link)

            px, py, pz = map(float, spec.pos_offset)
            w, x, y, z = self._normalize_quat_wxyz(spec.quat_offset)

            # link->camera transform
            xx, yy, zz = x * x, y * y, z * z
            xy, xz, yz = x * y, x * z, y * z
            wx, wy, wz = w * x, w * y, w * z
            R = np.array(
                [
                    [1.0 - 2.0 * (yy + zz), 2.0 * (xy - wz), 2.0 * (xz + wy)],
                    [2.0 * (xy + wz), 1.0 - 2.0 * (xx + zz), 2.0 * (yz - wx)],
                    [2.0 * (xz - wy), 2.0 * (yz + wx), 1.0 - 2.0 * (xx + yy)],
                ],
                dtype=np.float64,
            )
            T = np.eye(4, dtype=np.float64)
            T[:3, :3] = R
            T[:3, 3] = np.array([px, py, pz], dtype=np.float64)

            if B > 1:
                for env_id in range(B):
                    cam.attach(link_obj, T)  # <-- per-env attach is critical
            else:
                cam.attach(link_obj, T)

    def obs_space(self) -> dict[str, spaces.Dict]:
        r"""Builds the Gymnasium observation space for all cameras.

        The space is a dictionary mapping camera names to spaces.Dict objects.
        Each per-camera dictionary maps modality names (for example, \"rgb\" and
        \"depth\") to a spaces.Box.

        The shapes and data types are as follows:

        Shapes (B = number of environments, H = height, W = width):
            - single env (B=1):
                - rgb/normal: (H, W, 3)
                - depth/seg: (H, W)
            - batched (B>1):
                - rgb/normal: (B, H, W, 3)
                - depth/seg: (B, H, W)

        Dtypes:
            - rgb: uint8 [0..255]
            - depth: float32 [0..+inf)
            - segmentation: int32 [0..INT32_MAX]
            - normal: float32 [-1..1]

        Returns:
            dict[str, spaces.Dict]: Observation space for all cameras and modalities.
        """
        B = get_n_envs()
        enabled = set(self.cam_options.modalities)
        want_depth = "depth" in enabled
        want_seg = "segmentation" in enabled
        want_norm = "normal" in enabled

        def shape_hw(res_hw: tuple[int, int], channels: int | None) -> tuple[int, ...]:
            # Genesis camera resolution is configured as (W, H) but returns arrays as (H, W[, C]).
            W, H = int(res_hw[0]), int(res_hw[1])
            if B > 1:
                return (B, H, W, channels) if channels else (B, H, W)
            else:
                return (H, W, channels) if channels else (H, W)

        cams: dict[str, spaces.Dict] = {}

        # static cameras
        for name, spec in getattr(self.cam_options, "static", {}).items():
            if not isinstance(spec, StaticCamOptions):
                continue
            items = {
                "rgb": spaces.Box(0, 255, shape=shape_hw(spec.res, 3), dtype=np.uint8),
            }
            if want_depth:
                items["depth"] = spaces.Box(
                    0.0,
                    np.inf,
                    shape=shape_hw(spec.res, None),
                    dtype=np.float32,
                )
            if want_seg:
                items["segmentation"] = spaces.Box(
                    0,
                    np.iinfo(np.int32).max,
                    shape=shape_hw(spec.res, None),
                    dtype=np.int32,
                )
            if want_norm:
                items["normal"] = spaces.Box(
                    -1.0,
                    1.0,
                    shape=shape_hw(spec.res, 3),
                    dtype=np.float32,
                )
            cams[name] = spaces.Dict(items)

        # dynamic cameras (resolved + expanded in create())
        for name, (_cam, spec, _hand_ent, _root_link) in self._dyn_specs.items():
            items = {
                "rgb": spaces.Box(0, 255, shape=shape_hw(spec.res, 3), dtype=np.uint8),
            }
            if want_depth:
                items["depth"] = spaces.Box(
                    0.0,
                    np.inf,
                    shape=shape_hw(spec.res, None),
                    dtype=np.float32,
                )
            if want_seg:
                items["segmentation"] = spaces.Box(
                    0,
                    np.iinfo(np.int32).max,
                    shape=shape_hw(spec.res, None),
                    dtype=np.int32,
                )
            if want_norm:
                items["normal"] = spaces.Box(
                    -1.0,
                    1.0,
                    shape=shape_hw(spec.res, 3),
                    dtype=np.float32,
                )
            cams[name] = spaces.Dict(items)

        return cams

    def render_all(self) -> dict[str, dict[str, torch.Tensor]]:
        """Renders all requested modalities from all cameras.

        The output shapes come directly from Genesis (no extra massaging).

        Returns:
            A dictionary mapping camera names (str) to results.
            Each result is a dictionary mapping modality name
            (e.g., 'rgb', 'depth') to a torch.Tensor containing
            the rendered data.
        """
        enabled = tuple(self.cam_options.modalities)
        use_depth = "depth" in enabled
        use_seg = "segmentation" in enabled
        use_norm = "normal" in enabled

        out: dict[str, dict[str, torch.Tensor]] = {}
        for name, (cam, _spec) in self._cams.items():
            frames = cam.render(depth=use_depth, segmentation=use_seg, normal=use_norm)
            rgb = frames[0]
            dep = frames[1] if len(frames) > 1 else None
            seg = frames[2] if len(frames) > 2 else None
            norm = frames[3] if len(frames) > 3 else None

            pack: dict[str, torch.Tensor] = {}
            pack["rgb"] = torch.from_numpy(np.ascontiguousarray(rgb))
            if use_depth and dep is not None:
                pack["depth"] = torch.from_numpy(np.ascontiguousarray(dep))
            if use_seg and seg is not None:
                pack["segmentation"] = torch.from_numpy(np.ascontiguousarray(seg))
            if use_norm and norm is not None:
                pack["normal"] = torch.from_numpy(np.ascontiguousarray(norm))
            out[name] = pack
        return out
