import torch
import torch.nn as nn
from torch import zeros


class MultiheadRMSNorm(nn.Module):
    """
    Multi-head Root Mean Square Layer Normalization.

    This normalization applies RMSNorm to the input and then scales it
    with a per-head learnable parameter. Each attention head gets its own
    scaling factor (gamma), allowing different heads to have different
    normalization scales.

    The operation is: output = RMSNorm(x) * (gamma + 1.0)
    where gamma has shape (heads, 1, dim) and is initialized to zero.

    Args:
        dim: Feature dimension
        heads: Number of attention heads
    """

    def __init__(self, dim: int, heads: int):
        super().__init__()
        self.rmsnorm = nn.RMSNorm(dim, elementwise_affine=False)
        self.gamma = nn.Parameter(zeros(heads, 1, dim))

    def forward(self, x) -> torch.Tensor:
        """
        Forward pass through multi-head RMS normalization.

        Args:
            x: Input tensor, shape (..., heads, ..., dim) or (..., dim)
               The tensor should be compatible with broadcasting with
               gamma of shape (heads, 1, dim).

        Returns:
            Normalized and scaled tensor, same shape as input
        """
        return self.rmsnorm(x) * (self.gamma + 1.0)
