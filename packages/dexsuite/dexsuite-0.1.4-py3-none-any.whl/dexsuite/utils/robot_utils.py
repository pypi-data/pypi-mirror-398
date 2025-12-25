"""Robot-facing utility functions (Genesis integration).

This module contains helpers that depend on Genesis (genesis), such as morph
construction and querying link poses. Keep imports from this module explicit to
avoid pulling heavy dependencies into lightweight contexts.
"""

from __future__ import annotations

import genesis as gs
import numpy as np
import torch

from dexsuite.core.components.base import RigidBodyModel
from dexsuite.core.components.mount import GripperMount
from dexsuite.utils.globals import get_device
from dexsuite.utils.orientation_utils import (
    rpy_to_quat_wxyz_torch,
)


def create_mount_morph(
    mount: GripperMount,
) -> gs.morphs.Cylinder | gs.morphs.Box | None:
    """Creates a Genesis morphology for a gripper mount.

    Based on the mount's type, this function constructs either a Cylinder
    or a Box morphology. If the mount type is 'invisible', it returns None.

    Args:
        mount: The GripperMount configuration object.

    Returns:
        A Genesis Cylinder or Box morph, or None if the mount is invisible.

    Raises:
        ValueError: If the mount_type is unknown.
    """
    if mount.mount_type == "invisible":
        return None

    # Convert tensors to CPU numpy arrays for Genesis constructors
    # pos_np = mount.mount_pos.cpu().numpy().astype(np.float32)
    # quat_np = mount.mount_quat.cpu().numpy().astype(np.float32)
    pos_np = mount.mount_pos.cpu().numpy().astype(np.float32)
    quat_np = mount.mount_quat.cpu().numpy().astype(np.float32)

    if mount.mount_type == "cylinder":
        return gs.morphs.Cylinder(
            pos=pos_np,
            quat=quat_np,
            radius=mount.geometry["radius"],
            height=mount.geometry["height"],
            fixed=True,
        )

    elif mount.mount_type == "box":
        sx, sy, sz = mount.geometry["size"]
        return gs.morphs.Box(
            pos=pos_np,
            quat=quat_np,
            size=(sx, sy, sz),
            fixed=True,
        )
    else:
        raise ValueError(f"Unknown mount type: '{mount.mount_type}'")


def rpy_to_quat(rpy: torch.Tensor) -> torch.Tensor:
    """Converts roll, pitch, yaw Euler angles to a quaternion (w, x, y, z).

    Args:
        rpy: A tensor of shape (..., 3) representing [roll, pitch, yaw] in
            radians.

    Returns:
        A tensor of shape (..., 4) representing quaternions in (w, x, y, z)
            order.
    """
    return rpy_to_quat_wxyz_torch(rpy).to(get_device(), dtype=torch.float32)


def get_robot_morph(
    robot_model: RigidBodyModel,
    **kwargs,
) -> gs.morphs.URDF | gs.morphs.MJCF:
    """Creates a Genesis morphology (MJCF or URDF) from a robot model.

    Args:
        robot_model: The RigidBodyModel instance defining the robot.
        kwargs: Additional keyword arguments passed to the morphology constructor
            (for example, base position pos, orientation quat).

    Returns:
        A Genesis MJCF or URDF morph instance.

    Raises:
        ValueError: If the model file extension is not supported (.xml or .urdf).
    """
    if "pos" in kwargs and isinstance(kwargs["pos"], torch.Tensor):
        kwargs["pos"] = kwargs["pos"].cpu().numpy().astype(np.float32)
    if "quat" in kwargs and isinstance(kwargs["quat"], torch.Tensor):
        kwargs["quat"] = kwargs["quat"].cpu().numpy().astype(np.float32)

    robot_morph = None
    if robot_model.model_path.endswith(".xml"):
        robot_morph = gs.morphs.MJCF(file=robot_model.model_path, **kwargs)
    elif robot_model.model_path.endswith(".urdf") or robot_model.model_path.endswith(
        ".URDF",
    ):
        robot_morph = gs.morphs.URDF(file=robot_model.model_path, fixed=True, **kwargs)
    else:
        raise ValueError("The model file is not supported")
    return robot_morph


def get_end_effector_pose(
    entity,
    link_idx: int,
    qpos: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Compute forward kinematics for a given joint configuration.

    Args:
        entity: Genesis entity implementing forward_kinematics.
        link_idx: Link index local to entity.
        qpos: Joint positions with shape (dof,) or (B, dof).

    Returns:
        tuple[torch.Tensor, torch.Tensor]: (pos, quat) with shapes (3,) or (B, 3)
        and (4,) or (B, 4) respectively.
    """
    pos, quat = entity.forward_kinematics(
        qpos=qpos.contiguous(),
        links_idx_local=[link_idx],
    )
    pos = pos.contiguous()
    quat = quat.contiguous()
    return pos, quat


def get_tool_center_point_pose(
    robot,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Gets the world pose of the Tool Center Point (TCP).

    Retrieves the pose either from a dedicated TCP anchor entity/link if it
    exists, or defaults to the pose of the gripper's root link.

    Note: This function assumes the robot object structure includes attributes
        like _tcp_axis_ent, _tcp_axis_link_name, hand_ent, and gripper (with a
        root_link attribute).

    Args:
        robot: The robot instance (e.g., IntegratedRobot, ModularRobot).

    Returns:
        A tuple containing:
            - pos: Position tensor of shape (batch_size, 3).
            - quat: Quaternion tensor (w, x, y, z) of shape (batch_size, 4).
    """
    anchor_ent = getattr(robot, "_tcp_axis_ent", None)
    anchor_link_name = getattr(robot, "_tcp_axis_link_name", None)
    if anchor_ent is not None and anchor_link_name is not None:
        link = anchor_ent.get_link(anchor_link_name)
    else:
        link = robot.hand_ent.get_link(robot.gripper.root_link)

    pos = link.get_pos()
    quat = link.get_quat()

    return pos, quat


def attach_tcp_anchor(robot, visualize: bool = True) -> None:
    """Attaches a visual or invisible entity representing the TCP to the gripper.

    If the robot's gripper model defines a tcp_pose, this function creates
    a small entity (an axis mesh or a tiny box) at that pose relative to the
    gripper's root link. This anchor can be used for reliable TCP pose reads
    or visualization. The anchor entity and link name are stored on the robot
    object as _tcp_axis_ent and _tcp_axis_link_name.

    Args:
        robot: The robot instance. Expected attributes: gripper (with tcp_pose
            and root_link), device, scene, and hand_ent.
        visualize: If True, attaches a visible axis mesh. If False, attaches
            a tiny, effectively invisible box.
    """
    tcp_pose = getattr(robot.gripper, "tcp_pose", None)
    if tcp_pose is None:
        return

    dev = robot.device
    tcp = torch.as_tensor(tcp_pose, dtype=torch.float32, device=dev)
    tcp_pos = tcp[:3]
    tcp_rpy = tcp[3:]
    tcp_quat = rpy_to_quat(tcp_rpy)

    tcp_pos_np = tcp_pos.detach().cpu().numpy().astype(np.float32)
    tcp_quat_np = tcp_quat.detach().cpu().numpy().astype(np.float32)

    if visualize:
        morph = gs.morphs.Mesh(
            file="meshes/axis.obj",
            pos=tcp_pos_np,
            quat=tcp_quat_np,
            scale=0.1,
            fixed=True,
            collision=False,
        )
        surface = gs.surfaces.Default(color=(0.5, 1.0, 0.5, 1.0))
    else:
        morph = gs.morphs.Box(
            pos=tcp_pos_np,
            quat=tcp_quat_np,
            size=(1e-4, 1e-4, 1e-4),
            fixed=True,
            visualization=True,
            collision=False,
        )
        surface = None

    tcp_ent = robot.scene.add_entity(morph, surface=surface)
    robot.scene.link_entities(
        robot.hand_ent,
        tcp_ent,
        parent_link_name=robot.gripper.root_link,
        child_link_name=tcp_ent.links[0].name,
    )

    robot._tcp_axis_ent = tcp_ent
    robot._tcp_axis_link_name = tcp_ent.links[0].name


def grasp_observation(robot) -> dict[str, torch.Tensor]:
    """Computes grasp-related metrics for robot observations.

    Calculates the world positions of designated grasp tip links and the
    Euclidean distances between designated pinch pairs. Optimized to fetch
    link positions only once per call.

    Note: Assumes the robot object has gripper (with optional GRASP_TIPS and
        PINCH_PAIRS), hand_ent, and device attributes.

    Args:
        robot: The robot instance.

    Returns:
        A dictionary containing:
        - "grasp_tip_pos": Tensor of shape (n_envs, 3 times N_tips) with
            concatenated tip positions [x, y, z, ...]. Empty if no tips defined.
        - "pinch_widths": Tensor of shape (n_envs, M_pairs) with distances
            between pinch pairs. Empty if no pairs defined.
        - "pinch_min": Tensor of shape (n_envs, 1) with the minimum pinch
            width across all pairs (0 if no pairs).
    """
    tip_names = tuple(getattr(robot.gripper, "GRASP_TIPS", None) or ())
    pair_list = tuple(getattr(robot.gripper, "PINCH_PAIRS", None) or ())

    required = set(tip_names)
    for a, b in pair_list:
        required.add(a)
        required.add(b)

    link_positions: dict[str, torch.Tensor] = {}
    ent = robot.hand_ent
    ref_shape = None

    # 1) read link positions as-is from Genesis (keep (3,) or (B,3))
    for name in required:
        try:
            p = ent.get_link(name).get_pos()  # (3,) or (B,3)
            link_positions[name] = p.contiguous()
            ref_shape = p.shape  # remember first successful read
        except KeyError:
            pass

    # 2) infer batch-ness
    B = None
    batched = False
    if ref_shape is not None and len(ref_shape) == 2:
        batched, B = True, ref_shape[0]
    else:
        # fallback inference from a known batched signal, else assume single
        try:
            qpos_hand = ent.get_dofs_position()
            if qpos_hand.ndim == 2:
                batched, B = True, qpos_hand.shape[0]
        except Exception:
            pass

    # helpers to make zero tensors matching batch-ness
    def zeros_vec3():
        if batched:
            return torch.zeros((B, 3), dtype=torch.float32, device=robot.device)
        else:
            return torch.zeros((3,), dtype=torch.float32, device=robot.device)

    def zeros_like_last(width: int):
        if batched:
            return torch.zeros((B, width), dtype=torch.float32, device=robot.device)
        else:
            return torch.zeros((width,), dtype=torch.float32, device=robot.device)

    # 3) tips: concat along last dim -> (3*N) or (B, 3*N)
    if tip_names:
        tip_vecs = []
        for name in tip_names:
            tip_vecs.append(link_positions.get(name, zeros_vec3()))
        grasp_tip_pos = torch.cat(tip_vecs, dim=-1)
    else:
        grasp_tip_pos = zeros_like_last(0)

    # 4) pinch widths: per pair norm along last dim -> () or (B,)
    widths_list = []
    for a, b in pair_list:
        pa, pb = link_positions.get(a), link_positions.get(b)
        if pa is None or pb is None:
            # skip missing pairs; keeps behavior identical to your current code
            continue
        widths_list.append(torch.norm(pa - pb, dim=-1))

    if widths_list:
        pinch_widths = torch.stack(widths_list, dim=-1)  # (M,) or (B, M)
        pinch_min = torch.min(pinch_widths, dim=-1, keepdim=True).values
    else:
        pinch_widths = zeros_like_last(0)
        pinch_min = (
            torch.zeros((B, 1), dtype=torch.float32, device=robot.device)
            if batched
            else torch.zeros((1,), dtype=torch.float32, device=robot.device)
        )

    return {
        "grasp_tip_pos": grasp_tip_pos,
        "pinch_widths": pinch_widths,
        "pinch_min": pinch_min,
    }
