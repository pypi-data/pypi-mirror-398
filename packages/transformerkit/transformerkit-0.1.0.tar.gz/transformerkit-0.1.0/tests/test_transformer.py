"""
Test suite for the Transformer implementation.
Tests individual components and integration.
"""

import torch
import torch.nn as nn

from transformerkit import create_transformer
from transformerkit.attention import MultiHeadAttention, scaled_dot_product_attention
from transformerkit.components import LayerNorm, PositionalEncoding, PositionWiseFeedForward
from transformerkit.config import TransformerConfig
from transformerkit.decoder import Decoder, DecoderLayer
from transformerkit.encoder import Encoder, EncoderLayer
from transformerkit.utils import (
    create_look_ahead_mask,
    create_padding_mask,
    create_target_mask,
    greedy_decode,
)


def test_scaled_dot_product_attention():
    """Test scaled dot-product attention."""
    print("Testing scaled_dot_product_attention...")

    batch_size, n_heads, seq_len, d_k = 2, 4, 10, 64

    Q = torch.randn(batch_size, n_heads, seq_len, d_k)
    K = torch.randn(batch_size, n_heads, seq_len, d_k)
    V = torch.randn(batch_size, n_heads, seq_len, d_k)

    output, attn_weights = scaled_dot_product_attention(Q, K, V)

    assert output.shape == (batch_size, n_heads, seq_len, d_k)
    assert attn_weights.shape == (batch_size, n_heads, seq_len, seq_len)

    # Check attention weights sum to 1
    assert torch.allclose(attn_weights.sum(dim=-1), torch.ones(batch_size, n_heads, seq_len))

    print("✓ Scaled dot-product attention test passed")


def test_multi_head_attention():
    """Test multi-head attention."""
    print("Testing MultiHeadAttention...")

    batch_size, seq_len, d_model = 2, 10, 256
    n_heads = 8

    mha = MultiHeadAttention(d_model, n_heads)

    x = torch.randn(batch_size, seq_len, d_model)
    output, attn_weights = mha(x, x, x)

    assert output.shape == (batch_size, seq_len, d_model)
    assert attn_weights.shape == (batch_size, n_heads, seq_len, seq_len)

    print("✓ Multi-head attention test passed")


def test_positional_encoding():
    """Test positional encoding."""
    print("Testing PositionalEncoding...")

    batch_size, seq_len, d_model = 2, 20, 256

    pe = PositionalEncoding(d_model, max_seq_length=100)
    x = torch.randn(batch_size, seq_len, d_model)
    output = pe(x)

    assert output.shape == (batch_size, seq_len, d_model)

    print("✓ Positional encoding test passed")


def test_feed_forward():
    """Test position-wise feed-forward network."""
    print("Testing PositionWiseFeedForward...")

    batch_size, seq_len, d_model = 2, 10, 256
    d_ff = 512

    ff = PositionWiseFeedForward(d_model, d_ff)
    x = torch.randn(batch_size, seq_len, d_model)
    output = ff(x)

    assert output.shape == (batch_size, seq_len, d_model)

    print("✓ Feed-forward network test passed")


def test_layer_norm():
    """Test layer normalization."""
    print("Testing LayerNorm...")

    batch_size, seq_len, d_model = 2, 10, 256

    ln = LayerNorm(d_model)
    x = torch.randn(batch_size, seq_len, d_model)
    output = ln(x)

    assert output.shape == (batch_size, seq_len, d_model)

    # Check that output is normalized
    mean = output.mean(dim=-1)
    std = output.std(dim=-1)

    assert torch.allclose(mean, torch.zeros_like(mean), atol=1e-5)
    assert torch.allclose(std, torch.ones_like(std), atol=1e-5)

    print("✓ Layer normalization test passed")


def test_encoder_layer():
    """Test encoder layer."""
    print("Testing EncoderLayer...")

    batch_size, seq_len, d_model = 2, 10, 256
    n_heads, d_ff = 8, 512

    encoder_layer = EncoderLayer(d_model, n_heads, d_ff)
    x = torch.randn(batch_size, seq_len, d_model)
    output = encoder_layer(x)

    assert output.shape == (batch_size, seq_len, d_model)

    print("✓ Encoder layer test passed")


def test_decoder_layer():
    """Test decoder layer."""
    print("Testing DecoderLayer...")

    batch_size, src_len, tgt_len, d_model = 2, 10, 8, 256
    n_heads, d_ff = 8, 512

    decoder_layer = DecoderLayer(d_model, n_heads, d_ff)

    x = torch.randn(batch_size, tgt_len, d_model)
    encoder_output = torch.randn(batch_size, src_len, d_model)

    output = decoder_layer(x, encoder_output)

    assert output.shape == (batch_size, tgt_len, d_model)

    print("✓ Decoder layer test passed")


def test_encoder():
    """Test encoder stack."""
    print("Testing Encoder...")

    batch_size, seq_len = 2, 10
    vocab_size, d_model, n_layers, n_heads, d_ff = 1000, 256, 3, 8, 512

    encoder = Encoder(vocab_size, d_model, n_layers, n_heads, d_ff, max_seq_length=100)

    x = torch.randint(0, vocab_size, (batch_size, seq_len))
    output = encoder(x)

    assert output.shape == (batch_size, seq_len, d_model)

    print("✓ Encoder test passed")


def test_decoder():
    """Test decoder stack."""
    print("Testing Decoder...")

    batch_size, src_len, tgt_len = 2, 10, 8
    vocab_size, d_model, n_layers, n_heads, d_ff = 1000, 256, 3, 8, 512

    decoder = Decoder(vocab_size, d_model, n_layers, n_heads, d_ff, max_seq_length=100)

    x = torch.randint(0, vocab_size, (batch_size, tgt_len))
    encoder_output = torch.randn(batch_size, src_len, d_model)

    output = decoder(x, encoder_output)

    assert output.shape == (batch_size, tgt_len, d_model)

    print("✓ Decoder test passed")


def test_transformer_model():
    """Test complete transformer model."""
    print("Testing Transformer...")

    config = TransformerConfig(
        d_model=256, n_heads=8, n_layers=3, d_ff=512, dropout=0.1, vocab_size=1000
    )

    model = create_transformer(config)

    batch_size, src_len, tgt_len = 2, 10, 8

    src = torch.randint(0, 1000, (batch_size, src_len))
    tgt = torch.randint(0, 1000, (batch_size, tgt_len))

    output = model(src, tgt)

    assert output.shape == (batch_size, tgt_len, 1000)

    print("✓ Transformer model test passed")


def test_masking():
    """Test mask creation functions."""
    print("Testing masking functions...")

    batch_size, seq_len = 2, 10

    # Test padding mask
    seq = torch.tensor([[1, 2, 3, 0, 0], [4, 5, 6, 7, 0]])
    pad_mask = create_padding_mask(seq, pad_idx=0)

    assert pad_mask.shape == (batch_size, 1, 1, 5)
    assert pad_mask[0, 0, 0, 3] == True  # Padding position
    assert pad_mask[0, 0, 0, 0] == False  # Non-padding position

    # Test look-ahead mask
    look_ahead = create_look_ahead_mask(seq_len)
    assert look_ahead.shape == (1, 1, seq_len, seq_len)
    assert look_ahead[0, 0, 0, 1] == True  # Future position
    assert look_ahead[0, 0, 1, 0] == False  # Past position

    # Test target mask
    tgt_mask = create_target_mask(seq)
    assert tgt_mask.shape == (batch_size, 1, 5, 5)

    print("✓ Masking tests passed")


def test_gradients():
    """Test that gradients flow properly."""
    print("Testing gradient flow...")

    config = TransformerConfig(
        d_model=128, n_heads=4, n_layers=2, d_ff=256, dropout=0.0, vocab_size=100
    )

    model = create_transformer(config)
    criterion = nn.CrossEntropyLoss()

    src = torch.randint(3, 100, (2, 5))
    tgt = torch.randint(3, 100, (2, 5))
    tgt_output = torch.randint(3, 100, (2, 5))

    # Forward pass
    output = model(src, tgt)
    loss = criterion(output.reshape(-1, 100), tgt_output.reshape(-1))

    # Backward pass
    loss.backward()

    # Check that gradients exist
    for name, param in model.named_parameters():
        assert param.grad is not None, f"No gradient for {name}"
        assert not torch.isnan(param.grad).any(), f"NaN gradient for {name}"

    print("✓ Gradient flow test passed")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("Running Transformer Tests")
    print("=" * 60)
    print()

    tests = [
        test_scaled_dot_product_attention,
        test_multi_head_attention,
        test_positional_encoding,
        test_feed_forward,
        test_layer_norm,
        test_encoder_layer,
        test_decoder_layer,
        test_encoder,
        test_decoder,
        test_transformer_model,
        test_masking,
        test_gradients,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
        print()

    print("=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed == 0:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {failed} test(s) failed")


if __name__ == "__main__":
    run_all_tests()
