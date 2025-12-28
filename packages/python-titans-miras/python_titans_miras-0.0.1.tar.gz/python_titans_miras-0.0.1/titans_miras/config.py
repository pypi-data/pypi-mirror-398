from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from titans_miras.miras.config import MIRASConfig, MemoraNormalizeMode, MIRASArchitecture


class NeuralMemoryConfig(BaseModel):

    accept_weight_residual: bool = Field(
        default=False,
        description="when true, accepts contributions from weights of previous neural mem layer for improved performance (inspired by value residual learning free lunch paper)",
    )
    add_value_residual: bool = Field(
        default=False,
        description="when true, adds value residual to the neural memory output",
    )

    attn_pool_chunks: bool = Field(
        default=False,
        description="when true, uses attention pooling for chunk-derived momentum, per-layer learning rate modulation, and decay",
    )
    batch_size: int | None = Field(
        default=None,
        description="controls memory weight update frequency during sequence traversal; smaller values update more often",
    )
    chunk_size: int | tuple[int, int] = Field(
        default=1,
        description="chunk granularity for learning rate and momentum; smaller values provide finer control",
    )
    default_model_kwargs: dict = Field(
        default_factory=lambda: dict(depth=2, expansion_factor=4.0),
        description="kwargs passed to MemoryMLP constructor (e.g., depth=2, expansion_factor=4.0)",
    )
    default_step_transform_max_lr: float = Field(
        default=1.0, description="maximum learning rate for the step transform function"
    )
    depth: int = Field(default=2, description="number of layers in the neural memory model")
    dim: int = Field(default=64, description="hidden dimension of the neural memory model")
    dim_head: int | None = Field(
        default=None,
        description="dimension per attention head in the neural memory model",
    )
    gate_attn_output: bool = Field(
        default=False,
        description="when true, gates the attention output with retrieved memories",
    )
    gated_transition: bool = Field(
        default=False,
        description="when true, applies a gated transition function in the neural memory model",
    )
    heads: int = Field(default=1, description="number of attention heads in the neural memory model")
    init_adaptive_step_bias: float | None = Field(
        default=None,
        description="initial bias for adaptive step size; None uses default initialization",
    )
    init_decay_bias: float | None = Field(
        default=None,
        description="initial bias for memory decay; None uses default initialization",
    )
    init_momentum_bias: float | None = Field(
        default=None,
        description="initial bias for momentum; None uses default initialization",
    )
    layers: Optional[tuple[int, ...]] = Field(
        default=None,
        description="transformer layer indices with neural memory (e.g., (2, 4, 6) adds memory to layers 2, 4, 6)",
    )
    learned_combine_include_zeroth: bool = Field(
        default=False,
        description="when true, includes zeroth-order term in learned momentum combination",
    )
    learned_momentum_combine: bool = Field(
        default=False,
        description="when true, learns parameters to combine momentum orders",
    )
    max_grad_norm: float | None = Field(default=None, description="gradient clipping threshold; None disables clipping")
    max_lr: float = Field(default=1e-1, description="maximum learning rate for neural memory updates")
    max_mem_layer_modulation: float = Field(
        default=1.0,
        description="maximum modulation factor for memory layer contributions",
    )
    mem_model_norm_add_residual: bool = Field(
        default=True,
        description="when true, adds residual connection to memory model normalization",
    )
    momentum: bool = Field(
        default=True,
        description="when true, uses momentum in neural memory weight updates",
    )
    momentum_order: int = Field(
        default=1,
        description="order of momentum (1=standard momentum, higher=higher-order derivatives)",
    )
    num_kv_per_token: int = Field(default=1, description="number of key-value pairs generated per input token")

    per_head_learned_parameters: bool = Field(
        default=True,
        description="when true, learns separate parameters for each attention head",
    )
    per_parameter_lr_modulation: bool = Field(
        default=False,
        description="when true, allows outer network to control learning rate per weight matrix of memory network",
    )

    post_rmsnorm: bool = Field(
        default=False,
        description="when true, applies RMSNorm after neural memory operations",
    )
    pre_rmsnorm: bool = Field(
        default=True,
        description="when true, applies RMSNorm before neural memory operations",
    )
    qk_rmsnorm: bool = Field(
        default=False,
        description="when true, applies RMSNorm to query and key matrices",
    )
    qkv_receives_diff_views: bool = Field(
        default=False,
        description="when true, allows network to use hyper-connections for different previous layer inputs as keys/values, improving expressiveness beyond Wk @ Wv mapping",
    )
    segment_len: Optional[int] = Field(
        default=None,
        description="segment length for memory operations; smaller values provide finer granularity for learning rate and momentum",
    )
    apply_spectral_norm_surprises: bool = Field(
        default=False,
        description="when true, applies spectral normalization to improve memory model stability",
    )
    use_accelerated_scan: bool = Field(
        default=False,
        description="when true, uses accelerated scan for faster computation (automatically disabled on MPS devices)",
    )

    miras: Optional[MIRASConfig] = Field(
        default=None,
        description="MIRAS framework configuration for memory loss variants",
    )


class TransformerConfig(BaseModel):
    num_tokens: int = Field(description="vocabulary size (e.g., 256 for byte-level models like enwik8)")
    dim: int = Field(description="hidden dimension of the transformer model")
    dim_head: int = Field(default=64, description="dimension per attention head")
    depth: int = Field(description="number of transformer layers")
    segment_len: int = Field(
        description="segment length for processing; sequences are divided into segments of this size for memory operations"
    )
    neural_mem: NeuralMemoryConfig = Field(description="configuration for the neural memory module")

    miras: MIRASConfig = Field(
        default=MIRASConfig(),
        description="MIRAS framework configuration for memory loss variants",
    )
    num_longterm_mem_tokens: int = Field(
        default=0,
        description="number of long-term memory tokens that persist across segments in the memory hierarchy",
    )
    num_persist_mem_tokens: int = Field(
        default=0,
        description="number of persistent memory tokens that carry fixed learned context",
    )

    heads: int = Field(default=8, description="number of attention heads")
    ff_mult: int = Field(
        default=4,
        description="feed-forward hidden dimension multiplier (ff_dim = dim * ff_mult)",
    )
    num_residual_streams: int = Field(
        default=4,
        description="number of parallel residual streams for hyper-connections",
    )

    use_flex_attn: bool = Field(
        default=False,
        description="when true, uses FlexAttention for more flexible attention patterns",
    )
    use_sliding_window_attn: bool = Field(
        default=False,
        description="when true, uses sliding window attention to limit attention span and reduce memory",
    )


__all__ = [
    "NeuralMemoryConfig",
    "TransformerConfig",
    "MIRASConfig",
    "MemoraNormalizeMode",
    "MIRASArchitecture",
]
