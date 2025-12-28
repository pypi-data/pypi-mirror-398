import torch
import torch.nn as nn
from .layer_norm import LayerNorm


class ResidualNorm(nn.Module):
    """
    Residual connection with normalization wrapper.

    This module applies a model transformation, normalizes the output,
    and adds it to the input as a residual connection. This pattern was
    used in the original TTT (Titans) paper.

    The operation is: output = LayerNorm(model(x)) + x

    Note: This wrapper could potentially be removed in favor of more
    standard residual patterns, but is kept for compatibility with
    the original implementation.

    Args:
        dim: Model dimension for LayerNorm
        model: The model/transformation to apply before normalization
    """

    def __init__(self, dim, model: nn.Module):
        super().__init__()
        self.norm = LayerNorm(dim)
        self.model = model

    def forward(self, x) -> torch.Tensor:
        out = self.model(x)
        return self.norm(out) + x
