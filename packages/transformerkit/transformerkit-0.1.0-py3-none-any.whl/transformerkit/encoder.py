"""
Transformer Encoder implementation.
"""

import torch
import torch.nn as nn

from transformerkit.attention import MultiHeadAttention
from transformerkit.components import LayerNorm, PositionalEncoding, PositionWiseFeedForward


class EncoderLayer(nn.Module):
    """
    Single Transformer Encoder Layer.

    Structure:
    1. Multi-head self-attention
    2. Add & Norm (residual connection + layer normalization)
    3. Position-wise feed-forward network
    4. Add & Norm
    """

    def __init__(self, d_model, n_heads, d_ff, dropout=0.1):
        """
        Args:
            d_model: Model dimension
            n_heads: Number of attention heads
            d_ff: Feed-forward network dimension
            dropout: Dropout rate
        """
        super(EncoderLayer, self).__init__()

        # Multi-head self-attention
        self.self_attention = MultiHeadAttention(d_model, n_heads, dropout)

        # Feed-forward network
        self.feed_forward = PositionWiseFeedForward(d_model, d_ff, dropout)

        # Layer normalization
        self.norm1 = LayerNorm(d_model)
        self.norm2 = LayerNorm(d_model)

        # Dropout
        self.dropout = nn.Dropout(dropout)

    def forward(self, x, mask=None):
        """
        Forward pass through encoder layer.

        Args:
            x: Input tensor of shape (batch_size, seq_len, d_model)
            mask: Optional attention mask

        Returns:
            Output tensor of shape (batch_size, seq_len, d_model)
        """
        # Self-attention with residual connection and layer norm
        attn_output, _ = self.self_attention(x, x, x, mask)
        x = self.norm1(x + self.dropout(attn_output))

        # Feed-forward with residual connection and layer norm
        ff_output = self.feed_forward(x)
        x = self.norm2(x + self.dropout(ff_output))

        return x


class Encoder(nn.Module):
    """
    Transformer Encoder: Stack of N encoder layers.
    """

    def __init__(self, vocab_size, d_model, n_layers, n_heads, d_ff, max_seq_length, dropout=0.1):
        """
        Args:
            vocab_size: Size of vocabulary
            d_model: Model dimension
            n_layers: Number of encoder layers
            n_heads: Number of attention heads
            d_ff: Feed-forward network dimension
            max_seq_length: Maximum sequence length
            dropout: Dropout rate
        """
        super(Encoder, self).__init__()

        self.d_model = d_model

        # Token embedding
        self.embedding = nn.Embedding(vocab_size, d_model)

        # Positional encoding
        self.positional_encoding = PositionalEncoding(d_model, max_seq_length, dropout)

        # Stack of encoder layers
        self.layers = nn.ModuleList(
            [EncoderLayer(d_model, n_heads, d_ff, dropout) for _ in range(n_layers)]
        )

        self.dropout = nn.Dropout(dropout)

    def forward(self, x, mask=None):
        """
        Forward pass through encoder.

        Args:
            x: Input token IDs of shape (batch_size, seq_len)
            mask: Optional attention mask

        Returns:
            Output tensor of shape (batch_size, seq_len, d_model)
        """
        # Embedding + scaling
        x = self.embedding(x) * torch.sqrt(torch.tensor(self.d_model, dtype=torch.float32))

        # Add positional encoding
        x = self.positional_encoding(x)

        # Pass through encoder layers
        for layer in self.layers:
            x = layer(x, mask)

        return x
