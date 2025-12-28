#!/usr/bin/env python3
"""
Basic usage example for Titans-MIRAS.

This example shows how to create and use a MACTransformer model
for language modeling.
"""

import torch
from titans_miras import (
    MACTransformer,
    TransformerConfig,
    NeuralMemoryConfig,
    MIRASConfig,
    MIRASArchitecture,
)


def main():
    # Determine device
    if torch.cuda.is_available():
        device = torch.device("cuda")
    elif torch.backends.mps.is_available():
        device = torch.device("mps")
    else:
        device = torch.device("cpu")

    print(f"Using device: {device}")

    # Configure the model
    # Using small dimensions for demonstration
    config = TransformerConfig(
        num_tokens=256,  # Vocabulary size (256 for byte-level)
        dim=256,  # Model dimension
        depth=4,  # Number of transformer layers
        segment_len=32,  # Segment length for memory operations
        heads=4,  # Number of attention heads
        neural_mem=NeuralMemoryConfig(
            dim=256,
            heads=4,
            depth=2,  # Depth of memory MLP
            momentum=True,  # Use momentum in memory updates
        ),
        miras=MIRASConfig(
            architecture=MIRASArchitecture.DEFAULT,
        ),
    )

    # Create model
    model = MACTransformer(config=config).to(device)

    # Count parameters
    num_params = sum(p.numel() for p in model.parameters())
    print(f"Model parameters: {num_params:,}")

    # Create sample input (byte-level text)
    batch_size = 2
    seq_len = 128
    x = torch.randint(0, 256, (batch_size, seq_len)).to(device)

    print(f"Input shape: {x.shape}")

    # Forward pass (get logits)
    with torch.no_grad():
        logits = model(x)

    print(f"Output logits shape: {logits.shape}")

    # Forward pass with loss computation
    loss = model(x, return_loss=True)
    print(f"Loss: {loss.item():.4f}")

    # Training step example
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4)

    model.train()
    for step in range(3):
        optimizer.zero_grad()
        loss = model(x, return_loss=True)
        loss.backward()
        optimizer.step()
        print(f"Step {step + 1}: loss = {loss.item():.4f}")

    print("\nBasic usage example completed!")


if __name__ == "__main__":
    main()
