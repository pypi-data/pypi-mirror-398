#!/usr/bin/env python3
"""
MIRAS Variants Example

This example demonstrates how to use the four MIRAS architecture variants:
- DEFAULT: Original Titans with MSE loss
- YAAD: Huber loss for robustness to outliers
- MONETA: Generalized p-norms for bias and retention
- MEMORA: Probability map constraints for stable updates
"""

import torch
from titans_miras import (
    MACTransformer,
    TransformerConfig,
    NeuralMemoryConfig,
    MIRASConfig,
    MIRASArchitecture,
    MemoraNormalizeMode,
    MIRAS,
)


def create_model_with_miras(miras_config: MIRASConfig, device: torch.device):
    """Create a model with the specified MIRAS configuration."""
    config = TransformerConfig(
        num_tokens=256,
        dim=128,
        depth=2,
        segment_len=16,
        heads=2,
        neural_mem=NeuralMemoryConfig(
            dim=128,
            heads=2,
            depth=2,
        ),
        miras=miras_config,
    )
    return MACTransformer(config=config).to(device)


def main():
    # Determine device
    if torch.cuda.is_available():
        device = torch.device("cuda")
    elif torch.backends.mps.is_available():
        device = torch.device("mps")
    else:
        device = torch.device("cpu")

    print(f"Using device: {device}")
    print("=" * 60)

    # Sample input
    x = torch.randint(0, 256, (1, 64)).to(device)

    # 1. DEFAULT: Original Titans with MSE loss
    print("\n1. DEFAULT (MSE loss)")
    print("-" * 40)
    default_config = MIRASConfig(
        architecture=MIRASArchitecture.DEFAULT,
    )
    model = create_model_with_miras(default_config, device)
    loss = model(x, return_loss=True)
    print(f"   Loss: {loss.item():.4f}")

    # 2. YAAD: Huber loss for robustness to outliers
    print("\n2. YAAD (Huber loss)")
    print("-" * 40)
    yaad_config = MIRASConfig(
        architecture=MIRASArchitecture.YAAD,
        yaad_delta=1.0,  # Huber loss threshold
    )
    model = create_model_with_miras(yaad_config, device)
    loss = model(x, return_loss=True)
    print(f"   Delta: {yaad_config.yaad_delta}")
    print(f"   Loss: {loss.item():.4f}")

    # 3. MONETA: Generalized p-norms
    print("\n3. MONETA (Generalized p-norms)")
    print("-" * 40)
    moneta_config = MIRASConfig(
        architecture=MIRASArchitecture.MONETA,
        moneta_bias_p=1.5,  # p-norm for attentional bias
        moneta_gate_p=1.5,  # p-norm for retention gate
        moneta_regularization_weight=0.01,
    )
    model = create_model_with_miras(moneta_config, device)
    loss = model(x, return_loss=True)
    print(f"   Bias p-norm: {moneta_config.moneta_bias_p}")
    print(f"   Gate p-norm: {moneta_config.moneta_gate_p}")
    print(f"   Loss: {loss.item():.4f}")

    # 4. MEMORA: Probability map constraints
    print("\n4. MEMORA (Probability map constraints)")
    print("-" * 40)
    memora_config = MIRASConfig(
        architecture=MIRASArchitecture.MEMORA,
        memora_temperature=1.0,
        memora_normalize_mode=MemoraNormalizeMode.L2,
    )
    model = create_model_with_miras(memora_config, device)
    loss = model(x, return_loss=True)
    print(f"   Temperature: {memora_config.memora_temperature}")
    print(f"   Normalize mode: {memora_config.memora_normalize_mode}")
    print(f"   Loss: {loss.item():.4f}")

    # Using MIRAS factory methods directly
    print("\n" + "=" * 60)
    print("Using MIRAS factory methods:")
    print("-" * 40)

    miras_default = MIRAS.default()
    print(f"MIRAS.default(): {type(miras_default.attentional_bias).__name__}")

    miras_yaad = MIRAS.yaad(delta=1.0)
    print(f"MIRAS.yaad(): {type(miras_yaad.attentional_bias).__name__}")

    miras_moneta = MIRAS.moneta(bias_p=1.5, gate_p=1.5)
    print(f"MIRAS.moneta(): {type(miras_moneta.attentional_bias).__name__}")

    miras_memora = MIRAS.memora(temperature=1.0)
    print(f"MIRAS.memora(): {type(miras_memora.attentional_bias).__name__}")

    print("\nMIRAS variants example completed!")


if __name__ == "__main__":
    main()
