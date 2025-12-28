from einops import rearrange
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import zeros


def l2norm(t):
    """
    Apply L2 normalization to a tensor.

    Normalizes the tensor along the last dimension to have unit L2 norm.
    This is equivalent to dividing each vector by its Euclidean norm.

    Args:
        t: Input tensor, shape (..., dim)

    Returns:
        L2-normalized tensor, same shape as input
    """
    return F.normalize(t, dim=-1)


class LayerNorm(nn.Module):
    """Layer Normalization.
    Layer Normalization is a type of normalization that is used to normalize the input.
    It is defined as:
    LayerNorm(x) = x / sqrt(mean(x^2))
    where x is the input, and mean(x^2) is the mean of the square of the input.
    The gamma parameter is a learnable scale factor that is applied to the normalized input.
    The beta parameter is a learnable shift factor that is applied to the normalized input.
    The gamma and beta parameters are learned during training.
    The gamma and beta parameters are initialized to 1.0.
    """

    def __init__(self, dim):
        super().__init__()
        self.ln = nn.LayerNorm(dim, elementwise_affine=False)
        self.gamma = nn.Parameter(zeros(dim))

    def forward(self, x) -> torch.Tensor:
        """
        Forward pass through layer normalization.

        Args:
            x: Input tensor, shape (..., dim) or (batch, seq, dim).
               If gamma has 2 dimensions (batch, dim), it will be
               reshaped to (batch, 1, dim) for broadcasting.

        Returns:
            Normalized and scaled tensor, same shape as input
        """
        gamma = self.gamma
        if gamma.ndim == 2:
            gamma = rearrange(gamma, "b d -> b 1 d")
        return self.ln(x) * (gamma + 1.0)
