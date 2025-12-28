#!/usr/bin/env python3
"""
Training Example for Titans-MIRAS

This example demonstrates a complete training loop with:
- Data loading
- Model creation
- Training with gradient accumulation
- Validation
- Checkpointing
"""

import os
import gzip
from pathlib import Path

import torch
from torch.utils.data import Dataset, DataLoader
from tqdm import tqdm

from titans_miras import (
    MACTransformer,
    TransformerConfig,
    NeuralMemoryConfig,
    MIRASConfig,
    MIRASArchitecture,
)


class TextDataset(Dataset):
    """Simple text dataset that samples random sequences."""

    def __init__(self, data: torch.Tensor, seq_len: int):
        self.data = data
        self.seq_len = seq_len

    def __len__(self):
        return len(self.data) // self.seq_len

    def __getitem__(self, idx):
        start = torch.randint(0, len(self.data) - self.seq_len - 1, (1,)).item()
        return self.data[start : start + self.seq_len + 1].long()


def load_enwik8(path: str = "dev/enwik8.gz"):
    """Load enwik8 dataset if available, otherwise create synthetic data."""
    if os.path.exists(path):
        with gzip.open(path, "rt", encoding="utf-8") as f:
            data = f.read()
        data = torch.tensor([ord(c) for c in data], dtype=torch.uint8)
        print(f"Loaded enwik8: {len(data):,} bytes")
    else:
        # Create synthetic data for demonstration
        print("enwik8 not found, using synthetic data")
        data = torch.randint(0, 256, (100_000,), dtype=torch.uint8)

    # Split into train/val
    n = len(data)
    train_data = data[: int(0.9 * n)]
    val_data = data[int(0.9 * n) :]

    return train_data, val_data


def compute_perplexity(loss: float) -> float:
    """Compute perplexity from cross-entropy loss."""
    return torch.exp(torch.tensor(loss)).item()


def main():
    # Configuration
    batch_size = 4
    seq_len = 128
    num_epochs = 1
    num_steps = 100
    learning_rate = 1e-4
    gradient_accumulate_every = 2
    validate_every = 20
    save_every = 50

    # Determine device
    if torch.cuda.is_available():
        device = torch.device("cuda")
    elif torch.backends.mps.is_available():
        device = torch.device("mps")
    else:
        device = torch.device("cpu")

    print(f"Using device: {device}")
    print("=" * 60)

    # Load data
    train_data, val_data = load_enwik8()

    train_dataset = TextDataset(train_data, seq_len)
    val_dataset = TextDataset(val_data, seq_len)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

    # Create model
    config = TransformerConfig(
        num_tokens=256,
        dim=256,
        depth=4,
        segment_len=32,
        heads=4,
        neural_mem=NeuralMemoryConfig(
            dim=256,
            heads=4,
            depth=2,
            momentum=True,
        ),
        miras=MIRASConfig(
            architecture=MIRASArchitecture.DEFAULT,
        ),
    )

    model = MACTransformer(config=config).to(device)

    num_params = sum(p.numel() for p in model.parameters())
    print(f"Model parameters: {num_params:,}")

    # Optimizer
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)

    # Training loop
    print("\nStarting training...")
    print("-" * 60)

    model.train()
    train_iter = iter(train_loader)

    running_loss = 0.0
    step = 0

    pbar = tqdm(total=num_steps, desc="Training")

    while step < num_steps:
        # Gradient accumulation
        accumulated_loss = 0.0

        for _ in range(gradient_accumulate_every):
            try:
                batch = next(train_iter)
            except StopIteration:
                train_iter = iter(train_loader)
                batch = next(train_iter)

            batch = batch.to(device)
            loss = model(batch, return_loss=True)
            loss = loss / gradient_accumulate_every
            loss.backward()
            accumulated_loss += loss.item()

        # Gradient clipping
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)

        optimizer.step()
        optimizer.zero_grad()

        running_loss += accumulated_loss
        step += 1

        pbar.update(1)
        pbar.set_postfix({"loss": f"{accumulated_loss:.4f}"})

        # Validation
        if step % validate_every == 0:
            model.eval()
            val_losses = []

            with torch.no_grad():
                for i, batch in enumerate(val_loader):
                    if i >= 10:  # Limit validation batches
                        break
                    batch = batch.to(device)
                    val_loss = model(batch, return_loss=True)
                    val_losses.append(val_loss.item())

            avg_val_loss = sum(val_losses) / len(val_losses)
            val_ppl = compute_perplexity(avg_val_loss)

            print(f"\n  Step {step}: val_loss={avg_val_loss:.4f}, val_ppl={val_ppl:.2f}")

            model.train()

        # Save checkpoint
        if step % save_every == 0:
            checkpoint_path = f"checkpoint_step_{step}.pt"
            torch.save(
                {
                    "step": step,
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "loss": accumulated_loss,
                },
                checkpoint_path,
            )
            print(f"\n  Saved checkpoint: {checkpoint_path}")

    pbar.close()

    # Final statistics
    avg_train_loss = running_loss / num_steps
    train_ppl = compute_perplexity(avg_train_loss)

    print("\n" + "=" * 60)
    print(f"Training completed!")
    print(f"Average train loss: {avg_train_loss:.4f}")
    print(f"Train perplexity: {train_ppl:.2f}")


if __name__ == "__main__":
    main()
