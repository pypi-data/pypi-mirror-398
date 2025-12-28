from __future__ import annotations
from abc import ABC, abstractmethod
from functools import partial
from torch import Tensor, where
from torch.nn import Module, Linear

LinearNoBias = partial(Linear, bias=False)


class AttentionalBias(Module, ABC):
    """
    Abstract base class for attentional bias functions.

    The attentional bias determines what the memory model prioritizes
    when learning from new inputs. It computes the loss between the
    memory model's prediction and the target value.
    """

    @abstractmethod
    def forward(self, pred: Tensor, target: Tensor) -> Tensor:
        """
        Compute the attentional bias (loss) between prediction and target.

        Args:
            pred: Memory model prediction, shape (batch, seq, dim)
            target: Target values, shape (batch, seq, dim)

        Returns:
            Loss tensor, shape (batch, seq) - reduced over dim
        """
        raise NotImplementedError


class MSEBias(AttentionalBias):
    """
    Mean Squared Error attentional bias.

    This is the default bias used in the original Titans paper.
    L(pred, target) = (pred - target)² averaged over feature dimension.
    """

    def __init__(self):
        super().__init__()

    def forward(self, pred: Tensor, target: Tensor) -> Tensor:
        """Apply Mean Squared Error loss function to the prediction and target."""
        return (pred - target).pow(2).mean(dim=-1)


class GeneralizedNormBias(AttentionalBias):
    """
    Generalized p-norm attentional bias for MONETA variant.

    Uses Lp norm instead of L2 (MSE) for more disciplined attention.

    Common choices:
    - p=1: L1 norm (Manhattan distance) - robust to outliers
    - p=2: L2 norm (Euclidean distance) - standard MSE
    - p=inf: L∞ norm (Chebyshev distance) - minimizes max error

    Args:
        p: The norm order. Default is 2.0 (equivalent to MSE).
        eps: Small epsilon for numerical stability.
    """

    def __init__(self, p: float = 2.0, eps: float = 1e-8):
        super().__init__()
        self.p = p
        self.eps = eps

    def forward(self, pred: Tensor, target: Tensor) -> Tensor:
        """
        Compute generalized p-norm loss.

        For p=inf: uses L∞ norm (max absolute difference).
        For other p: uses Lp norm (sum |x|^p)^(1/p).
        """
        diff = pred - target

        if self.p == float("inf"):
            return diff.abs().max(dim=-1).values
        else:
            return (diff.abs().pow(self.p).mean(dim=-1) + self.eps).pow(1.0 / self.p)


class HuberBias(AttentionalBias):
    """
    Huber loss attentional bias for YAAD variant.

    The Huber loss is less sensitive to outliers than MSE:
    L_δ(x) = 0.5 * x²           if |x| ≤ δ
           = δ * (|x| - 0.5δ)   otherwise

    This makes the model more robust when input data is messy
    or contains inconsistent tokens.

    Args:
        delta: Threshold for switching between quadratic and linear.
               Default is 1.0. Smaller values are more robust to outliers.
    """

    def __init__(self, delta: float = 1.0):
        super().__init__()
        self.delta = delta

    def forward(self, pred: Tensor, target: Tensor) -> Tensor:
        """
        Compute Huber loss: quadratic for small errors, linear for large errors.
        """
        diff = pred - target
        abs_diff = diff.abs()

        quadratic = 0.5 * diff.pow(2)
        linear = self.delta * (abs_diff - 0.5 * self.delta)

        loss = where(abs_diff <= self.delta, quadratic, linear)
        return loss.mean(dim=-1)
