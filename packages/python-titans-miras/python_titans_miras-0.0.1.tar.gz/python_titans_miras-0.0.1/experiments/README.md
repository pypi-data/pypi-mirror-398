# Experiments

This directory contains reproducibility experiments for the Titans + MIRAS paper.

## Prerequisites

Install the package with dev dependencies:

```bash
pip install python-titans-miras[dev]
# or install from source:
pip install -e ".[dev]"
# or with uv:
uv pip install -e ".[dev]"
```

## Available Experiments

All experiments can be run using the unified entry point `scripts/run_experiments.py`:

```bash
# See all available experiments
python scripts/run_experiments.py --help
```

### 01. MIRAS Variant Comparison

Compare all four MIRAS architectures (DEFAULT, YAAD, MONETA, MEMORA) on language modeling.

```bash
# Using unified entry point (recommended)
python scripts/run_experiments.py miras-variants --scale small --num_batches 10000

# Or run directly
python experiments/01_miras_variants/run_comparison.py --scale small --num_batches 10000
```

### 02. Memory Depth Ablation

Study the effect of memory model depth on performance.

```bash
# Using unified entry point
python scripts/run_experiments.py memory-depth --scale small

# Or run directly
python experiments/02_memory_depth/run_ablation.py --scale small
```

### 03. Language Modeling

Train and evaluate on standard benchmarks:

```bash
# enwik8 (byte-level) - using unified entry point
python scripts/run_experiments.py train-enwik8 --scale small --num_batches 50000

# WikiText-103 (word-level)
python scripts/run_experiments.py train-wikitext --scale small

# Evaluate perplexity
python scripts/run_experiments.py eval-perplexity --checkpoint path/to/model.pt

# Or run directly
python experiments/03_language_modeling/train_enwik8.py --scale small
python experiments/03_language_modeling/train_wikitext.py --scale small
python experiments/03_language_modeling/eval_perplexity.py --checkpoint path/to/model.pt
```

### 04. Long-Context Evaluation

Evaluate on BABILong benchmark for extreme long-context reasoning:

```bash
# Using unified entry point
python scripts/run_experiments.py babilong --scale small --max_context 16384
python scripts/run_experiments.py scaling-analysis --scale small

# Or run directly
python experiments/04_longcontext/run_babilong.py --scale small --max_context 16384
python experiments/04_longcontext/scaling_analysis.py --scale small
```

### 05. Baselines

See [05_baselines/README.md](05_baselines/README.md) for instructions on comparing against Transformer++, Mamba-2, and other baselines.

## Configuration

Experiment configurations are in `configs/`:
- `scales.py`: Model scale configurations (tiny, small, medium, large)
- `miras_variants.py`: MIRAS architecture configurations

## Results

Results are saved to `results/` (gitignored). Each experiment creates a timestamped subdirectory with:
- Training logs
- Model checkpoints
- Metrics JSON files

