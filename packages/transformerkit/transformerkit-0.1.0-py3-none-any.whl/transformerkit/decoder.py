"""
Transformer Decoder implementation.
"""

import torch
import torch.nn as nn

from transformerkit.attention import MultiHeadAttention
from transformerkit.components import LayerNorm, PositionalEncoding, PositionWiseFeedForward


class DecoderLayer(nn.Module):
    """
    Single Transformer Decoder Layer.

    Structure:
    1. Masked multi-head self-attention
    2. Add & Norm
    3. Multi-head cross-attention (with encoder output)
    4. Add & Norm
    5. Position-wise feed-forward network
    6. Add & Norm
    """

    def __init__(self, d_model, n_heads, d_ff, dropout=0.1):
        """
        Args:
            d_model: Model dimension
            n_heads: Number of attention heads
            d_ff: Feed-forward network dimension
            dropout: Dropout rate
        """
        super(DecoderLayer, self).__init__()

        # Masked self-attention
        self.self_attention = MultiHeadAttention(d_model, n_heads, dropout)

        # Cross-attention with encoder output
        self.cross_attention = MultiHeadAttention(d_model, n_heads, dropout)

        # Feed-forward network
        self.feed_forward = PositionWiseFeedForward(d_model, d_ff, dropout)

        # Layer normalization
        self.norm1 = LayerNorm(d_model)
        self.norm2 = LayerNorm(d_model)
        self.norm3 = LayerNorm(d_model)

        # Dropout
        self.dropout = nn.Dropout(dropout)

    def forward(self, x, encoder_output, src_mask=None, tgt_mask=None):
        """
        Forward pass through decoder layer.

        Args:
            x: Input tensor of shape (batch_size, tgt_seq_len, d_model)
            encoder_output: Encoder output of shape (batch_size, src_seq_len, d_model)
            src_mask: Optional source mask for cross-attention
            tgt_mask: Optional target mask for self-attention (look-ahead mask)

        Returns:
            Output tensor of shape (batch_size, tgt_seq_len, d_model)
        """
        # Masked self-attention with residual connection and layer norm
        self_attn_output, _ = self.self_attention(x, x, x, tgt_mask)
        x = self.norm1(x + self.dropout(self_attn_output))

        # Cross-attention with encoder output
        cross_attn_output, _ = self.cross_attention(x, encoder_output, encoder_output, src_mask)
        x = self.norm2(x + self.dropout(cross_attn_output))

        # Feed-forward with residual connection and layer norm
        ff_output = self.feed_forward(x)
        x = self.norm3(x + self.dropout(ff_output))

        return x


class Decoder(nn.Module):
    """
    Transformer Decoder: Stack of N decoder layers.
    """

    def __init__(self, vocab_size, d_model, n_layers, n_heads, d_ff, max_seq_length, dropout=0.1):
        """
        Args:
            vocab_size: Size of vocabulary
            d_model: Model dimension
            n_layers: Number of decoder layers
            n_heads: Number of attention heads
            d_ff: Feed-forward network dimension
            max_seq_length: Maximum sequence length
            dropout: Dropout rate
        """
        super(Decoder, self).__init__()

        self.d_model = d_model

        # Token embedding
        self.embedding = nn.Embedding(vocab_size, d_model)

        # Positional encoding
        self.positional_encoding = PositionalEncoding(d_model, max_seq_length, dropout)

        # Stack of decoder layers
        self.layers = nn.ModuleList(
            [DecoderLayer(d_model, n_heads, d_ff, dropout) for _ in range(n_layers)]
        )

        self.dropout = nn.Dropout(dropout)

    def forward(self, x, encoder_output, src_mask=None, tgt_mask=None):
        """
        Forward pass through decoder.

        Args:
            x: Input token IDs of shape (batch_size, tgt_seq_len)
            encoder_output: Encoder output of shape (batch_size, src_seq_len, d_model)
            src_mask: Optional source mask
            tgt_mask: Optional target mask (look-ahead mask)

        Returns:
            Output tensor of shape (batch_size, tgt_seq_len, d_model)
        """
        # Embedding + scaling
        x = self.embedding(x) * torch.sqrt(torch.tensor(self.d_model, dtype=torch.float32))

        # Add positional encoding
        x = self.positional_encoding(x)

        # Pass through decoder layers
        for layer in self.layers:
            x = layer(x, encoder_output, src_mask, tgt_mask)

        return x
