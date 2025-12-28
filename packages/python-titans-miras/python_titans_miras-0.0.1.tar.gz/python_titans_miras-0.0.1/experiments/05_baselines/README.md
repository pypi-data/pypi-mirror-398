# Baseline Models for Comparison

This directory contains instructions and utilities for comparing Titans/MIRAS against baseline architectures from the paper.

## Baseline Architectures

The Titans/MIRAS papers compare against the following baselines:

### 1. Transformer++
A modern Transformer implementation with:
- RoPE positional encodings
- RMSNorm
- SwiGLU activations
- Improved initialization

**Implementation**: Use the `x-transformers` library (already a dependency):
```python
from x_transformers import TransformerWrapper, Decoder

model = TransformerWrapper(
    num_tokens=256,
    max_seq_len=8192,
    attn_layers=Decoder(
        dim=768,
        depth=16,
        heads=12,
        rotary_pos_emb=True,
        attn_flash=True,
    )
)
```

### 2. Mamba-2
State Space Model with selective scan:
- Linear time complexity
- Fixed-size state compression
- Efficient on long sequences

**Installation**:
```bash
pip install mamba-ssm
```

**Usage**:
```python
from mamba_ssm import Mamba2

model = Mamba2(
    d_model=768,
    d_state=128,
    d_conv=4,
    expand=2,
)
```

### 3. Gated DeltaNet
Linear attention with delta rule updates:
- O(n) complexity
- Improved expressivity over vanilla linear attention

**Implementation**: See the official repository:
https://github.com/proger/deltanets

## Running Baseline Comparisons

### Quick Comparison (Small Scale)

Train all models on enwik8 with comparable parameter counts:

```bash
# Train Titans/MIRAS variants
python experiments/01_miras_variants/run_comparison.py --scale small --num_batches 10000

# Train Transformer++ baseline (requires custom script)
python experiments/05_baselines/train_transformer.py --scale small --num_batches 10000

# Train Mamba-2 baseline (requires mamba-ssm)
python experiments/05_baselines/train_mamba.py --scale small --num_batches 10000
```

### Full Comparison (Paper Scale)

For reproducing paper results at 360M and 760M parameters:

```bash
# Medium scale (~360M params)
python experiments/01_miras_variants/run_comparison.py --scale medium --num_batches 100000

# Large scale (~760M params)
python experiments/03_language_modeling/train_enwik8.py --scale large --num_batches 200000
```

## Model Size Reference

| Model | Small | Medium | Large |
|-------|-------|--------|-------|
| Titans (MAC) | ~50M | ~360M | ~760M |
| Transformer++ | ~50M | ~360M | ~760M |
| Mamba-2 | ~50M | ~360M | ~760M |

## Expected Results

Based on the Titans/MIRAS papers, expected relative performance:

### Language Modeling (enwik8, BPB - lower is better)

| Model | Small | Medium |
|-------|-------|--------|
| Transformer++ | 1.05 | 0.95 |
| Mamba-2 | 1.02 | 0.93 |
| Titans (default) | 0.99 | 0.90 |
| Titans (YAAD) | 0.98 | 0.89 |

### Long Context (BABILong, Accuracy - higher is better)

| Model | 4K | 64K | 256K | 1M |
|-------|-----|------|------|-----|
| GPT-4 | 95% | 60% | 30% | 15% |
| Mamba-2 | 90% | 70% | 45% | 25% |
| Titans | 95% | 85% | 75% | 60% |

## Adding New Baselines

To add a new baseline model for comparison:

1. Create a training script in this directory (e.g., `train_newmodel.py`)
2. Ensure it uses the same:
   - Dataset loading from `experiments/utils/datasets.py`
   - Metrics from `experiments/utils/metrics.py`
   - Logging from `experiments/utils/logging.py`
3. Match the parameter count to existing models for fair comparison
4. Report the same metrics (perplexity, BPB, accuracy)

## Data Preparation

### enwik8
```bash
# Download and extract
wget https://mattmahoney.net/dc/enwik8.zip
unzip enwik8.zip
gzip enwik8
mv enwik8.gz dev/
```

### WikiText-103
```bash
# Using HuggingFace datasets
python -c "
from datasets import load_dataset
ds = load_dataset('wikitext', 'wikitext-103-v1')
# Tokenize and save as .pt files
"
```

### BABILong
```bash
# Clone official repository
git clone https://github.com/booydar/babilong
```

## Notes

- For fair comparison, all models should use the same:
  - Optimizer (AdoptAtan2)
  - Learning rate schedule
  - Batch size and sequence length
  - Number of training steps

- The key advantage of Titans is at long contexts (>64K tokens) where fixed-state models like Mamba degrade while Titans maintains accuracy.

- MIRAS variants (YAAD, MONETA, MEMORA) show improvements primarily on noisy/inconsistent data due to their robust loss functions.

