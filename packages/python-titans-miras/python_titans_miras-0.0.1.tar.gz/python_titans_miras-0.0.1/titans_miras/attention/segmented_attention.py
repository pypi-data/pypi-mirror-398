from typing import Callable

from functools import partial
from collections import namedtuple

from math import ceil
from torch import nn
import torch
import torch.nn.functional as F
from einops import repeat, rearrange
from einops.layers.torch import Rearrange
from rotary_embedding_torch import RotaryEmbedding
from x_transformers.attend import Attend


try:
    from torch.nn.attention.flex_attention import (
        flex_attention,
        create_block_mask,
    )

    if torch.cuda.is_available():
        flex_attention = torch.compile(flex_attention)
except ImportError:
    flex_attention = None
    create_block_mask = None

from titans_miras.miras.bias import LinearNoBias

AttnIntermediates = namedtuple("AttnIntermediates", ("value_residual", "cached_key_values"))


def create_mac_block_mask(seq_len: int, window_size: int, persist_mem_len: int, sliding: bool = False):
    """
    Create a block mask for Memory-As-Context (MAC) attention.

    The mask enforces:
    - Causal attention (can only attend to past tokens)
    - Block-diagonal structure (tokens only attend within their segment)
    - Persistent memory tokens are always accessible

    Args:
        seq_len: Length of the sequence
        window_size: Size of each attention window/segment
        persist_mem_len: Number of persistent memory tokens
        sliding: If True, use sliding window instead of block-diagonal.
                Sliding windows allow tokens to attend to previous window.

    Returns:
        Block mask function compatible with PyTorch's flex_attention
    """

    def create_mac_mask(_, __, q_idx, kv_idx):
        is_persist_mem = kv_idx < persist_mem_len
        kv_without_mem = kv_idx - persist_mem_len
        causal_mask = q_idx >= kv_without_mem
        if not sliding:
            block_diagonal = (q_idx // window_size) == (kv_without_mem // window_size)
            causal_mask = causal_mask & block_diagonal
        else:
            sliding_mask = (q_idx - kv_without_mem) <= window_size
            causal_mask = causal_mask & sliding_mask
        return is_persist_mem | (~is_persist_mem & causal_mask)

    block_mask = create_block_mask(
        create_mac_mask,
        B=None,
        H=None,
        Q_LEN=seq_len,
        KV_LEN=seq_len + persist_mem_len,
        _compile=True,
    )
    return block_mask


def round_up_multiple(seq, mult):
    """
    Round a number up to the nearest multiple.

    Args:
        seq: Number to round up
        mult: Multiple to round up to

    Returns:
        Smallest multiple of mult that is >= seq
    """
    return ceil(seq / mult) * mult


def pad_at_dim(t, pad, dim=-1, value=0.0):
    """
    Pad a tensor at a specific dimension.

    Args:
        t: Input tensor
        pad: Padding tuple (left, right) or single value for symmetric padding
        dim: Dimension to pad. Default is -1 (last dimension).
        value: Value to pad with. Default is 0.0.

    Returns:
        Padded tensor
    """
    dims_from_right = (-dim - 1) if dim < 0 else (t.ndim - dim - 1)
    zeros = (0, 0) * dims_from_right
    return F.pad(t, (*zeros, *pad), value=value)


def pad_and_segment_with_inverse(seq, segment_len, fold_into_batch=True, inverse_remove_pad=True):
    """
    Pad sequence to multiple of segment_len and optionally fold into batch dimension.

    This function prepares sequences for segmented processing by:
    1. Padding to the next multiple of segment_len
    2. Optionally folding segments into batch dimension
    3. Returning an inverse function to restore original shape

    Args:
        seq: Input sequence, shape (batch, seq_len, ...)
        segment_len: Target segment length
        fold_into_batch: If True, fold segments into batch dimension.
                        Result shape: (batch * num_segments, segment_len, ...)
        inverse_remove_pad: If True, inverse function removes padding.
                           Default is True.

    Returns:
        Tuple of (processed_seq, inverse_fn) where:
        - processed_seq: Padded and optionally folded sequence
        - inverse_fn: Function to restore original shape and remove padding
    """
    batch, seq_len = seq.shape[:2]
    next_seq_len_mult = round_up_multiple(seq_len, segment_len)
    padding = next_seq_len_mult - seq_len
    needs_pad = padding > 0
    if needs_pad:
        seq = F.pad(seq, (0, 0, 0, padding))
    if fold_into_batch:
        seq = rearrange(seq, "b (w n) d -> (b w) n d", n=segment_len)

    def inverse(out):
        if fold_into_batch:
            out = rearrange(out, "(b w) ... n d -> b ... (w n) d", b=batch)
        if needs_pad and inverse_remove_pad:
            out = out[..., :-padding, :]
        return out

    return seq, inverse


def is_not_none(v):
    """
    Check if a value is not None.

    Args:
        v: Value to check

    Returns:
        True if v is not None, False otherwise
    """
    return v is not None


class SegmentedAttention(nn.Module):
    """
    Segmented Attention mechanism for Memory-As-Context (MAC) transformer.

    This attention mechanism processes sequences in segments, enabling efficient
    handling of long sequences. It supports:
    - Persistent memory tokens that persist across segments
    - Long-term memory tokens within segments
    - Sliding window attention for overlapping context
    - Value residual connections for improved gradient flow
    - Flex attention for optimized CUDA kernels

    The attention uses rotary positional embeddings and can operate in three modes:
    1. Training mode: Processes full sequences with segmentation
    2. Inference mode: Processes single tokens with caching
    3. Flex attention mode: Uses optimized CUDA kernels when available

    Args:
        dim: Model dimension (feature size)
        segment_len: Length of each segment for processing
        num_persist_mem_tokens: Number of persistent memory tokens that persist
                               across all segments. Default is 0.
        num_longterm_mem_tokens: Number of long-term memory tokens within segments.
                                Default is 0.
        dim_head: Dimension per attention head. Default is 64.
        heads: Number of attention heads. Default is 8.
        sliding: Whether to use sliding window attention instead of block-diagonal.
                Sliding windows allow overlapping context. Default is False.
        accept_value_residual: Whether to accept and mix value residuals.
                              If True, enables learned mixing between current values
                              and residual values. Default is False.
        attend_kwargs: Additional keyword arguments to pass to attention function.
                      Default is empty dict.
        use_flex_attn: Whether to use PyTorch's flex attention when available.
                      Requires CUDA and PyTorch >= 2.4. Default is False.
    """

    def __init__(
        self,
        dim,
        segment_len,
        num_persist_mem_tokens=0,
        num_longterm_mem_tokens=0,
        dim_head=64,
        heads=8,
        sliding=False,
        accept_value_residual=False,
        attend_kwargs: dict = dict(),
        use_flex_attn=False,
    ):
        super().__init__()
        self.norm = nn.RMSNorm(dim)
        dim_inner = dim_head * heads
        self.rotary_emb = RotaryEmbedding(dim_head)
        self.attend = Attend(causal=True, **attend_kwargs)
        self.to_qkv = LinearNoBias(dim, dim_inner * 3)
        self.to_out = LinearNoBias(dim_inner, dim)
        self.to_learned_v_mix = (
            nn.Sequential(
                nn.Linear(dim, heads),
                Rearrange("b n h -> b h n 1"),
                nn.Sigmoid(),
            )
            if accept_value_residual
            else None
        )
        self.segment_len = segment_len
        self.num_longterm_mem_tokens = num_longterm_mem_tokens
        total_segment_len = segment_len + num_longterm_mem_tokens
        self.total_segment_len = total_segment_len
        self.sliding = sliding
        self.split_heads = Rearrange("b n (h d) -> b h n d", h=heads)
        self.merge_heads = Rearrange("b h n d -> b n (h d)")
        self.persistent_memory = nn.Parameter(torch.zeros(2, heads, num_persist_mem_tokens, dim_head))

        assert not (
            use_flex_attn and not is_not_none(flex_attention)
        ), "you need to be on the latest pytorch with a cuda device available"
        self.use_flex_attn = use_flex_attn
        self.segment_len = segment_len
        self.num_persist_mem_tokens = num_persist_mem_tokens

    def forward_inference(
        self,
        token,
        cache,
        value_residual=None,
        output_gating=None,
    ):
        """
        Forward pass for inference (single token processing).

        Args:
            token: Single token input, shape (batch, 1, dim)
            cache: Cached key-value pairs from previous forward pass.
                  Should be a tuple (cache_keys, cache_values) where each
                  is a tensor of shape (batch, heads, cached_seq_len, dim_head).
            value_residual: Optional value residual for mixing. Only used if
                          accept_value_residual was True in __init__.
            output_gating: Optional output gating tensor for scaling output.
                          Shape should be (batch, seq_len, dim).

        Returns:
            Tuple of (output, intermediates) where:
            - output: Attention output, shape (batch, 1, dim)
            - intermediates: AttnIntermediates namedtuple containing:
              * value_residual: Original value before mixing
              * cached_key_values: Updated cache for next iteration

        Process:
            1. Compute attention queries, keys, and values
            2. Apply value residual mixing if enabled
            3. Update cache with new key-value pairs
            4. Apply rotary positional embeddings
            5. Prepare tensors for attention
            6. Add persistent memory key/value pairs
            7. Apply attention
        """
        batch = token.shape[0]

        token = self.norm(token)
        q, k, v = self.to_qkv(token).chunk(3, dim=-1)
        q, k, v = map(self.split_heads, (q, k, v))

        orig_v = v
        if is_not_none(self.to_learned_v_mix):
            mix = self.to_learned_v_mix(token)
            v = v.lerp(value_residual, mix)

        ck, cv = cache
        k = torch.cat((ck, k), dim=-2)
        v = torch.cat((cv, v), dim=-2)
        next_cache = (k, v)

        q, k = self.rotary_emb.rotate_queries_with_cached_keys(q, k)

        q, k, v = tuple(rearrange(t, "b h n d -> b h n d") for t in (q, k, v))

        pmk, pmv = repeat(self.persistent_memory, "kv ... -> kv b ...", b=k.shape[0])
        k = torch.cat((pmk, k), dim=-2)
        v = torch.cat((pmv, v), dim=-2)

        out, _ = self.attend(q, k, v)
        out = self.merge_heads(out)
        out = self.to_out(out)
        if is_not_none(output_gating):
            out = out * output_gating
        return out, AttnIntermediates(orig_v, next_cache)

    def forward_flex(
        self,
        seq,
        value_residual=None,
        flex_attn_fn: Callable | None = None,
        output_gating=None,
        cache=None,
    ):
        """
        Forward pass using PyTorch's flex attention (CUDA optimized).

        This method uses optimized CUDA kernels for attention computation.
        Requires CUDA device and PyTorch >= 2.4 with flex_attention support.

        Args:
            seq: Input sequence, shape (batch, seq_len, dim)
            value_residual: Optional value residual for mixing. Only used if
                          accept_value_residual was True in __init__.
            flex_attn_fn: Optional custom flex attention function. If None,
                         a default block mask will be created.
            output_gating: Optional output gating tensor for scaling output.
                          Shape should be (batch, seq_len, dim).
            cache: Currently unused in flex attention mode.

        Returns:
            Tuple of (output, intermediates) where:
            - output: Attention output, shape (batch, seq_len, dim)
            - intermediates: AttnIntermediates namedtuple containing:
              * value_residual: Original value before mixing
              * cached_key_values: Cache tuple (keys, values)

        Process:
            1. Compute attention queries, keys, and values
            2. Apply value residual mixing if enabled
            3. Prepare cache for next iteration
            4. Add persistent memory key/value pairs
            5. Apply rotary positional embeddings
            6. Concatenate persistent memory with sequence keys/values
            7. Prepare flex attention mask if not provided
            8. Apply flex attention
        """
        assert not (is_not_none(value_residual) ^ is_not_none(self.to_learned_v_mix))
        batch, seq_len = seq.shape[:2]

        seq = self.norm(seq)
        q, k, v = self.to_qkv(seq).chunk(3, dim=-1)
        q, k, v = map(self.split_heads, (q, k, v))

        orig_v = v
        if is_not_none(self.to_learned_v_mix):
            mix = self.to_learned_v_mix(seq)
            v = v.lerp(value_residual, mix)

        next_cache = (k, v)

        pmk, pmv = repeat(self.persistent_memory, "kv h n d -> kv b h n d", b=batch)

        q, k = self.rotary_emb.rotate_queries_with_cached_keys(q, k)

        k = torch.cat((pmk, k), dim=-2)
        v = torch.cat((pmv, v), dim=-2)

        if not is_not_none(flex_attn_fn):
            block_mask = create_mac_block_mask(
                seq_len,
                self.total_segment_len,
                self.num_persist_mem_tokens,
                self.sliding,
            )
            flex_attn_fn = partial(flex_attention, block_mask=block_mask)

        out = flex_attn_fn(q, k, v)
        out = self.merge_heads(out)
        out = self.to_out(out)
        if is_not_none(output_gating):
            out = out * output_gating
        return out, AttnIntermediates(orig_v, next_cache)

    def forward(
        self,
        seq,
        value_residual=None,
        flex_attn_fn: Callable | None = None,
        disable_flex_attn=False,
        output_gating=None,
        cache=None,
    ):
        """
        Forward pass through segmented attention.

        Automatically selects the appropriate forward method based on:
        - If cache is provided: uses forward_inference (single token)
        - If CUDA and use_flex_attn: uses forward_flex (optimized)
        - Otherwise: uses standard segmented attention

        Args:
            seq: Input sequence, shape (batch, seq_len, dim) for training,
                 or (batch, 1, dim) for inference
            value_residual: Optional value residual for mixing. Only used if
                          accept_value_residual was True in __init__.
            flex_attn_fn: Optional custom flex attention function.
            disable_flex_attn: If True, disables flex attention even if available.
                             Default is False.
            output_gating: Optional output gating tensor for scaling output.
                          Shape should be (batch, seq_len, dim).
            cache: Optional cached key-value pairs for inference mode.
                  If provided, seq must have shape (batch, 1, dim).

        Returns:
            Tuple of (output, intermediates) where:
            - output: Attention output, shape matches input seq
            - intermediates: AttnIntermediates namedtuple containing:
              * value_residual: Original value before mixing
              * cached_key_values: Updated cache for next iteration

        Process (standard segmented attention):
            1. Auto-pad sequence to multiple of segment length
            2. Compute attention queries, keys, and values
            3. Apply value residual mixing if enabled
            4. Prepare cache for next iteration
            5. Apply rotary positional embeddings
            6. Fold sequence into segments for block-diagonal attention
            7. Handle sliding window attention (for CPU or when enabled)
            8. Create sliding window mask for attention (if sliding enabled)
            9. Add persistent memory key/value pairs
            10. Apply attention
        """
        is_inferencing = is_not_none(cache)
        if is_inferencing:
            assert seq.shape[-2] == 1
            return self.forward_inference(seq, cache, value_residual, output_gating=output_gating)
        if seq.is_cuda and self.use_flex_attn and not disable_flex_attn:
            return self.forward_flex(
                seq,
                value_residual,
                flex_attn_fn,
                output_gating=output_gating,
                cache=cache,
            )
        assert not (is_not_none(value_residual) ^ is_not_none(self.to_learned_v_mix))
        segment_len, num_longterm_mem_tokens = (
            self.segment_len,
            self.num_longterm_mem_tokens,
        )
        total_segment_len = segment_len + num_longterm_mem_tokens
        batch, seq_len = seq.shape[:2]

        seq, inverse_segment = pad_and_segment_with_inverse(seq, total_segment_len, fold_into_batch=False)

        seq = self.norm(seq)
        q, k, v = self.to_qkv(seq).chunk(3, dim=-1)
        q, k, v = map(self.split_heads, (q, k, v))

        orig_v = v
        if is_not_none(self.to_learned_v_mix):
            mix = self.to_learned_v_mix(seq)
            v = v.lerp(value_residual, mix)

        next_cache = tuple(map(inverse_segment, (k, v)))

        q, k = self.rotary_emb.rotate_queries_with_cached_keys(q, k)

        q, k, v = tuple(rearrange(t, "b h (w n) d -> (b w) h n d", n=total_segment_len) for t in (q, k, v))

        attend_kwargs = dict()
        if self.sliding:
            k, v = tuple(rearrange(t, "(b w) ... -> b w ...", b=batch) for t in (k, v))
            k, v = tuple(pad_at_dim(t, (1, 0), value=0.0, dim=1) for t in (k, v))
            k = torch.cat((k[:, :-1], k[:, 1:]), dim=-2)
            v = torch.cat((v[:, :-1], v[:, 1:]), dim=-2)
            k, v = tuple(rearrange(t, "b w ... -> (b w) ...") for t in (k, v))

            idx = torch.arange(seq.shape[-2], device=seq.device)
            q_idx = rearrange(idx, "(w n) -> w n", n=total_segment_len)
            k_idx = pad_at_dim(q_idx, (1, 0), dim=0, value=-1e4)
            k_idx = torch.cat((k_idx[:-1], k_idx[1:]), dim=-1)
            q_idx = rearrange(q_idx, "w i -> w i 1")
            k_idx = rearrange(k_idx, "w j -> w 1 j")
            sliding_mask = (q_idx - k_idx) <= total_segment_len
            sliding_mask = F.pad(sliding_mask, (self.num_persist_mem_tokens, 0), value=True)
            sliding_mask = repeat(sliding_mask, "w i j -> (b w) 1 i j", b=batch)
            attend_kwargs.update(mask=sliding_mask)

        pmk, pmv = repeat(self.persistent_memory, "kv ... -> kv b ...", b=k.shape[0])
        k = torch.cat((pmk, k), dim=-2)
        v = torch.cat((pmv, v), dim=-2)

        out, _ = self.attend(q, k, v, **attend_kwargs)
        out = self.merge_heads(out)
        out = self.to_out(out)
        out = rearrange(out, "(b w) n d -> b (w n) d", b=batch)
        out = inverse_segment(out)
        if is_not_none(output_gating):
            out = out * output_gating
        return out, AttnIntermediates(orig_v, next_cache)
