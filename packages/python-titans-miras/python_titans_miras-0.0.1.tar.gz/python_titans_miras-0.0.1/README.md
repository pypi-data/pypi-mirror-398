# Titans-MIRAS

[![PyPI version](https://img.shields.io/pypi/v/python-titans-miras.svg)](https://pypi.org/project/python-titans-miras/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![PyTorch 2.0+](https://img.shields.io/badge/pytorch-2.0+-ee4c2c.svg)](https://pytorch.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Implementation of the [Titans-MIRAS system](https://research.google/blog/titans-miras-helping-ai-have-long-term-memory/) from Google Research, enabling test-time memorization and long-term memory in AI for long-context sequence modeling.

## Overview

Titans introduces a neural long-term memory module that learns to memorize information as data streams in, enabling efficient handling of extremely long contexts (2M+ tokens). MIRAS provides a theoretical framework for designing memory mechanisms through four key components:

1. **Memory Architecture**: Structure storing information (vector, matrix, or deep MLP)
2. **Attentional Bias**: Learning objective determining what to prioritize
3. **Retention Gate**: Regularizer balancing new learning vs. past knowledge
4. **Memory Algorithm**: Optimization algorithm for updating memory

### MIRAS Variants

| Variant | Description | Use Case |
|---------|-------------|----------|
| **DEFAULT** | Original Titans with MSE loss | General purpose |
| **YAAD** | Huber loss for robustness | Noisy/outlier-heavy data |
| **MONETA** | Generalized p-norms | Enhanced expressivity |
| **MEMORA** | Probability map constraints | Maximum stability |

## Installation

```bash
pip install python-titans-miras
```

Or install from source:

```bash
git clone https://github.com/jonlukewatts/titans-miras.git
cd titans-miras
pip install -e .
```

With development dependencies:

```bash
pip install -e ".[dev]"
```

## Quick Start

```python
import torch
from titans_miras import (
    MACTransformer,
    TransformerConfig,
    NeuralMemoryConfig,
    MIRASConfig,
    MIRASArchitecture,
)

# Configure the model
config = TransformerConfig(
    num_tokens=256,           # Vocabulary size (256 for byte-level)
    dim=512,                  # Model dimension
    depth=6,                  # Number of transformer layers
    segment_len=64,           # Segment length for memory operations
    neural_mem=NeuralMemoryConfig(
        dim=512,
        heads=8,
        depth=2,              # Depth of memory MLP
    ),
    miras=MIRASConfig(
        architecture=MIRASArchitecture.DEFAULT,  # or YAAD, MONETA, MEMORA
    ),
)

# Create model
model = MACTransformer(config=config)

# Forward pass
x = torch.randint(0, 256, (1, 512))  # (batch, seq_len)
logits = model(x)                     # (batch, seq_len, vocab_size)

# Training with loss
loss = model(x, return_loss=True)
loss.backward()
```

### Using Different MIRAS Variants

```python
from titans_miras import MIRASConfig, MIRASArchitecture

# YAAD: Robust to outliers
yaad_config = MIRASConfig(
    architecture=MIRASArchitecture.YAAD,
    yaad_delta=1.0,  # Huber loss threshold
)

# MONETA: Generalized p-norms
moneta_config = MIRASConfig(
    architecture=MIRASArchitecture.MONETA,
    moneta_bias_p=1.5,
    moneta_gate_p=1.5,
)

# MEMORA: Probability map constraints
memora_config = MIRASConfig(
    architecture=MIRASArchitecture.MEMORA,
    memora_temperature=1.0,
)
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  MACTransformer              │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   Token     │    │   Neural    │    │  Segmented  │  │
│  │  Embedding  │───▶│   Memory    │───▶│  Attention  │  │
│  └─────────────┘    └─────────────┘    └─────────────┘  │
│                            │                  │          │
│                     ┌──────▼──────┐          │          │
│                     │   Memory    │          │          │
│                     │    MLP      │◀─────────┘          │
│                     │  (stores &  │                     │
│                     │  retrieves) │                     │
│                     └─────────────┘                     │
└─────────────────────────────────────────────────────────┘
```

The Neural Memory module stores information in the weights of a small MLP, which are updated online during the forward pass using gradient-based learning. This allows the model to "memorize" important information and retrieve it later.

## Einops Notation

The codebase uses [einops](https://github.com/arogozhnikov/einops) for tensor operations. Here are the dimension conventions:

| Symbol | Meaning |
|--------|---------|
| `b` | batch |
| `h` | heads |
| `bh` | batch and heads (combined) |
| `n` | sequence length |
| `d` | feature dimension |
| `c` | intra-chunk position |
| `w` | number of memory network weight parameters |
| `o` | momentum orders |
| `u` | key/value updates per token |

Example usage in the codebase:

```python
# Split into heads
x = rearrange(x, 'b n (h d) -> b h n d', h=num_heads)

# Compute attention
attn = einsum('b h n d, b h m d -> b h n m', q, k)

# Merge heads back
x = rearrange(x, 'b h n d -> b n (h d)')
```

## Configuration Reference

### TransformerConfig

| Parameter | Type | Description |
|-----------|------|-------------|
| `num_tokens` | int | Vocabulary size |
| `dim` | int | Model hidden dimension |
| `depth` | int | Number of transformer layers |
| `segment_len` | int | Segment length for memory operations |
| `heads` | int | Number of attention heads (default: 8) |
| `ff_mult` | int | Feed-forward dimension multiplier (default: 4) |
| `num_longterm_mem_tokens` | int | Long-term memory tokens (default: 0) |
| `num_persist_mem_tokens` | int | Persistent memory tokens (default: 0) |

### NeuralMemoryConfig

| Parameter | Type | Description |
|-----------|------|-------------|
| `dim` | int | Neural memory dimension |
| `heads` | int | Number of memory heads (default: 1) |
| `depth` | int | Depth of memory MLP (default: 2) |
| `chunk_size` | int | Chunk size for operations (default: 1) |
| `momentum` | bool | Use momentum in updates (default: True) |
| `max_lr` | float | Max learning rate for memory (default: 0.1) |

See [`titans_miras/config.py`](titans_miras/config.py) for the complete configuration reference.

## Training

For training models, use the unified training script:

```bash
python scripts/train.py --config path/to/config.yaml
```

See [`scripts/train.py`](scripts/train.py) for available options.

## Experiments

The `experiments/` directory contains scripts to reproduce paper results. Use the unified entry point:

```bash
# Compare MIRAS variants
python scripts/run_experiments.py miras-variants --scale small

# Memory depth ablation
python scripts/run_experiments.py memory-depth --scale small

# Language modeling (enwik8)
python scripts/run_experiments.py train-enwik8 --scale small

# Long-context evaluation
python scripts/run_experiments.py babilong --scale small
```

You can also run experiments directly:

```bash
python experiments/01_miras_variants/run_comparison.py --scale small
```

See [`experiments/README.md`](experiments/README.md) for detailed instructions.

## Research Context

### Titans: Learning to Memorize at Test Time

The Transformer architecture revolutionized sequence modeling with attention, but computational cost increases quadratically with sequence length. Titans addresses this by introducing a **neural long-term memory module** that:

- Uses a deep neural network (MLP) as memory, providing higher expressive power than fixed-size vectors/matrices
- Learns to recognize and retain important relationships across extremely long sequences
- Employs a **"surprise metric"** (gradient magnitude) to prioritize memorable information
- Incorporates **momentum** and **adaptive forgetting** for stable long-term memory

### MIRAS: A Unified Framework

MIRAS (Memory-Informed Retrieval and Storage) provides a theoretical blueprint showing that major sequence modeling architectures are essentially associative memory modules. Key insights:

- Transformers, RNNs, and SSMs can be viewed through the lens of associative memory
- Different loss functions (MSE, Huber, p-norms) lead to different memory properties
- Retention gates act as regularizers balancing old vs. new information
