import torch.nn as nn
import torch.nn.functional as F
from torch import cat, randn


class GatedResidualMemoryMLP(nn.Module):
    """
    Memory MLP with gated residual connections and final projection.

    This variant enhances the standard memory MLP with:
    1. Gated residual connections: Each layer uses a learned gate to mix
       the residual input with the transformed output
    2. Final projection: An additional linear layer at the end

    The gating mechanism allows the model to learn how much to retain from
    the input versus how much to use from the transformation, providing
    more flexible information flow.

    Args:
        dim: Input and output dimension
        depth: Number of layers in the MLP
        expansion_factor: Factor to expand hidden dimensions.
                         Hidden dim = dim * expansion_factor.
                         Default is 4.0.
    """

    def __init__(self, dim, depth, expansion_factor=4.0):
        super().__init__()
        dim_hidden = int(dim * expansion_factor)
        self.weights = nn.ParameterList(
            [
                nn.ParameterList(
                    [
                        nn.Parameter(randn(dim, dim_hidden)),
                        nn.Parameter(randn(dim_hidden, dim)),
                        nn.Parameter(randn(dim * 2, dim)),
                    ]
                )
                for _ in range(depth)
            ]
        )
        self.final_proj = nn.Parameter(randn(dim, dim))
        for param in self.parameters():
            nn.init.xavier_uniform_(param)

    def forward(self, x):
        """
        Forward pass through the gated residual memory MLP.

        Args:
            x: Input tensor, shape (..., dim)

        Returns:
            Output tensor, shape (..., dim)

        Process:
            For each layer:
            1. Compute feedforward transformation with GELU activation
            2. Gated residual: learn to mix residual input with transformed output
            3. Apply final projection
        """
        for weight1, weight2, to_gates in self.weights:
            res = x
            hidden = x @ weight1
            hidden = F.gelu(hidden)
            branch_out = hidden @ weight2

            gates = cat((branch_out, res), dim=-1) @ to_gates
            x = res.lerp(branch_out, gates.sigmoid())
        return x @ self.final_proj
