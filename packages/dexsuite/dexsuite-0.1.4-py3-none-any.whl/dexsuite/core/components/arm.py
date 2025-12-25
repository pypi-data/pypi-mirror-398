"""Models for robotic manipulators (arms) used in DexSuite.

This module defines common base classes for manipulators, including support
for modular arms (with swappable grippers via adapter catalogs) and
integrated arms (whose MJCF already includes a gripper).
"""

from __future__ import annotations

import inspect
from collections.abc import Sequence
from pathlib import Path

import torch

from dexsuite.core.components.base import RigidBodyModel
from dexsuite.utils import extract_grippermount_yaml


class ArmModel(RigidBodyModel):
    """Base class for all robotic manipulator models.

    This class provides a common interface for robotic arms. Subclasses must
    define essential properties like the model path, degrees of freedom (DoF),
    and key kinematic links.

    Note:
        Modular arms may supply a mount adapter catalog via a YAML file, while
        integrated arms must expose metadata for their built-in gripper.

    Attributes:
        end_link: The name of the end-effector link used for IK/OSC.
        root_link: The name of the link recommended for anchoring or placement.
        home_q: The nominal joint configuration (arm-only) as a torch.Tensor.
        kp: Optional per-joint proportional gains for controllers; shape=(dof,).
        kv: Optional per-joint derivative gains for controllers; shape=(dof,).
        force_range: Optional per-joint effort limits; shape=(dof,).
        q_lo: Optional lower joint limits; shape=(dof,).
        q_hi: Optional upper joint limits; shape=(dof,).
        _adapter_yaml: An optional path or filename of a YAML file that
            describes mount adapters for attaching grippers.
    """

    end_link: str
    root_link: str
    home_q: torch.Tensor

    kp: torch.Tensor | None = None
    kv: torch.Tensor | None = None
    force_range: torch.Tensor | None = None
    q_lo: torch.Tensor | None = None
    q_hi: torch.Tensor | None = None

    _adapter_yaml: str | None = None

    @classmethod
    def _load_adapter_yaml(cls) -> dict:
        """Locates and loads the mount-adapter YAML file.

        The method searches for the YAML file in the following order:
            1. The explicit path defined in _adapter_yaml.
            2. A file named <registry>_adapters.yaml if _registry_name is set.
            3. A file named <module>_adapters.yaml next to the class definition.

        Returns:
            A dictionary with the parsed adapter specification. Returns an empty
            dictionary if no file is found.
        """
        here = Path(inspect.getfile(cls))

        if cls._adapter_yaml:
            p = Path(cls._adapter_yaml)
            if not p.is_absolute():
                p = here.with_name(cls._adapter_yaml)
            if p.exists():
                return extract_grippermount_yaml(p)

        key = getattr(cls, "_registry_name", None)
        if key:
            p = here.with_name(f"{key.lower()}_adapters.yaml")
            if p.exists():
                return extract_grippermount_yaml(p)

        p = here.with_name(f"{here.stem}_adapters.yaml")
        if p.exists():
            return extract_grippermount_yaml(p)

        return {}


class ModularManipulatorModel(ArmModel):
    """A manipulator model with a flange for attaching different grippers.

    This represents an arm that does not have a built-in hand and requires a
    gripper to be attached separately.

    Attributes:
        has_builtin_gripper: Always False for this class.
    """

    has_builtin_gripper = False

    @property
    def adapters(self) -> dict[str, dict]:
        """Gets the adapter catalog for attaching grippers.

        The catalog maps gripper registry keys to their corresponding adapter
        specifications. The associated YAML file is loaded lazily on first
        access and cached on the instance to avoid I/O at import time.

        Returns:
            A dictionary mapping from gripper key to adapter specification.
        """
        cache_attr = "_adapters_cache"
        if not hasattr(self, cache_attr):
            setattr(self, cache_attr, self._load_adapter_yaml())
        return getattr(self, cache_attr)

    def required_gripper(self):
        """Specify a default gripper for the arm model.

        Subclasses can override this convenience hook to provide an automatic
        default gripper. The base implementation returns None.

        Returns:
            An identifier or registry key for the default gripper, or None.
        """
        return None


class IntegratedManipulatorModel(ArmModel):
    """A manipulator model where the gripper is part of the main MJCF file.

    This class represents a complete arm-hand system defined in a single model.

    Attributes:
        has_builtin_gripper: Always True for this class.
        builtin_gripper_dof: The number of DoFs of the built-in gripper.
        builtin_gripper_joint_map: A mapping from logical finger names to
            slices or indices in the entity's joint vector.
        builtin_gripper_root_link: The name of the link in which the built-in
            gripper's root frame is expressed.
        builtin_gripper_q_lo: Optional lower joint limits for the gripper.
        builtin_gripper_q_hi: Optional upper joint limits for the gripper.
        builtin_gripper_home_q: Optional nominal configuration for the gripper.
        tcp_pose: Optional pose of the tool center point (TCP) expressed in the
            builtin_gripper_root_link frame as [x, y, z, qx, qy, qz, qw].
        builtin_gripper_grasp_tips: An optional list of tip link names used for
            grasping visualizations.
        builtin_gripper_pinch_pairs: An optional list of finger-pair tuples
            used for pinch grasp helpers.
    """

    has_builtin_gripper = True

    builtin_gripper_dof: int
    builtin_gripper_joint_map: dict[str, slice] | dict[str, Sequence[int]]
    builtin_gripper_root_link: str

    builtin_gripper_q_lo: torch.Tensor | None = None
    builtin_gripper_q_hi: torch.Tensor | None = None
    builtin_gripper_home_q: torch.Tensor | None = None

    tcp_pose: torch.Tensor | None = None

    builtin_gripper_grasp_tips: Sequence[str] | None = None
    builtin_gripper_pinch_pairs: Sequence[tuple[str, str]] | None = None

    @property
    def finger_slice(self) -> slice:
        """Gets a slice for the gripper joints in the entity's DoF array.

        This is useful when a separate gripper controller needs to operate on
        the joint state of an integrated manipulator.

        Returns:
            A slice covering the last builtin_gripper_dof joints.

        Raises:
            AttributeError: If called on a non-integrated manipulator or if
                builtin_gripper_dof is not defined.
        """
        if not self.has_builtin_gripper:
            raise AttributeError("finger_slice only valid on integrated manipulators")
        dof = getattr(self, "builtin_gripper_dof", None)
        if dof is None:
            raise AttributeError(
                "integrated manipulator must define builtin_gripper_dof for finger_slice",
            )
        return slice(self.dof - dof, self.dof)
