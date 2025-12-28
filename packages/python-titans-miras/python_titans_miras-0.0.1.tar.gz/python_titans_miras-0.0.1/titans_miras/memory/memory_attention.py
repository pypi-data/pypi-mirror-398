import torch.nn as nn
import torch.nn.functional as F
from torch import randn
from titans_miras.norm.layer_norm import l2norm


class MemoryAttention(nn.Module):
    """
    Attention-based memory module.

    This module combines attention and feedforward operations in parallel,
    similar to the architecture used in PaLM and GPT-J. It computes:
    1. Attention over L2-normalized queries, keys, and values
    2. Feedforward transformation with GELU activation
    3. Sums attention and feedforward outputs

    The attention uses scaled dot-product attention with a configurable scale factor.
    Keys and queries are L2-normalized before attention computation.

    Args:
        dim: Model dimension (feature size)
        scale: Scale factor for attention computation. Default is 8.0.
        expansion_factor: Factor to expand feedforward hidden dimension.
                         Hidden dim = dim * expansion_factor.
                         Default is 2.0.
    """

    def __init__(self, dim, scale=8.0, expansion_factor=2.0):
        super().__init__()
        self.scale = scale
        dim_ff_hidden = int(dim * expansion_factor)
        self.weights = nn.ParameterList(
            [
                nn.Parameter(randn(dim, dim)),
                nn.Parameter(randn(dim, dim)),
                nn.Parameter(randn(dim, dim)),
                nn.Parameter(randn(dim, dim_ff_hidden)),
                nn.Parameter(randn(dim_ff_hidden, dim)),
            ]
        )
        for weight in self.weights:
            nn.init.xavier_uniform_(weight)

    def forward(self, x):
        """
        Forward pass through the memory attention module.

        Args:
            x: Input tensor, shape (..., dim)

        Returns:
            Output tensor, shape (..., dim)

        Process:
            1. Compute L2-normalized queries and keys, and values
            2. Apply scaled dot-product attention
            3. Compute feedforward transformation with GELU activation
            4. Sum attention and feedforward outputs (parallel architecture as in PaLM + GPT-J)
        """
        wq, wk, wv, ffw1, ffw2 = self.weights
        q = l2norm(x @ wq)
        k = l2norm(x @ wk)
        v = x @ wv
        attn_out = F.scaled_dot_product_attention(q, k, v, scale=self.scale, is_causal=True)

        h = F.gelu(x @ ffw1)
        ff_out = h @ ffw2
        return attn_out + ff_out
