import torch.nn as nn
import torch.nn.functional as F
from torch import randn


class MemoryMLP(nn.Module):
    """
    Memory MLP as proposed in the Titans (TTT) paper.

    This is a multi-layer perceptron used as the memory network in the
    neural memory module. It consists of a series of linear transformations
    with GELU activations between layers (except after the first layer).

    The network architecture:
    - Input dimension: dim
    - Hidden dimensions: dim * expansion_factor (repeated depth-1 times)
    - Output dimension: dim

    Weights are initialized using Xavier uniform initialization.

    Args:
        dim: Input and output dimension
        depth: Number of layers in the MLP
        expansion_factor: Factor to expand hidden dimensions.
                         Hidden dim = dim * expansion_factor.
                         Default is 2.0.
    """

    def __init__(self, dim, depth, expansion_factor=2.0):
        super().__init__()
        dim_hidden = int(dim * expansion_factor)
        dims = (dim, *((dim_hidden,) * (depth - 1)), dim)
        self.weights = nn.ParameterList(
            [nn.Parameter(randn(dim_in, dim_out)) for dim_in, dim_out in zip(dims[:-1], dims[1:])]
        )
        for weight in self.weights:
            nn.init.xavier_uniform_(weight)

    def forward(self, x):
        """
        Forward pass through the memory MLP.

        Args:
            x: Input tensor, shape (..., dim)

        Returns:
            Output tensor, shape (..., dim)
        """
        for ind, weight in enumerate(self.weights):
            is_first = ind == 0
            if not is_first:
                x = F.gelu(x)
            x = x @ weight
        return x
