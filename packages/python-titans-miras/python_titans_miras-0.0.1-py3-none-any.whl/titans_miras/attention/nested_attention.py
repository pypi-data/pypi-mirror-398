import torch.nn as nn
import torch.nn.functional as F
from torch import cat, randn
from torch.utils._pytree import tree_map
from einops.layers.torch import Rearrange
from rotary_embedding_torch import RotaryEmbedding
from titans_miras.shared.utils import is_not_none


class NestedAttention(nn.Module):
    """
    Nested Attention mechanism.

    This attention mechanism applies attention in a nested fashion:
    1. First, three separate attention operations are performed in parallel
    2. The outputs are then combined through a nested attention operation
    3. This creates a hierarchical attention pattern

    The mechanism uses rotary positional embeddings and supports key-value
    caching for efficient autoregressive generation. Keys are normalized using
    RMSNorm before attention.

    Args:
        dim: Model dimension (feature size)
        dim_head: Dimension per attention head. Default is 64.
        heads: Number of attention heads. Default is 8.
        prenorm: Whether to apply normalization before attention. Default is True.
        keys_rmsnorm: Whether to apply RMSNorm to keys before attention.
                     See https://openreview.net/forum?id=HkztQWZfl2
                     Default is True.
    """

    def __init__(
        self,
        dim,
        *,
        dim_head=64,
        heads=8,
        prenorm=True,
        keys_rmsnorm=True,
    ):
        super().__init__()
        self.norm = nn.RMSNorm(dim) if prenorm else nn.Identity()
        dim_inner = dim_head * heads
        self.to_queries = nn.Linear(dim, dim_inner, bias=False)
        self.rotary_embed = RotaryEmbedding(dim_head)
        self.to_keys = nn.Linear(dim, dim_inner * 3, bias=False)
        self.to_values = nn.Linear(dim, dim_inner * 3, bias=False)
        self.key_norms = nn.ModuleList([nn.RMSNorm(dim_head) for _ in range(3)])
        self.nested_key_norm = nn.RMSNorm(dim_head)
        self.split_heads = Rearrange("b n (h d) -> b h n d", h=heads)
        self.merge_heads = Rearrange("b h n d -> b n (h d)")
        self.to_out = nn.Linear(dim_inner, dim, bias=False)

    def forward(self, tokens, cache=None, return_kv_cache: bool = False):
        """
        Forward pass through nested attention.

        Args:
            tokens: Input tokens, shape (batch, seq_len, dim)
            cache: Optional cached key-value pairs from previous forward pass.
                  Should be a tuple ((cache_keys, cache_values), (cache_nested_keys, cache_nested_values))
                  where cache_keys/cache_values are lists of 3 tensors each,
                  and cache_nested_keys/cache_nested_values are single tensors.
            return_kv_cache: If True, return the key-value cache for next iteration.
                           Default is False.

        Returns:
            If return_kv_cache is False:
                Output tensor, shape (batch, seq_len, dim)
            If return_kv_cache is True:
                Tuple of (output, cache) where cache structure matches input cache

        Process:
            1. Split heads for input as well as all keys, values that form the implicit weights
            2. Normalize all keys (if keys_rmsnorm is enabled)
            3. Handle caching for autoregressive generation
            4. Apply attention operations
            5. Nested attention: first apply three parallel attention operations, then nest them
            6. Merge heads back to original dimension
        """
        batch, seq_len, device = *tokens.shape[:2], tokens.device
        tokens = self.norm(tokens)
        queries = self.to_queries(tokens)
        keys = self.to_keys(tokens).chunk(3, dim=-1)
        values = self.to_values(tokens).chunk(3, dim=-1)

        queries, keys, values = tree_map(self.split_heads, (queries, keys, values))

        keys = [norm(k) for norm, k in zip(self.key_norms, keys)]

        if is_not_none(cache):
            (cache_keys, cache_values), (
                cache_nested_keys,
                cache_nested_values,
            ) = cache
            keys = [cat(args, dim=-2) for args in zip(cache_keys, keys)]
            values = [cat(args, dim=-2) for args in zip(cache_values, values)]

        def attend(q, k, v):
            q, k = self.rotary_embed.rotate_queries_with_cached_keys(q, k)
            return F.scaled_dot_product_attention(q, k, v, is_causal=True)

        nq, nk, nv = [attend(queries, key, value) for key, value in zip(keys, values)]
        nk = self.nested_key_norm(nk)
        if is_not_none(cache):
            nk = cat((cache_nested_keys, nk), dim=-2)
            nv = cat((cache_nested_values, nv), dim=-2)
        out = attend(nq, nk, nv)

        out = self.merge_heads(out)
        out = self.to_out(out)
        if not return_kv_cache:
            return out
        return out, ((keys, values), (nk, nv))


if __name__ == "__main__":
    nested_attn = NestedAttention(dim=512)
    tokens = randn(1, 1024, 512)
    out1, cache = nested_attn(tokens)
    out2, cache = nested_attn(tokens[:, -1:], cache=cache)
    assert out1.shape == tokens.shape
    assert out2.shape == (1, 1, 512)
