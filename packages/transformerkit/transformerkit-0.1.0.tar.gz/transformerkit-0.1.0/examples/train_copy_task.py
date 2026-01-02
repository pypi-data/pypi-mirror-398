"""
Training script for the Transformer model.
Demonstrates training on a simple copy task.
"""

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset

from transformerkit import create_transformer
from transformerkit.config import TransformerConfig
from transformerkit.utils import create_padding_mask, create_target_mask


class CopyTaskDataset(Dataset):
    """
    Simple copy task dataset.
    Model learns to copy input sequence to output.
    """

    def __init__(self, num_samples=10000, seq_len=10, vocab_size=100):
        """
        Args:
            num_samples: Number of training samples
            seq_len: Sequence length
            vocab_size: Vocabulary size
        """
        self.num_samples = num_samples
        self.seq_len = seq_len
        self.vocab_size = vocab_size

        # Generate random sequences (avoiding 0, 1, 2 for special tokens)
        self.data = np.random.randint(3, vocab_size, size=(num_samples, seq_len))

    def __len__(self):
        return self.num_samples

    def __getitem__(self, idx):
        """
        Returns source and target (same sequence for copy task).
        """
        seq = self.data[idx]

        # Source: [seq]
        src = torch.tensor(seq, dtype=torch.long)

        # Target input: [<start>, seq] - length = seq_len + 1
        # Target output: [seq, <end>] - length = seq_len + 1
        # Using 1 as <start> token, 2 as <end> token
        tgt_input = torch.cat([torch.tensor([1]), torch.tensor(seq, dtype=torch.long)])
        tgt_output = torch.cat([torch.tensor(seq, dtype=torch.long), torch.tensor([2])])

        return src, tgt_input, tgt_output


def train_epoch(model, dataloader, optimizer, criterion, device):
    """
    Train for one epoch.

    Args:
        model: Transformer model
        dataloader: Training data loader
        optimizer: Optimizer
        criterion: Loss function
        device: Device to train on

    Returns:
        avg_loss: Average loss for the epoch
    """
    model.train()
    total_loss = 0

    for batch_idx, (src, tgt_input, tgt_output) in enumerate(dataloader):
        src = src.to(device)
        tgt_input = tgt_input.to(device)
        tgt_output = tgt_output.to(device)

        # Create masks
        src_mask = create_padding_mask(src, pad_idx=0)
        tgt_mask = create_target_mask(tgt_input, pad_idx=0)

        # Forward pass
        output = model(src, tgt_input, src_mask, tgt_mask)

        # Reshape for loss calculation
        # output: (batch_size, seq_len, vocab_size)
        # tgt_output: (batch_size, seq_len)
        output = output.reshape(-1, output.size(-1))
        tgt_output = tgt_output.reshape(-1)

        # Calculate loss
        loss = criterion(output, tgt_output)

        # Backward pass
        optimizer.zero_grad()
        loss.backward()

        # Gradient clipping
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)

        optimizer.step()

        total_loss += loss.item()

        if (batch_idx + 1) % 100 == 0:
            print(f"  Batch {batch_idx + 1}/{len(dataloader)}, Loss: {loss.item():.4f}")

    return total_loss / len(dataloader)


def evaluate(model, dataloader, criterion, device):
    """
    Evaluate model on validation set.

    Args:
        model: Transformer model
        dataloader: Validation data loader
        criterion: Loss function
        device: Device to evaluate on

    Returns:
        avg_loss: Average loss
        accuracy: Accuracy
    """
    model.eval()
    total_loss = 0
    correct = 0
    total = 0

    with torch.no_grad():
        for src, tgt_input, tgt_output in dataloader:
            src = src.to(device)
            tgt_input = tgt_input.to(device)
            tgt_output = tgt_output.to(device)

            # Create masks
            src_mask = create_padding_mask(src, pad_idx=0)
            tgt_mask = create_target_mask(tgt_input, pad_idx=0)

            # Forward pass
            output = model(src, tgt_input, src_mask, tgt_mask)

            # Calculate loss
            output_flat = output.reshape(-1, output.size(-1))
            tgt_flat = tgt_output.reshape(-1)
            loss = criterion(output_flat, tgt_flat)
            total_loss += loss.item()

            # Calculate accuracy
            predictions = output.argmax(dim=-1)
            correct += (predictions == tgt_output).sum().item()
            total += tgt_output.numel()

    return total_loss / len(dataloader), correct / total


def main():
    """
    Main training function.
    """
    # Set random seed for reproducibility
    torch.manual_seed(42)
    np.random.seed(42)

    # Device selection: CUDA (NVIDIA) > MPS (Apple Silicon) > CPU
    if torch.cuda.is_available():
        device = torch.device("cuda")
        print(f"Using device: cuda (NVIDIA GPU)")
    elif torch.backends.mps.is_available():
        device = torch.device("mps")
        print(f"Using device: mps (Apple Silicon GPU)")
    else:
        device = torch.device("cpu")
        print(f"Using device: cpu")

    # Configuration
    config = TransformerConfig(
        d_model=256,
        n_heads=8,
        n_layers=3,
        d_ff=512,
        dropout=0.1,
        max_seq_length=100,
        vocab_size=100,
    )

    print("\nModel Configuration:")
    print(config)

    # Create model
    model = create_transformer(config).to(device)

    # Count parameters
    num_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"\nTotal trainable parameters: {num_params:,}")

    # Create datasets
    print("\nCreating datasets...")
    train_dataset = CopyTaskDataset(num_samples=10000, seq_len=10, vocab_size=100)
    val_dataset = CopyTaskDataset(num_samples=1000, seq_len=10, vocab_size=100)

    train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=64, shuffle=False)

    # Loss and optimizer
    criterion = nn.CrossEntropyLoss(ignore_index=0)  # Ignore padding
    optimizer = optim.Adam(model.parameters(), lr=0.0001, betas=(0.9, 0.98), eps=1e-9)

    # Learning rate scheduler
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="min", factor=0.5, patience=2)

    # Training loop
    num_epochs = 10
    print(f"\nTraining for {num_epochs} epochs...")

    best_val_loss = float("inf")

    for epoch in range(num_epochs):
        print(f"\nEpoch {epoch + 1}/{num_epochs}")

        # Train
        train_loss = train_epoch(model, train_loader, optimizer, criterion, device)

        # Validate
        val_loss, val_acc = evaluate(model, val_loader, criterion, device)

        # Update learning rate
        scheduler.step(val_loss)

        print(f"Train Loss: {train_loss:.4f}")
        print(f"Val Loss: {val_loss:.4f}, Val Accuracy: {val_acc:.4f}")

        # Save best model
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), "best_transformer.pth")
            print("Saved best model!")

    print("\nTraining complete!")


if __name__ == "__main__":
    main()
