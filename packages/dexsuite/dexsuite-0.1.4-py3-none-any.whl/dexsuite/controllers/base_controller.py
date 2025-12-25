"""Base classes and utilities for DexSuite controllers.

Controllers in DexSuite are lightweight wrappers that map an action tensor to
low-level simulator commands (position, velocity, or force) for a subset of a
robot's degrees of freedom (DoFs).

This module defines the Controller base class, which provides:

- Shape handling for single vs. batched environments.
- Optional gain and limit installation from the model.
- Convenience helpers for forward kinematics and inverse kinematics.

The controller API is intentionally small: environments and robots construct a
controller, call post_build once after the scene is built, and then call step at
each control cycle.
"""

from __future__ import annotations

import abc
from typing import Any

import torch

from dexsuite.utils.globals import get_device, get_n_envs


class Controller(abc.ABC):
    """Abstract base class for all DexSuite robot controllers.

    A controller transforms an action vector into simulator commands applied to
    a subset of a robot's degrees of freedom (DoFs). Subclasses implement
    action_space and _apply_cmd.

    Notes:
        DexSuite supports vectorized environments. A controller is constructed
        against a scene with n_envs parallel environments and follows these rules:

        - If n_envs == 1: actions may be 1D with shape (D,).
        - If n_envs > 1: actions must be 2D with shape (n_envs, D).

        The associated model object is expected to provide:

        - Required: dof (int)
        - Optional:
          - control_dofs_index (Sequence[int]): indices controlled by this controller.
          - kp / kv: PD gains (broadcastable to controlled DoFs).
          - force_range: symmetric force/torque limits (broadcastable).
          - home_q: home joint configuration for controlled DoFs (broadcastable).
          - end_link: link name used by OSC and IK controllers.

    Attributes:
        entity: Simulator entity controlled by this controller.
        model: Robot component model associated with the entity.
        dofs_idx: Local DoF indices controlled by this controller.
        n_envs: Number of parallel environments in the scene.
        device: Torch device used for controller tensors.
        kp: Optional proportional gains (torch tensor on device).
        kv: Optional derivative gains (torch tensor on device).
        force_range: Optional symmetric force/torque limits.
        home_q: Optional home configuration for controlled DoFs.
    """

    def __init__(
        self,
        *,
        entity: Any,
        model: Any,
        **_: Any,
    ) -> None:
        """Initialize the controller base.

        Args:
            entity: The simulation entity to control (Genesis entity-like API).
            model: The robot component model.
            _: Ignored extra keyword arguments (kept for forward compatibility).

        Notes:
            This constructor reads optional controller metadata from model (for
            example, gains and home_q) and stores them as torch tensors on the
            active device.
        """
        self.entity = entity
        self.model = model

        control_dofs_index = getattr(self.model, "control_dofs_index", None)
        if control_dofs_index is None:
            self.dofs_idx: list[int] = list(range(int(model.dof)))
        else:
            self.dofs_idx = list(control_dofs_index)

        self.n_envs: int = get_n_envs()
        self._batched: bool = self.n_envs > 1
        self.device: torch.device = get_device()

        kp = getattr(model, "kp", None)
        self.kp: torch.Tensor | None = (
            torch.as_tensor(kp, dtype=torch.float32, device=self.device).contiguous()
            if kp is not None
            else None
        )
        kv = getattr(model, "kv", None)
        self.kv: torch.Tensor | None = (
            torch.as_tensor(kv, dtype=torch.float32, device=self.device).contiguous()
            if kv is not None
            else None
        )
        force_range = getattr(model, "force_range", None)
        self.force_range: torch.Tensor | None = (
            torch.as_tensor(
                force_range,
                dtype=torch.float32,
                device=self.device,
            ).contiguous()
            if force_range is not None
            else None
        )

        home_q = getattr(self.model, "home_q", None)
        self.home_q: torch.Tensor | None = (
            torch.as_tensor(home_q, dtype=torch.float32, device=self.device)
            .contiguous()
            .view(-1)
            if home_q is not None
            else None
        )
        self._home_q_row: torch.Tensor | None = (
            self.home_q.view(1, -1).contiguous() if self.home_q is not None else None
        )

    @property
    def dof(self) -> int:
        """Return the number of controlled degrees of freedom."""
        return len(self.dofs_idx)

    def _is_batched(self) -> bool:
        """Check if the simulation is running in batched mode."""
        return self._batched

    def _n_envs(self) -> int:
        """Get the number of parallel environments."""
        return self.n_envs

    def _as_batch2d(self, x: torch.Tensor, cols: int) -> torch.Tensor:
        """Validate and reshape an input tensor to 2D (batch, cols).

        Args:
            x: Input tensor, either 1D (cols,) (single env) or 2D
                (n_envs, cols) (batched envs).
            cols: Expected size of the last dimension.

        Returns:
            A 2D tensor of shape (1, cols) (single env) or (n_envs, cols)
            (batched envs).

        Raises:
            TypeError: If x is not a torch tensor.
            ValueError: If the tensor has the wrong rank or shape.
        """
        if not torch.is_tensor(x):
            raise TypeError("Input must be a torch.Tensor.")
        if x.ndim == 1:
            if self.n_envs != 1:
                raise ValueError(
                    f"Expected input shape ({self.n_envs}, {cols}) in batched mode; "
                    f"got 1D tensor.",
                )
            if x.numel() != cols:
                raise ValueError(f"Expected input length {cols}, got {x.numel()}.")
            return x.view(1, cols)
        if x.ndim == 2:
            if x.shape[0] != self.n_envs or x.shape[1] != cols:
                raise ValueError(
                    f"Expected input shape ({self.n_envs}, {cols}), "
                    f"got {tuple(x.shape)}.",
                )
            return x
        raise ValueError("Input must be 1D or 2D.")

    def _expect_2d(self, x: torch.Tensor, cols: int) -> torch.Tensor:
        """Alias for _as_batch2d for readability."""
        return self._as_batch2d(x, cols)

    def _to_entity_shape(self, x2d: torch.Tensor) -> torch.Tensor:
        """Convert a batched tensor to the shape expected by Genesis.

        Genesis APIs generally expect (D,) for single-env scenes and (n_envs, D)
        for batched scenes. This helper performs that squeeze when n_envs == 1.
        """
        return x2d[0] if not self._batched else x2d

    def _get_end_effector_link(self) -> Any:
        """Return the end-effector link handle defined by model.end_link."""
        link_name = getattr(self.model, "end_link", None)
        if not link_name:
            raise ValueError("model must define end_link.")
        return self.entity.get_link(link_name)

    def _fk_pos_quat_2d(self, link_idx_local: int) -> tuple[torch.Tensor, torch.Tensor]:
        """Compute forward kinematics for a single link and return batched outputs.

        Args:
            link_idx_local: Link index local to the simulation entity.

        Returns:
            Tuple (pos, quat) where pos has shape (N, 3) and quat has shape
            (N, 4) in wxyz convention, with N == n_envs for batched environments
            and N == 1 otherwise.
        """
        qpos = self.entity.get_dofs_position()
        if self._batched and qpos.ndim == 1:
            qpos = qpos.unsqueeze(0).expand(self.n_envs, -1)
        qpos = qpos.contiguous()

        pos, quat = self.entity.forward_kinematics(
            qpos=qpos,
            links_idx_local=[link_idx_local],
        )
        pos = pos.reshape(-1, 3).to(self.device).contiguous()
        quat = quat.reshape(-1, 4).to(self.device).contiguous()
        return pos, quat

    def _q_to_ctrl(self, q: torch.Tensor) -> torch.Tensor:
        """Convert a full-DoF joint vector to the controlled DoF slice."""
        if q.shape[-1] == self.dof:
            return q
        return q[..., self.dofs_idx]

    @staticmethod
    def _reduce_bounds_1d(
        lo: torch.Tensor,
        hi: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Reduce batched DoF bounds to 1D bounds.

        Some Genesis APIs return per-env bounds with shape (N, D). This helper
        reduces them to 1D bounds with shape (D,) using min and max across
        environments.
        """
        if lo.ndim == 2:
            lo = lo.min(dim=0).values
        if hi.ndim == 2:
            hi = hi.max(dim=0).values
        return lo, hi

    def post_build(self) -> None:
        """Finalize controller construction after the scene is built.

        Subclasses may override this to fetch simulator-derived limits or cache
        handles. The base implementation installs runtime PD gains/limits onto
        the simulator entity (if provided by the model).
        """
        self.install_runtime_gains()

    def install_runtime_gains(self) -> None:
        """Install PD gains and force limits on the simulation entity.

        This is a best-effort operation: if the model does not define a given
        attribute (kp, kv, force_range), that part is skipped.
        """
        if self.kp is not None:
            self.entity.set_dofs_kp(self.kp, self.dofs_idx)
        if self.kv is not None:
            self.entity.set_dofs_kv(self.kv, self.dofs_idx)
        if self.force_range is not None:
            lo = -self.force_range
            hi = self.force_range
            self.entity.set_dofs_force_range(lo, hi, self.dofs_idx)

    def set_home_position(self, env_idx: torch.Tensor | None = None) -> None:
        """Reset controlled joints to the model's home configuration.

        If the model does not define home_q, this method uses zeros for the
        controlled degrees of freedom.

        Broadcasting rules:

        - If home_q contains one scalar and the controller drives multiple DoFs,
          it is broadcast to all controlled DoFs.
        - Otherwise, home_q must match the number of controlled DoFs.

        Genesis expects a 1D position vector when n_envs == 1 and env_idx is
        None, so this method squeezes the leading batch dimension in that case.

        Args:
            env_idx: Optional subset of environment indices to reset.

        Raises:
            ValueError: If home_q is defined but does not match the number of
                controlled DoFs.
        """
        ctrl_dof = len(self.dofs_idx)
        if self.home_q is None:
            q_row = torch.zeros((1, ctrl_dof), dtype=torch.float32, device=self.device)
        else:
            q = self.home_q.reshape(-1)
            if q.numel() == 1 and ctrl_dof > 1:
                q = q.expand(ctrl_dof)
            if q.numel() != ctrl_dof:
                raise ValueError(
                    f"home_q length {q.numel()} != controlled DoFs {ctrl_dof}.",
                )
            q_row = q.view(1, ctrl_dof)

        n_reset = env_idx.numel() if env_idx is not None else self.n_envs
        q_target = q_row.repeat(n_reset, 1).contiguous()
        if self.n_envs == 1 and env_idx is None:
            pos_to_set = q_target.squeeze(0)
        else:
            pos_to_set = q_target

        self.entity.set_dofs_position(
            pos_to_set,
            dofs_idx_local=self.dofs_idx,
            envs_idx=env_idx,
            zero_velocity=True,
        )

    def _ik(
        self,
        *,
        link: Any,
        pos: torch.Tensor,
        quat: torch.Tensor,
        init_qpos: torch.Tensor | None = None,
        envs_idx: torch.Tensor | None = None,
        **kw,
    ) -> torch.Tensor:
        """Solve inverse kinematics for an end-effector pose target.

        Args:
            link: Link handle passed through to the simulator IK API.
            pos: Target positions with shape (3,) or (n_envs, 3).
            quat: Target orientations (wxyz) with shape (4,) or (n_envs, 4).
            init_qpos: Optional IK seed. May be either the full entity DoFs or
                only the controlled DoFs. Supports 1D (broadcast) and 2D seeds.
            envs_idx: Optional indices of environments to solve for.
            kw: Extra keyword arguments passed through to entity.inverse_kinematics.

        Returns:
            A 2D tensor of IK joint solutions. In single-env mode, the returned
            tensor has shape (1, dof) for consistent downstream indexing.

        Raises:
            ValueError: If provided tensors have incompatible shapes.
        """
        p = self._expect_2d(pos, 3)
        q = self._expect_2d(quat, 4)

        batch = p.shape[0]
        full_init_qpos = self._full_qpos_template(batch)

        if init_qpos is None:
            if self._home_q_row is not None:
                full_init_qpos[:, self.dofs_idx] = self._home_q_row.to(
                    self.device,
                ).expand(batch, -1)
        else:
            seed = init_qpos if init_qpos.ndim == 2 else init_qpos.view(1, -1)
            if seed.shape[0] != batch:
                if seed.shape[0] == 1:
                    seed = seed.expand(batch, -1)
                else:
                    raise ValueError(
                        f"init_qpos batch dim must be 1 or {batch}; "
                        f"got {seed.shape[0]}.",
                    )
            if seed.shape[-1] == full_init_qpos.shape[-1]:
                full_init_qpos = seed.contiguous()
            elif seed.shape[-1] == len(self.dofs_idx):
                full_init_qpos[:, self.dofs_idx] = seed.contiguous()
            else:
                raise ValueError(
                    "init_qpos must match either full entity DoFs or controlled DoFs.",
                )

        # The solver expects the full joint state as the initial seed, even if
        # this controller drives only a subset of the entity DoFs.
        out = self.entity.inverse_kinematics(
            link=link,
            pos=self._to_entity_shape(p),
            quat=self._to_entity_shape(q),
            init_qpos=self._to_entity_shape(full_init_qpos),
            dofs_idx_local=self.dofs_idx,
            envs_idx=envs_idx,
            **kw,
        )
        return out if self._batched else out.unsqueeze(0)

    def _full_qpos_template(self, batch: int) -> torch.Tensor:
        """Return a full-DoF joint-position template.

        Args:
            batch: Batch size to match the IK target batch.

        Returns:
            A contiguous clone of the entity's joint positions with shape
            (batch, dof_total).
        """
        qpos = self.entity.get_dofs_position()
        if qpos.ndim == 1:
            qpos = qpos.unsqueeze(0)
        if qpos.shape[0] != batch:
            qpos = qpos.expand(batch, -1)
        return qpos.to(self.device).contiguous().clone()

    def _control_position(self, target: torch.Tensor) -> None:
        """Send a joint position command to the entity.

        Args:
            target: Desired joint positions for the controlled DoFs, shaped
                (D,) or (n_envs, D).
        """
        target = self._expect_2d(target, self.dof)
        self.entity.control_dofs_position(self._to_entity_shape(target), self.dofs_idx)

    def _control_velocity(self, velocity: torch.Tensor) -> None:
        """Send a joint velocity command to the entity.

        Args:
            velocity: Desired joint velocities for the controlled DoFs, shaped
                (D,) or (n_envs, D).
        """
        velocity = self._expect_2d(velocity, self.dof)
        self.entity.control_dofs_velocity(
            self._to_entity_shape(velocity),
            self.dofs_idx,
        )

    def _control_force(self, force_2d: torch.Tensor) -> None:
        """Send a joint force/torque command to the entity.

        Args:
            force_2d: Desired forces/torques for the controlled DoFs, shaped
                (D,) or (n_envs, D).
        """
        tau = self._expect_2d(force_2d, self.dof)
        self.entity.control_dofs_force(self._to_entity_shape(tau), self.dofs_idx)

    @abc.abstractmethod
    def action_space(self) -> Any:
        """Return this controller's action space.

        Returns:
            A Gymnasium spaces.Box describing the action bounds and shape.
        """

    @torch.no_grad()
    def step(self, action: torch.Tensor) -> None:
        """Apply a control action.

        Args:
            action: Action tensor with shape (D,) (single env) or (n_envs, D)
                (batched envs).

        Notes:
            This method is intentionally thin; subclasses should implement
            _apply_cmd and can assume actions are already on the correct device
            and in the correct shape conventions enforced by _expect_2d.
        """
        self._apply_cmd(action)

    @abc.abstractmethod
    def _apply_cmd(self, vec: torch.Tensor) -> None:
        """Apply the processed control command vector.

        Args:
            vec: Action tensor, either (D,) or (n_envs, D) depending on the
                scene configuration.
        """
