"""Defines a robot where the manipulator and gripper are a single entity."""

from __future__ import annotations

from typing import Any

import genesis as gs
import torch
from gymnasium import spaces

from dexsuite.controllers import make as make_ctrl
from dexsuite.core.components.arm import IntegratedManipulatorModel
from dexsuite.options import ControllerOptions
from dexsuite.utils import get_device
from dexsuite.utils.action_utils import build_single_layout, dispatch
from dexsuite.utils.robot_utils import (
    attach_tcp_anchor,
    get_end_effector_pose,
    get_robot_morph,
    get_tool_center_point_pose,
    grasp_observation,
)


class _HandProxy:
    """A minimal proxy for an integrated gripper.

    This class provides a gripper-like interface for the hand portion of an
    integrated manipulator, allowing a standard gripper controller to target
    the correct slice of the manipulator's degrees of freedom.

    Attributes:
        dof: The number of degrees of freedom of the integrated gripper.
        root_link: The root link of the integrated gripper.
        home_q: The home joint configuration for the gripper's joints.
        GRASP_TIPS: A tuple of link names for grasp visualization.
        PINCH_PAIRS: A tuple of link name pairs for pinch grasp helpers.
    """

    def __init__(self, manip: IntegratedManipulatorModel, device: torch.device):
        """Initialize the HandProxy.

        Args:
            manip: The integrated manipulator model.
            device: The torch device to move tensors to.
        """
        self.dof = int(getattr(manip, "builtin_gripper_dof", 0))
        self.root_link = getattr(manip, "builtin_gripper_root_link", manip.end_link)
        self.control_dofs_index = getattr(
            manip,
            "builtin_gripper_control_dofs_index",
            None,
        )
        self.tcp_pose = getattr(manip, "builtin_gripper_tcp_pose", None)

        self.home_q = getattr(manip, "builtin_gripper_home_q", None)

        self.GRASP_TIPS = tuple(getattr(manip, "builtin_gripper_grasp_tips", ()) or ())
        self.PINCH_PAIRS = tuple(
            tuple(p) for p in (getattr(manip, "builtin_gripper_pinch_pairs", ()) or ())
        )


class IntegratedRobot:
    """Represents an integrated robot with a built-in gripper.

    This class manages a single simulation entity that contains both the
    manipulator and the gripper. It handles the instantiation of controllers
    for both the arm and the integrated hand.

    Note:
        This class operates internally with 2D tensors (batch_size, dim) for
        all simulation state and actions. The environment is responsible for
        broadcasting 1D actions to 2D.

    Attributes:
        manip: The manipulator model instance.
        scene: The simulation scene.
        device: The PyTorch device for tensor operations.
        arm_ent: The simulation entity for the robot.
        grip: The _HandProxy instance for the integrated gripper.
        arm_ctrl: The controller for the manipulator joints.
        hand_ctrl: The controller for the gripper joints.
        action_space: The combined action space for the robot.
        dof: The total degrees of freedom of the robot.
    """

    def __init__(
        self,
        *,
        manipulator: IntegratedManipulatorModel,
        arm_control_options: ControllerOptions,
        gripper_control_options: ControllerOptions | None,
        scene: gs.Scene,
        base_pos: tuple[float, float, float] = (0.0, 0.0, 0.0),
        quat: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0),
        visualize_tcp: bool = False,
    ):
        """Initialize the IntegratedRobot.

        Args:
            manipulator: The integrated manipulator model instance.
            arm_control_options: Configuration for the arm's controller.
            gripper_control_options: Configuration for the gripper's controller.
            scene: The simulation scene.
            base_pos: The (x, y, z) position of the robot's base.
            quat: The (w, x, y, z) orientation of the robot's base.
            visualize_tcp: If True, enables visualization of the TCP.
        """
        self.manip = manipulator
        self.scene = scene
        self.device = get_device()

        self.arm_ent = scene.add_entity(
            get_robot_morph(manipulator, pos=base_pos, quat=quat),
            material=gs.materials.Rigid(needs_coup=True, gravity_compensation=1.0),
        )
        self._link_names = [ln.name for ln in self.arm_ent.links]
        self._eef_link_idx = self._link_names.index(self.manip.end_link)

        self.gripper = _HandProxy(self.manip, device=self.device)
        self.hand_ent = self.arm_ent
        self.arm_ctrl = make_ctrl(
            arm_control_options,
            entity=self.arm_ent,
            model=self.manip,
        )

        self.hand_ctrl = None
        if gripper_control_options:
            self.hand_ctrl = make_ctrl(
                gripper_control_options,
                entity=self.arm_ent,
                model=self.gripper,
            )

        self.dof = int(self.manip.dof)

        attach_tcp_anchor(self, visualize_tcp)

    @property
    def action_space(self) -> spaces.Box:
        """Get the robot's flat Gymnasium action space."""
        return self._layout.as_box()

    def apply_action(self, action) -> None:
        """Apply an action to the robot's controllers."""
        if action.ndim == 1:
            if action.numel() != self._act_dim:
                raise ValueError(
                    f"Expected ({self._act_dim},), got {tuple(action.shape)}",
                )
        elif action.ndim == 2:
            if action.shape[1] != self._act_dim:
                raise ValueError(
                    f"Expected (_, {self._act_dim}), got {tuple(action.shape)}",
                )
        else:
            raise ValueError("Action must be 1D or 2D.")
        dispatch(self._layout, action)

    def apply_action_validated(self, action: torch.Tensor) -> None:
        """Apply an action without re-validating shape/dtype.

        Intended for hot paths that already validated the flat action at the
        environment boundary.
        """
        dispatch(self._layout, action)

    def install_pd(self) -> None:
        """Initialize the PD controllers for the arm and gripper."""
        self.arm_ctrl.post_build()
        if self.hand_ctrl:
            self.hand_ctrl.post_build()
        self._layout = build_single_layout(
            arm_ctrl=self.arm_ctrl,
            grip_ctrl=self.hand_ctrl,
        )
        self._act_dim = self._layout.total_dim

    def reset(self, env_idx=None) -> None:
        """Reset the robot to its home joint configuration."""
        self.arm_ctrl.set_home_position(env_idx=env_idx)

    def get_obs(self) -> dict[str, Any]:
        """Retrieves the observation dictionary for the robot."""
        qpos_full = self.arm_ent.get_dofs_position()
        qvel_full = self.arm_ent.get_dofs_velocity()
        qtorque_full = self.arm_ent.get_dofs_force()

        eef_pos, eef_quat = get_end_effector_pose(
            self.arm_ent,
            self._eef_link_idx,
            qpos=qpos_full,
        )
        manipulator_observation = {
            "qpos": qpos_full,
            "qvel": qvel_full,
            "qtorque": qtorque_full,
            "eef_pos": eef_pos,
            "eef_quat": eef_quat,
        }

        finger_slice = self.manip.finger_slice
        tcp_pos, tcp_quat = get_tool_center_point_pose(self)
        gripper_observation = {
            "qpos": qpos_full[..., finger_slice],
            "qvel": qvel_full[..., finger_slice],
            "qtorque": qtorque_full[..., finger_slice],
            "tcp_pos": tcp_pos,
            "tcp_quat": tcp_quat,
            **grasp_observation(self),
        }

        return {"manipulator": manipulator_observation, "gripper": gripper_observation}
