from __future__ import annotations
from typing import Callable, Optional
from functools import partial
import tqdm
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import randn, no_grad, tensor
from einops import repeat, rearrange, pack, unpack, einsum
from einops.layers.torch import Rearrange
from axial_positional_embedding import ContinuousAxialPositionalEmbedding
from hyper_connections import get_init_and_expand_reduce_stream_functions
from titans_miras.config import NeuralMemoryConfig, TransformerConfig
from titans_miras.neural_memory import NeuralMemory
from titans_miras.shared.utils import divisible_by, is_not_none
from titans_miras.attention.segmented_attention import (
    SegmentedAttention,
    create_mac_block_mask,
    pad_and_segment_with_inverse,
    flex_attention,
)
from titans_miras.miras.bias import LinearNoBias


def default(v, d):
    """Return value if not None, otherwise return default."""
    return v if is_not_none(v) else d


def round_down_multiple(seq, mult):
    """Round sequence length down to nearest multiple."""
    return seq // mult * mult


def pack_with_inverse(t, pattern):
    """
    Pack tensor with einops and return inverse function.

    Useful for temporarily reshaping tensors and restoring original shape later.
    """
    packed, packed_shape = pack(t, pattern)

    def inverse(out, inv_pattern=None):
        return unpack(out, packed_shape, default(inv_pattern, pattern))

    return packed, inverse


def log(t, eps=1e-20):
    """Safe logarithm with minimum epsilon to avoid log(0)."""
    return torch.log(t.clamp(min=eps))


def gumbel_noise(t):
    """
    Generate Gumbel noise for Gumbel-max sampling.

    Gumbel-max trick: adding Gumbel noise to logits and taking argmax
    gives samples from the softmax distribution.
    """
    noise = torch.rand_like(t)
    return -log(-log(noise))


def gumbel_sample(t, temperature=1.0):
    """
    Sample from logits using Gumbel-max trick with temperature scaling.

    Temperature controls randomness: higher = more random, lower = more deterministic.
    """
    if temperature > 0.0:
        t = t / temperature + gumbel_noise(t)
    return t.argmax(dim=-1, keepdim=True)


def min_p_filter(logits, min_p=0.1):
    """
    Min-p filter for logits.

    Filters out tokens with probability below min_p * max_prob.
    This prevents sampling low-probability tokens while preserving
    the relative ordering of high-probability tokens.

    Reference: https://arxiv.org/abs/2407.01082
    """
    probs = logits.softmax(dim=-1)
    max_probs = probs.amax(dim=-1, keepdim=True)
    limit = min_p * max_probs
    return torch.where(probs < limit, float("-inf"), logits)


class GEGLU(nn.Module):
    """
    Gaussian Error Gated Linear Units activation.

    GEGLU splits the input in half, applies SiLU to one half (gate),
    and multiplies it with the other half. This gating mechanism helps
    control information flow through the network.

    Reference: https://arxiv.org/abs/2002.05202
    """

    def forward(self, x):
        x, gate = x.chunk(2, dim=-1)
        return F.silu(gate) * x


def FeedForward(dim, mult=4):
    """
    Standard transformer feedforward block with GEGLU activation.

    Architecture: RMSNorm -> Linear(expand) -> GEGLU -> Linear(project)
    The expansion factor is scaled by 2/3 to account for GEGLU's split.
    """
    dim_inner = int(dim * mult * 2 / 3)
    return nn.Sequential(
        nn.RMSNorm(dim),
        nn.Linear(dim, dim_inner * 2),
        GEGLU(),
        nn.Linear(dim_inner, dim),
    )


class MACTransformer(nn.Module):
    """
    Memory-as-Context Transformer.

    This is the main transformer architecture that integrates neural memory
    with segmented attention. The key innovation is that memories retrieved
    from the neural memory module are used as context for attention operations,
    enabling the model to leverage long-term information stored in memory.

    Architecture:
    - Token embeddings + axial positional embeddings
    - Long-term memory tokens interspersed between segments
    - Stack of transformer layers, each containing:
      * Neural memory (optional, for specified layers)
      * Segmented attention with local + long-term memory context
      * Feedforward network
    - Hyper connections for multi-stream residual processing
    - Output projection to vocabulary logits

    Attributes:
        token_emb: Token embedding layer
        axial_pos_emb: 2D axial positional embedding for segment-aware positions
        segment_len: Length of each attention segment
        num_longterm_mem_tokens: Number of learnable long-term memory tokens per segment
        longterm_mems: Learnable memory token embeddings
        attn_window_size: Total attention window (segment + long-term mem tokens)
        sliding_window_attn: Whether to use sliding window attention
        expand_streams: Function to expand residual streams for hyper connections
        reduce_streams: Function to reduce residual streams back to single stream
        layers: List of transformer layers (mem, attn, ff)
        neural_mem_segment_len: Chunk size for neural memory operations
        gate_attn_output: Whether to gate attention output with retrieved memories
        use_flex_attn: Whether to use PyTorch's flex_attention for efficiency

    Initialization process:
        1. Token Embeddings: Initialize token embeddings (defaults to standard embedding if not provided)
        2. Positional Embeddings: Axial positional embedding allows the model to distinguish between
           intra-segment positions (within a segment) and inter-segment positions (which segment in
           the sequence). This is crucial for segmented attention.
        3. Long-Term Memory Tokens: Learnable memory tokens that are interspersed between segments.
           These tokens can attend to and be attended by tokens in adjacent segments, providing a
           mechanism for long-range information flow.
        4. Attention Window Configuration: Attention window size includes both segment tokens and
           long-term memory tokens. Sliding window attention can be enabled to limit attention span
           for efficiency.
        5. Hyper Connections: Hyper connections allow multiple parallel residual streams, enabling
           more flexible information routing. When num_residual_streams == 1, this reduces to
           standard residual connections.
        6. Layer Construction: Build transformer layers with optional neural memory modules.
           Neural memory can be placed at specific layers or all layers. Weight residual allows
           cross-layer information flow in neural memory by blending weights from previous layers.
        7. Build Transformer Layers: Each layer contains: neural memory (optional), attention, and
           feedforward. Hyper connections are used to route information through each component.
        8. Output Projection: Final normalization and projection to vocabulary logits
        9. Memory-Attention Gating: When enabled, retrieved memories gate the attention output via
           sigmoid. Otherwise, memories are added directly to the residual stream.
        10. Auxiliary Buffers and Flags: Zero buffer for potential auxiliary losses.
            Flex attention requires PyTorch with CUDA support.
    """

    def __init__(
        self,
        *,
        config: TransformerConfig,
        neural_memory_model: Optional[nn.Module] = None,
        token_emb: Optional[nn.Module] = None,
    ):
        super().__init__()

        if not is_not_none(token_emb):
            token_emb = nn.Embedding(config.num_tokens, config.dim)
        self.token_emb = token_emb

        self.axial_pos_emb = ContinuousAxialPositionalEmbedding(dim=config.dim, num_axial_dims=2)

        self.segment_len = config.segment_len
        self.num_longterm_mem_tokens = config.num_longterm_mem_tokens
        has_longterm_mems = config.num_longterm_mem_tokens > 0
        self.longterm_mems = nn.Parameter(randn(config.num_longterm_mem_tokens, config.dim) * 0.02)

        self.sliding_window_attn = config.use_sliding_window_attn
        self.attn_window_size = config.segment_len + config.num_longterm_mem_tokens

        (
            init_hyper_conn,
            self.expand_streams,
            self.reduce_streams,
        ) = get_init_and_expand_reduce_stream_functions(
            config.num_residual_streams,
            dim=config.dim,
            add_stream_embed=True,
            disable=config.num_residual_streams == 1,
        )

        self.layers = nn.ModuleList([])
        self.neural_mem_segment_len = default(
            config.neural_mem.segment_len,
            config.num_longterm_mem_tokens + config.segment_len,
        )
        layers = tuple(range(1, config.depth + 1))
        neural_mem_layers = default(config.neural_mem.layers, layers)

        self.neural_mem_weight_residual = config.neural_mem.accept_weight_residual
        is_first_neural_mem = True

        for layer in layers:
            is_first = layer == 1

            attn = SegmentedAttention(
                dim=config.dim,
                dim_head=config.dim_head,
                heads=config.heads,
                segment_len=config.segment_len,
                use_flex_attn=config.use_flex_attn,
                accept_value_residual=not is_first,
                num_longterm_mem_tokens=config.num_longterm_mem_tokens,
                num_persist_mem_tokens=config.num_persist_mem_tokens,
                sliding=config.use_sliding_window_attn,
            )

            mem = None
            mem_qkv_layer_selector = None
            mem_hyper_conn = None
            if layer in neural_mem_layers:
                mem_hyper_conn = init_hyper_conn(add_branch_out_to_residual=not config.neural_mem.gate_attn_output)

                if not is_first and config.neural_mem.qkv_receives_diff_views:
                    num_layer_choices = (layer - 1) * 4 + 1
                    mem_qkv_layer_selector = nn.Sequential(
                        nn.RMSNorm(config.dim),
                        nn.Linear(config.dim, 3 * num_layer_choices),
                        Rearrange("... (views layers) -> views ... layers", views=3),
                        nn.Softmax(dim=-1),
                    )

                mem = NeuralMemory(
                    config=NeuralMemoryConfig(
                        dim=config.dim,
                        chunk_size=self.neural_mem_segment_len,
                        batch_size=config.neural_mem.batch_size,
                        qkv_receives_diff_views=True,
                        accept_weight_residual=config.neural_mem.accept_weight_residual and not is_first_neural_mem,
                        dim_head=config.neural_mem.dim_head,
                        heads=config.neural_mem.heads,
                        attn_pool_chunks=config.neural_mem.attn_pool_chunks,
                        momentum=config.neural_mem.momentum,
                        qk_rmsnorm=config.neural_mem.qk_rmsnorm,
                        momentum_order=config.neural_mem.momentum_order,
                        default_step_transform_max_lr=config.neural_mem.default_step_transform_max_lr,
                        use_accelerated_scan=config.neural_mem.use_accelerated_scan,
                        per_parameter_lr_modulation=config.neural_mem.per_parameter_lr_modulation,
                        apply_spectral_norm_surprises=config.neural_mem.apply_spectral_norm_surprises,
                    ),
                    model=neural_memory_model,
                )
                is_first_neural_mem = False

            ff = FeedForward(dim=config.dim, mult=config.ff_mult)

            self.layers.append(
                nn.ModuleList(
                    [
                        mem_hyper_conn,
                        init_hyper_conn(),
                        init_hyper_conn(),
                        mem_qkv_layer_selector,
                        mem,
                        attn,
                        ff,
                    ]
                )
            )

        self.norm = nn.RMSNorm(config.dim)
        self.to_logits = LinearNoBias(config.dim, config.num_tokens)

        self.gate_attn_output = config.neural_mem.gate_attn_output

        self.register_buffer("zero", tensor(0.0), persistent=False)

        assert not (
            config.use_flex_attn and not is_not_none(flex_attention)
        ), "you need to be on the latest pytorch with a cuda device available"
        self.use_flex_attn = config.use_flex_attn
        self.num_persist_mem_tokens = config.num_persist_mem_tokens

    def seq_index_is_longterm(self, seq_index):
        """
        Check if a sequence index corresponds to a long-term memory token.

        Long-term memory tokens are interspersed between segments, so they
        appear at positions after each segment within the attention window.
        """
        total_segment_len, segment_len = self.attn_window_size, self.segment_len
        return ((seq_index % total_segment_len + 1) - segment_len) > 0

    def seq_len_with_longterm_mem(self, seq_len):
        """
        Calculate total sequence length including interspersed long-term memory tokens.

        For each segment (except possibly the last), we add num_longterm_mem_tokens
        memory tokens. This accounts for the expanded sequence after memory insertion.
        """
        assert seq_len > 0
        segment_len, num_mem = self.segment_len, self.num_longterm_mem_tokens
        return ((seq_len - 1) // segment_len) * num_mem + seq_len

    @no_grad()
    def sample(
        self,
        prompt: torch.Tensor,
        seq_len: int,
        temperature=1.5,
        filter_fn: Callable = min_p_filter,
        filter_kwargs: dict = dict(
            min_p=0.1,
        ),
        show_progress=True,
        use_cache=False,
    ):
        """
        Autoregressively sample tokens from the model.

        Generates text by repeatedly:
        1. Forward pass to get logits for next token
        2. Apply filtering (e.g., min-p filter)
        3. Sample using Gumbel-max with temperature
        4. Append sampled token and repeat

        Supports KV caching for efficient generation by reusing
        attention states from previous tokens.

        Args:
            prompt: Initial token sequence [batch, prompt_len]
            seq_len: Total desired sequence length (including prompt)
            temperature: Sampling temperature (higher = more random)
            filter_fn: Function to filter logits before sampling
            filter_kwargs: Arguments for filter function
            show_progress: Whether to show progress bar
            use_cache: Whether to use KV caching for efficiency

        Returns:
            Generated tokens [batch, seq_len - prompt_len]

        Generation process:
            1. Cache Initialization: Precompute factorized positional embeddings if caching is
               enabled. This avoids recomputing them for each token during generation.
            2. Autoregressive Generation Loop: Generate one token at a time, appending to the
               sequence. When processing long-term memory tokens during inference, the forward pass
               may return None (early return), which we skip.
        """
        was_training = self.training
        self.eval()
        prompt_seq_len, out = prompt.shape[-1], prompt.clone()
        sample_num_times = max(0, seq_len - prompt_seq_len)

        cache = None
        factorized_pos_emb = None
        if use_cache:
            seq_len_with_mem = self.seq_len_with_longterm_mem(seq_len)
            axial_dims = self.axial_pos_emb.maybe_derive_outer_dim(seq_len_with_mem, (self.neural_mem_segment_len,))
            factorized_pos_emb = self.axial_pos_emb(axial_dims, return_factorized=True)

        with tqdm.tqdm(total=sample_num_times, disable=not show_progress) as pbar:
            while out.shape[-1] < seq_len:
                logits, next_cache = self.forward(
                    out,
                    disable_flex_attn=True,
                    cache=cache,
                    return_cache=True,
                    factorized_pos_emb=factorized_pos_emb,
                )
                if use_cache:
                    cache = next_cache
                if not is_not_none(logits):
                    continue
                logits = logits[:, -1]
                logits = filter_fn(logits, **filter_kwargs)
                sample = gumbel_sample(logits, temperature=temperature)
                out = torch.cat((out, sample), dim=-1)
                pbar.update(1)
        self.train(was_training)
        return out[..., prompt_seq_len:]

    def forward(
        self,
        x,
        return_loss=False,
        return_loss_breakdown=False,
        disable_flex_attn=False,
        cache=None,
        return_cache=False,
        factorized_pos_emb=None,
    ):
        """
        Forward pass through the Memory-as-Context Transformer.

        The forward pass processes input tokens through:
        1. Token embeddings and positional embeddings
        2. Interspersion of long-term memory tokens between segments
        3. Stack of transformer layers (neural memory + attention + feedforward)
        4. Output projection to vocabulary logits

        Supports:
        - Training mode: full sequence processing with loss computation
        - Inference mode: single-token processing with KV caching
        - Flex attention: efficient block-sparse attention when available

        Forward pass process:
            1. Input Preparation: For loss computation, shift sequence by one token for
               next-token prediction
            2. Extract Shape Information: Unpack batch size, sequence length, and attention
               configuration
            3. Token Embeddings: Convert token indices to dense embeddings
            4. Intersperse Long-Term Memory Tokens: Long-term memory tokens are inserted between
               segments to enable cross-segment information flow. The process: (1) Pad and segment
               the sequence, (2) Pack segments with memory tokens, (3) Unpack to get interspersed
               sequence. Remove padding tokens that were added for alignment.
            5. Positional Embeddings: Apply 2D axial positional embeddings to distinguish:
               - Intra-segment position (which token within a segment)
               - Inter-segment position (which segment in the sequence)
               This helps the model understand both local and global structure.
            6. Flex Attention Setup: Flex attention uses block-sparse masks for efficient attention
               computation. Only available on CUDA with recent PyTorch versions.
            7. KV Cache Initialization: For inference, maintain caches of attention KV pairs and
               neural memory states to avoid recomputing them for previously seen tokens.
            8. Residual State Initialization: Value residual (previous layer's attention values
               for residual connection), memory weight residual (previous layer's memory weights
               for cross-layer flow), memory input layers (accumulated residual stream points for
               QKV selection)
            9. Inference Mode Handling: During inference, process only the current token position
            10. Expand Residual Streams: Hyper connections require expanding to multiple parallel
                streams
            11. Process Transformer Layers: Each layer applies: neural memory (optional) ->
                attention -> feedforward with hyper connections routing information through each
                component
            12. Cache Management and Early Return: Prepare cache for next inference step. During
                inference, when processing long-term memory tokens (which don't produce logits),
                return early with updated cache to avoid unnecessary computation. Truncate KV
                cache to attention window size (only keep recent tokens). For non-sliding window
                attention, clear cache when it reaches a full window boundary (allows periodic
                cache reset). Early return for long-term memory tokens during inference (they don't
                produce logits, only update memory state)
            13. Reduce Residual Streams: Collapse multiple parallel streams back to single stream
            14. Remove Memory Tokens: During training, remove the interspersed long-term memory
                tokens to get back to the original sequence length. During inference, this is
                handled differently since we process one token at a time.
            15. Output Projection: Apply final normalization and project to vocabulary logits
            16. Return Results: Return logits, loss, or cache depending on mode

        Args:
            x: Input token sequence [batch, seq_len] or [batch, seq_len+1] if return_loss
            return_loss: Whether to compute and return cross-entropy loss
            return_loss_breakdown: (unused) For future loss component analysis
            disable_flex_attn: Force disable flex attention even if available
            cache: KV cache tuple (seq_index, kv_caches, neural_mem_caches) for inference
            return_cache: Whether to return updated cache for next inference step
            factorized_pos_emb: Precomputed positional embeddings for efficiency

        Returns:
            logits: [batch, seq_len, num_tokens] if not return_loss
            loss: Scalar tensor if return_loss=True
            cache: Updated cache tuple if return_cache=True
        """
        if return_loss:
            x, labels = x[:, :-1], x[:, 1:]

        (
            batch,
            seq_len,
            self.neural_mem_segment_len,
            segment_len,
            num_longterm_mem_tokens,
            attn_window_size,
        ) = (
            *x.shape,
            self.neural_mem_segment_len,
            self.segment_len,
            self.num_longterm_mem_tokens,
            self.attn_window_size,
        )
        seq_len_with_mem = self.seq_len_with_longterm_mem(seq_len)

        x = self.token_emb(x)

        x, inverse_segment = pad_and_segment_with_inverse(x, segment_len, inverse_remove_pad=False)
        mems = repeat(self.longterm_mems, "n d -> b n d", b=x.shape[0])
        x, inverse_pack_mems = pack_with_inverse((x, mems), "b * d")
        x = inverse_segment(x)
        x = x[:, :seq_len_with_mem]

        pos_emb = self.axial_pos_emb.forward_with_seq_len(
            seq_len_with_mem,
            (self.segment_len,),
            factorized=factorized_pos_emb,
        )
        x = x + pos_emb

        use_flex_attn = x.is_cuda and self.use_flex_attn and not disable_flex_attn
        flex_attn_fn = None
        if use_flex_attn:
            block_mask = create_mac_block_mask(
                seq_len_with_mem,
                self.attn_window_size,
                self.num_persist_mem_tokens,
                self.sliding_window_attn,
            )
            flex_attn_fn = partial(flex_attention, block_mask=block_mask)

        is_inferencing = is_not_none(cache)
        if not is_not_none(cache):
            cache = (seq_len_with_mem - 1, None, None)
        inference_seq_index, kv_caches, neural_mem_caches = cache
        kv_caches = iter(default(kv_caches, []))
        neural_mem_caches = iter(default(neural_mem_caches, []))
        next_kv_caches = []
        next_neural_mem_caches = []

        value_residual = None
        mem_weight_residual = None
        mem_input_layers = []

        if is_inferencing:
            ind = inference_seq_index
            x = x[:, ind : (ind + 1)]

        x = self.expand_streams(x)

        for (
            mem_hyper_conn,
            attn_hyper_conn,
            ff_hyper_conn,
            mem_qkv_layer_selector,
            mem,
            attn,
            ff,
        ) in self.layers:
            retrieved = None
            attn_out_gates = None
            next_neural_mem_cache = None

            if is_not_none(mem):
                mem_input, add_residual = mem_hyper_conn(x)

                if not is_not_none(mem_qkv_layer_selector):
                    qkv_mem_input = torch.stack((mem_input, mem_input, mem_input))
                else:
                    layers_to_choose_from = torch.stack((mem_input, *mem_input_layers))
                    selected = mem_qkv_layer_selector(mem_input)
                    qkv_mem_input = einsum(
                        layers_to_choose_from,
                        selected,
                        "l b n d, v b n l -> v b n d",
                    )

                retrieved, next_neural_mem_cache = mem.forward(
                    qkv_mem_input,
                    state=next(neural_mem_caches, None),
                    prev_weights=mem_weight_residual,
                )

                if self.neural_mem_weight_residual:
                    mem_weight_residual = next_neural_mem_cache.updates

                if self.gate_attn_output:
                    attn_out_gates = retrieved.sigmoid()
                else:
                    x = add_residual(retrieved)

            attn_in, add_residual = attn_hyper_conn(x)
            mem_input_layers.append(attn_in)
            attn_out, (values, next_kv_cache) = attn(
                attn_in,
                value_residual=value_residual,
                disable_flex_attn=disable_flex_attn,
                flex_attn_fn=flex_attn_fn,
                output_gating=attn_out_gates,
                cache=next(kv_caches, None),
            )
            mem_input_layers.append(attn_out)
            value_residual = default(value_residual, values)
            x = add_residual(attn_out)

            next_kv_caches.append(next_kv_cache)
            next_neural_mem_caches.append(next_neural_mem_cache)

            ff_in, add_ff_residual = ff_hyper_conn(x)
            mem_input_layers.append(ff_in)
            ff_out = ff(ff_in)
            mem_input_layers.append(ff_out)
            x = add_ff_residual(ff_out)

        if return_cache:
            next_kv_caches = torch.stack([torch.stack(kv_cache) for kv_cache in next_kv_caches])
            next_kv_caches = next_kv_caches[..., -attn_window_size:, :]
            kv_cache_length = next_kv_caches.shape[-2]
            if not self.sliding_window_attn and divisible_by(kv_cache_length, attn_window_size):
                next_kv_caches = next_kv_caches[..., 0:0, :]
            next_cache = (
                inference_seq_index + 1,
                next_kv_caches,
                next_neural_mem_caches,
            )
            is_longterm_mem = self.seq_index_is_longterm(inference_seq_index)
            if is_inferencing and is_longterm_mem:
                return None, next_cache

        x = self.reduce_streams(x)

        if not is_inferencing:
            x, inverse_segment = pad_and_segment_with_inverse(x, attn_window_size, inverse_remove_pad=False)
            x, _ = inverse_pack_mems(x)
            x = inverse_segment(x)
            x = x[:, :seq_len]

        x = self.norm(x)
        logits = self.to_logits(x)

        if not return_loss:
            if not return_cache:
                return logits
            return logits, next_cache
        return F.cross_entropy(rearrange(logits, "b n l -> b l n"), labels)
