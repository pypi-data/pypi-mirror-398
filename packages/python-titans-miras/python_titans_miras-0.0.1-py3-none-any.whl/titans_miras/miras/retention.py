from __future__ import annotations
from typing import Callable, Literal
from abc import ABC, abstractmethod
from torch.nn import Module
from torch import Tensor
import torch.nn.functional as F


class RetentionGate(Module, ABC):
    """
    Abstract base class for retention gate mechanisms.

    The retention gate controls how much of past knowledge is retained
    versus how much new information is incorporated. It acts as a
    forgetting mechanism with regularization properties.
    """

    @abstractmethod
    def forward(
        self,
        update: Tensor,
        decay_factor: Tensor,
        prev_state: Tensor | None = None,
    ) -> Tensor:
        """
        Apply retention/forgetting mechanism to the update.

        Args:
            update: The surprise/gradient update to apply
            decay_factor: Learned decay factor (0-1), how much to forget
            prev_state: Previous state for the associative scan

        Returns:
            Processed update with retention applied
        """
        raise NotImplementedError

    def __call__(
        self,
        update: Tensor,
        decay_factor: Tensor,
        prev_state: Tensor | None = None,
    ) -> Tensor:
        return self.forward(update, decay_factor, prev_state)

    def combine_with_scan(
        self,
        assoc_scan: Callable,
        decay_factor: Tensor,
        update: Tensor,
        prev_state: Tensor | None = None,
    ) -> Tensor:
        """
        Combine update with previous state using associative scan.

        This is the default implementation using weighted decay.
        Subclasses can override for different combination strategies.

        Args:
            assoc_scan: Associative scan function
            decay_factor: Decay factor tensor
            update: Current update
            prev_state: Previous accumulated state

        Returns:
            Combined state
        """
        return assoc_scan(1.0 - decay_factor, update, prev=prev_state, remove_prev=False)


class MSERetentionGate(RetentionGate):
    """
    MSE-based retention gate (default weight decay).

    This implements the standard exponential moving average decay
    used in the original Titans paper. The retention uses the
    standard (1 - decay) * new + decay * old formulation.
    """

    def __init__(self):
        super().__init__()

    def forward(
        self,
        update: Tensor,
        decay_factor: Tensor,
        prev_state: Tensor | None = None,
    ) -> Tensor:
        """
        Apply retention/forgetting mechanism to the update.
        The combination happens in combine_with_scan - we pass it forward here for gradient computation.


        Args:
            update: The surprise/gradient update to apply
            decay_factor: Learned decay factor (0-1), how much to forget
            prev_state: Previous state for the associative scan

        Returns:
            Tensor
        """
        return update


class GeneralizedNormRetentionGate(RetentionGate):
    """
    Generalized p-norm retention gate for MONETA variant.

    Applies p-norm regularization to the retention mechanism,
    encouraging sparser or more uniform forgetting patterns
    depending on the norm order.

    Args:
        p: The norm order for regularization. Default is 2.0.
        regularization_weight: How strongly to apply the norm constraint.
    """

    def __init__(self, p: float = 2.0, regularization_weight: float = 0.01):
        super().__init__()
        self.p = p
        self.regularization_weight = regularization_weight

    def forward(
        self,
        update: Tensor,
        decay_factor: Tensor,
        prev_state: Tensor | None = None,
    ) -> Tensor:
        """
        Apply p-norm scaling to the update.

        Args:
            update: The surprise/gradient update to apply
            decay_factor: Learned decay factor (0-1), how much to forget
            prev_state: Previous state for the associative scan

        Returns:
            Processed update with p-norm regularization applied

        Process:
            If p != 2.0:
            1. Apply p-norm scaling to the update
            2. Scale update based on its p-norm
        """
        if self.p != 2.0:
            update_norm = (update.abs().pow(self.p).sum(dim=-1, keepdim=True) + 1e-8).pow(1.0 / self.p)
            l2_norm = (update.pow(2).sum(dim=-1, keepdim=True) + 1e-8).sqrt()
            scale = (l2_norm / (update_norm + 1e-8)).clamp(max=2.0)
            update = update * (1.0 + self.regularization_weight * (scale - 1.0))

        return update


class ProbabilityMapRetentionGate(RetentionGate):
    """
    Probability map retention gate for MEMORA variant.

    Forces the memory to act like a strict probability map by
    normalizing updates to ensure controlled, balanced integration.
    This guarantees a clean, stable process for incorporating
    new information.

    Args:
        temperature: Softmax temperature for probability computation.
                    Lower values make the distribution sharper.
        normalize_mode: How to normalize ('softmax', 'l1', 'l2')
    """

    def __init__(
        self,
        temperature: float = 1.0,
        normalize_mode: Literal["softmax", "l1", "l2"] = "l2",
    ):
        super().__init__()
        self.temperature = temperature
        self.normalize_mode = normalize_mode

    def forward_softmax(
        self,
        update: Tensor,
        decay_factor: Tensor,
        prev_state: Tensor | None = None,
    ):
        """
        Apply softmax normalization over feature dimension.

        Flattens to apply softmax over all weight dimensions, then scales back
        to original magnitude to preserve update magnitude.

        Process:
            1. Flatten update tensor
            2. Apply softmax normalization with temperature
            3. Scale back to original magnitude
        """
        orig_shape = update.shape
        flat_update = update.view(*orig_shape[:-1], -1)
        normalized = F.softmax(flat_update / self.temperature, dim=-1)

        scale = flat_update.abs().sum(dim=-1, keepdim=True).clamp(min=1e-8)
        update = (normalized * scale).view(orig_shape)
        return update

    def forward_l1(
        self,
        update: Tensor,
        decay_factor: Tensor,
        prev_state: Tensor | None = None,
    ):
        """
        Apply L1 normalization: sum of absolute values = 1.
        """
        norm = update.abs().sum(dim=-1, keepdim=True).clamp(min=1e-8)
        update = update / norm
        return update

    def forward_l2(
        self,
        update: Tensor,
        decay_factor: Tensor,
        prev_state: Tensor | None = None,
    ):
        """
        Apply L2 normalization: unit norm.
        """
        norm = update.pow(2).sum(dim=-1, keepdim=True).sqrt().clamp(min=1e-8)
        update = update / norm
        return update

    def forward(
        self,
        update: Tensor,
        decay_factor: Tensor,
        prev_state: Tensor | None = None,
    ) -> Tensor:
        return getattr(self, f"forward_{self.normalize_mode}")(
            update=update, decay_factor=decay_factor, prev_state=prev_state
        )

    def combine_with_scan(
        self,
        assoc_scan: Callable,
        decay_factor: Tensor,
        update: Tensor,
        prev_state: Tensor | None = None,
    ) -> Tensor:
        """
        Combine with strict probability constraints.

        After combining, re-normalize to maintain probability map properties.

        Note: Currently only re-normalizes when normalize_mode == "l2". This may
        need review for consistency across normalization modes.

        TODO: Review this - The ProbabilityMapRetentionGate.combine_with_scan method
        only re-normalizes the combined state when normalize_mode == "l2". However,
        the class supports three normalization modes ("softmax", "l1", and "l2"), and
        the docstring claims the gate "Forces the memory to act like a strict probability
        map." When "softmax" or "l1" modes are selected, the combined state won't be
        re-normalized, breaking the probability map constraint and resulting in
        inconsistent behavior across different normalize modes.

        Process:
            1. Combine update with previous state using associative scan
            2. Re-normalize the combined state (currently only for L2 mode)
        """
        combined = assoc_scan(1.0 - decay_factor, update, prev=prev_state, remove_prev=False)

        if self.normalize_mode == "l2":
            norm = combined.pow(2).sum(dim=-1, keepdim=True).sqrt().clamp(min=1e-8)
            combined = combined / norm

        return combined
