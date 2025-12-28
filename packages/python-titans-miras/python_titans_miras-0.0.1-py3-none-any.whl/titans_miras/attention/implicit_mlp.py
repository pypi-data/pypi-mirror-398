from __future__ import annotations
import torch.nn as nn
import torch.nn.functional as F
from torch import cat, randn
from torch.utils._pytree import tree_map
from einops.layers.torch import Rearrange
from rotary_embedding_torch import RotaryEmbedding
from titans_miras.shared.utils import is_not_none


class ImplicitMLPAttention(nn.Module):
    """
    Implicit MLP Attention mechanism from Titans/TTT.

    This attention mechanism implements an implicit multi-layer perceptron (MLP)
    through a chain of attention operations. Each key-value pair in the chain
    forms an implicit weight matrix, and chaining them creates the implicit MLP
    structure used in the Titans architecture.

    The mechanism uses rotary positional embeddings and supports talking heads
    for improved attention patterns. Keys can optionally be normalized using RMSNorm.

    Args:
        dim: Model dimension (feature size)
        mlp_hiddens: Tuple of hidden dimensions for the implicit MLP.
                    Must have at least 2 elements. The first and last should
                    typically match the model dimension.
        activation: Activation function to apply between attention layers.
                   Default is SiLU.
        heads: Number of attention heads. Default is 8.
        talking_heads: Whether to use talking heads mechanism (Shazeer et al.).
                      Default is True.
        prenorm: Whether to apply normalization before attention. Default is True.
        keys_rmsnorm: Whether to apply RMSNorm to keys before attention.
                     See https://openreview.net/forum?id=HkztQWZfl2
                     Default is True.
    """

    def __init__(
        self,
        dim,
        mlp_hiddens: tuple[int, ...],
        *,
        activation=nn.SiLU(),
        heads=8,
        talking_heads=True,
        prenorm=True,
        keys_rmsnorm=True,  # https://openreview.net/forum?id=HkztQWZfl2
    ):
        super().__init__()
        assert isinstance(mlp_hiddens, tuple) and len(mlp_hiddens) >= 2
        dim_mlp_in, *dim_mlp_inner, dim_mlp_out = mlp_hiddens
        self.norm = nn.RMSNorm(dim) if prenorm else nn.Identity()
        dim_query_inner = dim_mlp_in * heads
        self.to_queries = nn.Linear(dim, dim_query_inner, bias=False)
        self.rotary_embed = RotaryEmbedding(min(mlp_hiddens))

        self.keys = nn.ModuleList([])
        self.key_norms = nn.ModuleList([])
        self.values = nn.ModuleList([])
        for dim_in, dim_out in zip(mlp_hiddens[:-1], mlp_hiddens[1:]):
            dim_keys_inner = dim_in * heads
            dim_values_inner = dim_out * heads
            keys = nn.Linear(dim, dim_keys_inner, bias=False)
            key_norms = nn.RMSNorm(dim_in) if keys_rmsnorm else nn.Identity()
            values = nn.Linear(dim, dim_values_inner, bias=False)
            self.keys.append(keys)
            self.key_norms.append(key_norms)
            self.values.append(values)
        self.activation = activation

        self.talking_heads = nn.Identity()
        if talking_heads and len(dim_mlp_inner) > 0:
            self.talking_heads = nn.Conv2d(heads, heads, 1, bias=False)
            nn.init.dirac_(self.talking_heads.weight)

        self.split_heads = Rearrange("b n (h d) -> b h n d", h=heads)
        self.merge_heads = Rearrange("b h n d -> b n (h d)")
        self.to_out = nn.Linear(dim_mlp_out * heads, dim, bias=False)

    def forward(self, tokens, cache=None, return_kv_cache=False):
        """
        Forward pass through implicit MLP attention.

        Args:
            tokens: Input tokens, shape (batch, seq_len, dim)
            cache: Optional cached key-value pairs from previous forward pass.
                  Should be a tuple (cache_keys, cache_values) where each
                  element is a list of tensors matching the number of MLP layers.
            return_kv_cache: If True, return the key-value cache for next iteration.
                           Default is False.

        Returns:
            If return_kv_cache is False:
                Output tensor, shape (batch, seq_len, dim)
            If return_kv_cache is True:
                Tuple of (output, cache) where cache is (keys, values)

        Process:
            1. Split heads for input as well as all keys, values that form the implicit weights
            2. Normalize all keys (if keys_rmsnorm is enabled)
            3. Handle caching for autoregressive generation
            4. Implicit memory MLP: chain attention operations to form implicit MLP
            5. Merge heads back to original dimension
        """
        batch, seq_len, device = *tokens.shape[:2], tokens.device
        tokens = self.norm(tokens)
        queries = self.to_queries(tokens)
        keys = [fn(tokens) for fn in self.keys]
        values = [fn(tokens) for fn in self.values]

        queries, keys, values = tree_map(self.split_heads, (queries, keys, values))

        keys = [norm(k) for norm, k in zip(self.key_norms, keys)]
        if is_not_none(cache):
            cache_keys, cache_values = cache
            keys = [cat(args, dim=-2) for args in zip(cache_keys, keys)]
            values = [cat(args, dim=-2) for args in zip(cache_values, values)]

        def attend(q, k, v):
            q, k = self.rotary_embed.rotate_queries_with_cached_keys(q, k)
            return F.scaled_dot_product_attention(q, k, v, is_causal=True)

        out = queries
        for i, (key, value) in enumerate(zip(keys, values), start=1):
            is_last = i == len(keys)
            out = attend(out, key, value)
            if not is_last:
                out = self.talking_heads(out)
                out = self.activation(out)

        out = self.merge_heads(out)
        out = self.to_out(out)
        if not return_kv_cache:
            return out
        return out, (keys, values)


if __name__ == "__main__":
    implicit_mlp_attention = ImplicitMLPAttention(512, (64, 128, 128, 64), activation=nn.ReLU())
    tokens = randn(1, 1024, 512)
    out, cache = implicit_mlp_attention(tokens)
    out, cache = implicit_mlp_attention(tokens, cache=cache)
    assert out.shape == tokens.shape
