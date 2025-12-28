import torch.nn as nn
import torch.nn.functional as F
from torch import randn


class FactorizedMemoryMLP(nn.Module):
    """
    Memory MLP with factorized weights for reduced memory footprint.

    This variant uses low-rank factorization for each weight matrix:
    W = W1 @ W2 where W1 is (dim, k) and W2 is (k, dim).

    This factorization allows trading off model capacity for smaller chunk sizes
    and reduced memory usage, making it suitable for memory-constrained scenarios.

    Args:
        dim: Input and output dimension
        depth: Number of layers in the MLP
        k: Rank of the factorization (bottleneck dimension).
          Smaller k reduces memory but also reduces capacity.
          Default is 32.
    """

    def __init__(self, dim, depth, k=32):
        super().__init__()
        self.weights = nn.ParameterList(
            [
                nn.ParameterList(
                    [
                        nn.Parameter(randn(dim, k)),
                        nn.Parameter(randn(k, dim)),
                    ]
                )
                for _ in range(depth)
            ]
        )
        for weight1, weight2 in self.weights:
            nn.init.xavier_uniform_(weight1)
            nn.init.xavier_uniform_(weight2)

    def forward(self, x):
        """
        Forward pass through the factorized memory MLP.

        Args:
            x: Input tensor, shape (..., dim)

        Returns:
            Output tensor, shape (..., dim)
        """
        for ind, (weight1, weight2) in enumerate(self.weights):
            is_first = ind == 0
            if not is_first:
                x = F.gelu(x)
            x = x @ weight1 @ weight2
        return x
