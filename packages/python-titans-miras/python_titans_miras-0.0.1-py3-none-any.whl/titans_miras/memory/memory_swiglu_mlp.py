import torch.nn as nn
import torch.nn.functional as F
from torch import randn
from titans_miras.norm.layer_norm import LayerNorm


class MemorySwiGluMLP(nn.Module):
    """
    Memory MLP using SwiGLU (Swish-Gated Linear Unit) activation.

    This module is modeled after the popular SwiGLU feedforward architecture
    used in modern transformers (e.g., PaLM, LLaMA). Each layer consists of:
    1. Linear projection to expanded dimension (with gates)
    2. Split into two parts: one for activation, one for gating
    3. Apply Swish (SiLU) to gates and multiply
    4. Linear projection back to original dimension
    5. Residual connection
    6. Layer normalization

    Note: depth=1 corresponds to a 2-layer MLP (one SwiGLU block).
          depth=2 would be 4 layers (two SwiGLU blocks with residual).

    Args:
        dim: Input and output dimension
        depth: Number of SwiGLU blocks. Default is 1 (2-layer MLP).
        expansion_factor: Factor to expand hidden dimensions.
                         Hidden dim = dim * expansion_factor * 2/3.
                         The 2/3 factor is standard for SwiGLU architectures.
                         Default is 4.0.
    """

    def __init__(
        self,
        dim,
        depth: int = 1,
        expansion_factor: float = 4.0,
    ):
        super().__init__()
        dim_inner = int(dim * expansion_factor * 2 / 3)
        self.weights = nn.ParameterList(
            [
                nn.ParameterList(
                    [
                        nn.Parameter(randn(dim, dim_inner * 2)),
                        nn.Parameter(randn(dim_inner, dim)),
                    ]
                )
                for _ in range(depth)
            ]
        )
        self.norm = LayerNorm(dim)

    def forward(self, x):
        """
        Forward pass through the SwiGLU memory MLP.

        Args:
            x: Input tensor, shape (..., dim)

        Returns:
            Output tensor, shape (..., dim)
        """
        for w1, w2 in self.weights:
            residual = x
            x, gates = (x @ w1).chunk(2, dim=-1)
            x = x * F.gelu(gates)
            x = x @ w2
            x = x + residual
        return self.norm(x)
