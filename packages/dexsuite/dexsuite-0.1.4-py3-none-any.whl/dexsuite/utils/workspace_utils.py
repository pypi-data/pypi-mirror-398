"""Utilities for computing the world-frame AABB of the robot workspace."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Union

import genesis as gs
import numpy as np
import torch

from dexsuite.options import ArmOptions, PoseOptions, RobotOptions
from dexsuite.utils.aabb import AABB
from dexsuite.utils.orientation_utils import rpy_to_quat

Vec3 = Union[Sequence[float], np.ndarray, torch.Tensor]


def aabb_corners(min_pt: Vec3, max_pt: Vec3) -> np.ndarray:
    """Return the 8 corner points of an axis-aligned box defined by two opposite corners.

    This function accepts 3D vectors in NumPy array or PyTorch tensor format
    (on any device) and returns the coordinates of the 8 vertices of the AABB.

    Args:
        min_pt: The minimum corner point of the AABB (3 elements).
        max_pt: The maximum corner point of the AABB (3 elements).

    Returns:
        np.ndarray: A NumPy array of shape (8, 3) containing the 8 corner
            coordinates, with dtype float32.
    """

    def _to_np3(x: Vec3) -> np.ndarray:
        if isinstance(x, torch.Tensor):
            x = x.detach().cpu().numpy()
        x = np.asarray(x, dtype=np.float32).reshape(
            3,
        )
        return x

    lo = _to_np3(min_pt)
    hi = _to_np3(max_pt)

    xs = [lo[0], hi[0]]
    ys = [lo[1], hi[1]]
    zs = [lo[2], hi[2]]

    corners = np.array(
        [
            [xs[0], ys[0], zs[0]],
            [xs[1], ys[0], zs[0]],
            [xs[0], ys[1], zs[0]],
            [xs[1], ys[1], zs[0]],
            [xs[0], ys[0], zs[1]],
            [xs[1], ys[0], zs[1]],
            [xs[0], ys[1], zs[1]],
            [xs[1], ys[1], zs[1]],
        ],
        dtype=np.float32,
    )
    return corners


def add_corner_markers(
    scene: gs.Scene,
    corners: np.ndarray,
    radius: float = 0.01,
) -> list:
    """Add a small fixed, non-colliding sphere at each corner.

    Args:
        scene: The Genesis simulation scene to which the markers will be added.
        corners: A numpy array of shape (N, 3) where N is the number of corners.
        radius: The radius of the sphere marker in meters. Defaults to 0.01.

    Returns:
        list: A list of the created Genesis entities (sphere markers).
    """
    corners = np.asarray(corners, dtype=np.float32).reshape(-1, 3)
    ents = []
    for p in corners:
        morph = gs.morphs.Sphere(
            pos=(float(p[0]), float(p[1]), float(p[2])),
            radius=radius,
            fixed=True,
            visualization=True,
            collision=False,
        )
        ent = scene.add_entity(
            morph,
            material=gs.materials.Rigid(gravity_compensation=1.0),
        )
        ents.append(ent)
    return ents


def draw_workspace_corners(
    scene: gs.Scene,
    aabb: AABB | None,
    radius: float = 0.01,
) -> list:
    """Draws visual sphere markers at the corners of a world-frame AABB.

    This function computes the 8 corners of the AABB defined by the min/max
    extents and adds fixed, non-colliding sphere markers to the scene.

    Args:
        scene: The Genesis simulation scene.
        aabb: The world-frame AABB to visualize (or None).
        radius: The radius of the corner markers in meters. Defaults to 0.01.

    Returns:
        list: A list of the created Genesis entities (sphere markers).
            Returns an empty list if aabb is None.
    """
    if aabb is None:
        return []
    corners = aabb_corners(aabb.min, aabb.max)
    return add_corner_markers(scene, corners, radius=radius)


def _pose_quat_wxyz(pose: PoseOptions | None) -> tuple[float, float, float, float]:
    """Extracts the base quaternion (w, x, y, z) from PoseOptions, handling RPY."""
    if pose is None:
        return (1.0, 0.0, 0.0, 0.0)

    if pose.quat is not None:
        w, x, y, z = pose.quat
        return (float(w), float(x), float(y), float(z))

    # If only yaw_rad is provided, convert RPY (0, 0, yaw) to quaternion
    q = rpy_to_quat(torch.tensor([0.0, 0.0, float(pose.yaw_rad)]))
    return tuple(map(float, q.tolist()))


def _arm_world_aabb(
    arm: ArmOptions | None,
    pose: PoseOptions | None,
    device: torch.device,
) -> AABB | None:
    """Compute the world-frame AABB for a single arm, if defined."""
    if arm is None or arm.workspace is None or pose is None:
        return None

    local = AABB.from_lists(arm.workspace.min, arm.workspace.max)
    world = local.transform_by_base(
        base_pos=pose.pos,
        base_quat_wxyz=_pose_quat_wxyz(pose),
    )
    # Ensure tensors are on the requested device
    return AABB.from_tensors(world.min.to(device), world.max.to(device))


def compute_world_aabb_from_options(
    ro: RobotOptions,
    device: torch.device,
) -> dict[str, AABB | None]:
    """Build world-frame workspaces (union + per-arm) for the robot.

    Returns a dict with keys: "union", "left", "right", "overlap".
    For single-arm robots, left/right/overlap are None and union is the
    single workspace. For bimanual robots, union is the box covering both
    arms, and overlap is the intersection (or None if disjoint).
    """
    if ro.type_of_robot == "bimanual":
        return compute_bimanual_world_aabbs(ro, device)

    single = _arm_world_aabb(ro.single, ro.layout.single, device)
    return {"union": single, "left": None, "right": None, "overlap": None}


def compute_bimanual_world_aabbs(
    ro: RobotOptions,
    device: torch.device,
) -> dict[str, AABB | None]:
    """Return per-arm, overlap, and union AABBs for bimanual robots.

    For single-arm robots, left/right are None and union is the single-arm AABB.
    """
    if ro.type_of_robot != "bimanual":
        single = _arm_world_aabb(ro.single, ro.layout.single, device)
        return {"left": None, "right": None, "overlap": None, "union": single}

    left = _arm_world_aabb(ro.left, ro.layout.left, device)
    right = _arm_world_aabb(ro.right, ro.layout.right, device)

    if left is None and right is None:
        return {"left": None, "right": None, "overlap": None, "union": None}
    if left is None:
        return {"left": None, "right": right, "overlap": None, "union": right}
    if right is None:
        return {"left": left, "right": None, "overlap": None, "union": left}

    union = left.union(right)
    overlap = left.intersection(right)
    return {"left": left, "right": right, "overlap": overlap, "union": union}


def outside_aabb(pos: torch.Tensor, aabb_min: AABB, aabb_max: AABB) -> torch.Tensor:
    """Return whether the given position tensor is outside of its own AABB.

    Args:
        pos: The position of the calling AABB object
        aabb_min: minimum boundary of the AABB
        aabb_max: maximum boundary of the AABB

    Returns:
        Tensor with bool value.

    """
    aabb_min.to(pos.device)
    aabb_max.to(pos.device)

    lower_cond = torch.any(pos < aabb_min, dim=-1)
    upper_cond = torch.any(pos > aabb_max, dim=-1)
    return lower_cond | upper_cond
