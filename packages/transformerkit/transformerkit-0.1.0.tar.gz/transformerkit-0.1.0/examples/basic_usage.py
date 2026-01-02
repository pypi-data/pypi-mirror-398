"""
Example usage of the Transformer model.
Demonstrates model creation, training, and inference.
"""

import torch

from transformerkit import create_transformer
from transformerkit.config import TransformerConfig
from transformerkit.utils import count_parameters, create_padding_mask, greedy_decode


def simple_example():
    """
    Simple example demonstrating transformer forward pass.
    """
    print("=" * 60)
    print("Simple Transformer Example")
    print("=" * 60)

    # Create a small transformer
    config = TransformerConfig(
        d_model=128,
        n_heads=4,
        n_layers=2,
        d_ff=256,
        dropout=0.1,
        max_seq_length=50,
        vocab_size=1000,
    )

    model = create_transformer(config)

    print(f"\nModel created with {count_parameters(model):,} parameters")
    print(
        f"Configuration: {config.n_layers} layers, {config.n_heads} heads, d_model={config.d_model}"
    )

    # Create sample input
    batch_size = 2
    src_seq_len = 10
    tgt_seq_len = 8

    # Random source and target sequences
    src = torch.randint(3, 1000, (batch_size, src_seq_len))
    tgt = torch.randint(3, 1000, (batch_size, tgt_seq_len))

    print(f"\nInput shapes:")
    print(f"  Source: {src.shape}")
    print(f"  Target: {tgt.shape}")

    # Forward pass
    model.eval()
    with torch.no_grad():
        output = model(src, tgt)

    print(f"\nOutput shape: {output.shape}")
    print(
        f"  Expected: (batch_size={batch_size}, seq_len={tgt_seq_len}, vocab_size={config.vocab_size})"
    )

    # Get predictions
    predictions = output.argmax(dim=-1)
    print(f"\nPredictions shape: {predictions.shape}")
    print(f"Sample predictions (first sequence):\n  {predictions[0].tolist()}")


def generation_example():
    """
    Example demonstrating sequence generation with greedy decoding.
    """
    print("\n" + "=" * 60)
    print("Sequence Generation Example")
    print("=" * 60)

    # Create transformer
    config = TransformerConfig(
        d_model=128,
        n_heads=4,
        n_layers=2,
        d_ff=256,
        dropout=0.0,  # No dropout for inference
        max_seq_length=50,
        vocab_size=100,
    )

    model = create_transformer(config)
    model.eval()

    # Sample input sequence
    src = torch.tensor([[5, 10, 15, 20, 25, 30, 35, 40, 45]])

    print(f"\nSource sequence: {src[0].tolist()}")

    # Create source mask
    src_mask = create_padding_mask(src, pad_idx=0)

    # Generate sequence
    max_len = 12
    start_idx = 1  # <start> token
    end_idx = 2  # <end> token

    with torch.no_grad():
        generated = greedy_decode(
            model, src, src_mask, max_len=max_len, start_idx=start_idx, end_idx=end_idx
        )

    print(f"Generated sequence: {generated[0].tolist()}")
    print(f"Length: {generated.size(1)}")


def architecture_overview():
    """
    Print an overview of the transformer architecture.
    """
    print("\n" + "=" * 60)
    print("Transformer Architecture Overview")
    print("=" * 60)

    config = TransformerConfig(
        d_model=512, n_heads=8, n_layers=6, d_ff=2048, dropout=0.1, vocab_size=10000
    )

    model = create_transformer(config)

    print(f"\nConfiguration:")
    print(f"  Model dimension (d_model): {config.d_model}")
    print(f"  Number of attention heads: {config.n_heads}")
    print(f"  Dimension per head: {config.d_k}")
    print(f"  Number of layers: {config.n_layers}")
    print(f"  Feed-forward dimension: {config.d_ff}")
    print(f"  Dropout rate: {config.dropout}")
    print(f"  Vocabulary size: {config.vocab_size}")
    print(f"  Maximum sequence length: {config.max_seq_length}")

    print(f"\nModel Structure:")
    print(f"  Encoder:")
    print(f"    - Token Embedding")
    print(f"    - Positional Encoding")
    print(f"    - {config.n_layers}x Encoder Layers:")
    print(f"        - Multi-Head Self-Attention ({config.n_heads} heads)")
    print(f"        - Add & Norm")
    print(f"        - Feed-Forward Network (d_ff={config.d_ff})")
    print(f"        - Add & Norm")

    print(f"\n  Decoder:")
    print(f"    - Token Embedding")
    print(f"    - Positional Encoding")
    print(f"    - {config.n_layers}x Decoder Layers:")
    print(f"        - Masked Multi-Head Self-Attention ({config.n_heads} heads)")
    print(f"        - Add & Norm")
    print(f"        - Multi-Head Cross-Attention ({config.n_heads} heads)")
    print(f"        - Add & Norm")
    print(f"        - Feed-Forward Network (d_ff={config.d_ff})")
    print(f"        - Add & Norm")

    print(f"\n  Output:")
    print(f"    - Linear projection to vocabulary (d_model → vocab_size)")

    print(f"\nTotal parameters: {count_parameters(model):,}")

    # Parameter breakdown
    encoder_params = sum(p.numel() for p in model.encoder.parameters())
    decoder_params = sum(p.numel() for p in model.decoder.parameters())
    output_params = sum(p.numel() for p in model.fc_out.parameters())

    print(f"\nParameter breakdown:")
    print(f"  Encoder: {encoder_params:,}")
    print(f"  Decoder: {decoder_params:,}")
    print(f"  Output layer: {output_params:,}")


if __name__ == "__main__":
    # Run examples
    simple_example()
    generation_example()
    architecture_overview()

    print("\n" + "=" * 60)
    print("Examples complete!")
    print("=" * 60)
    print("\nTo train the model, run: python train.py")
