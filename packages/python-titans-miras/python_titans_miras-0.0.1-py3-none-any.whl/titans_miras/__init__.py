"""
Titans-MIRAS: Test-Time Memorization for Long-Context Sequence Modeling

This package implements the Titans architecture and MIRAS framework from Google Research,
enabling AI models to maintain long-term memory by updating their core memory while actively running.

Main components:
- MACTransformer: The main Titans model architecture (MAC variant)
- NeuralMemory: The neural long-term memory module
- MIRAS: Framework for composing different memory strategies

MIRAS Variants:
- DEFAULT: Original Titans with MSE loss
- YAAD: Huber loss for robustness to outliers
- MONETA: Generalized p-norms for bias and retention
- MEMORA: Probability map constraints for stable updates

Einops Notation (used throughout the codebase):
    b  - batch
    h  - heads
    bh - batch and heads
    n  - sequence
    d  - feature dimension
    c  - intra-chunk
    w  - num memory network weight parameters
    o  - momentum orders
    u  - key / value updates (allowing a token to emit multiple key/values)

Example:
    >>> from titans_miras import MACTransformer, TransformerConfig, NeuralMemoryConfig
    >>> config = TransformerConfig(
    ...     num_tokens=256,
    ...     dim=512,
    ...     depth=6,
    ...     segment_len=64,
    ...     neural_mem=NeuralMemoryConfig(dim=512, heads=8)
    ... )
    >>> model = MACTransformer(config=config)
"""

__version__ = "0.0.1"

from titans_miras.config import (
    MIRASArchitecture,
    MIRASConfig,
    MemoraNormalizeMode,
    NeuralMemoryConfig,
    TransformerConfig,
)

from titans_miras.transformer.mac_transformer import MACTransformer

from titans_miras.neural_memory import NeuralMemory

from titans_miras.miras import (
    MIRAS,
    AttentionalBias,
    RetentionGate,
    MSEBias,
    HuberBias,
    GeneralizedNormBias,
    MSERetentionGate,
    GeneralizedNormRetentionGate,
    ProbabilityMapRetentionGate,
)


from titans_miras.memory.memory_mlp import MemoryMLP
from titans_miras.memory.memory_attention import MemoryAttention

__all__ = [
    "__version__",
    "MIRASArchitecture",
    "MIRASConfig",
    "MemoraNormalizeMode",
    "NeuralMemoryConfig",
    "TransformerConfig",
    "MACTransformer",
    "NeuralMemory",
    "MIRAS",
    "AttentionalBias",
    "RetentionGate",
    "MSEBias",
    "HuberBias",
    "GeneralizedNormBias",
    "MSERetentionGate",
    "GeneralizedNormRetentionGate",
    "ProbabilityMapRetentionGate",
    "MemoryMLP",
    "MemoryAttention",
]
