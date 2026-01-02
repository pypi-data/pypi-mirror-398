"""
Attention mechanisms for the Transformer model.
Implements scaled dot-product attention and multi-head attention.
"""

import math

import torch
import torch.nn as nn
import torch.nn.functional as F


def scaled_dot_product_attention(query, key, value, mask=None, dropout=None):
    """
    Compute scaled dot-product attention.

    Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) V

    Args:
        query: Query tensor of shape (batch_size, n_heads, seq_len, d_k)
        key: Key tensor of shape (batch_size, n_heads, seq_len, d_k)
        value: Value tensor of shape (batch_size, n_heads, seq_len, d_v)
        mask: Optional mask tensor (values to mask should be True)
        dropout: Optional dropout layer

    Returns:
        output: Attention output of shape (batch_size, n_heads, seq_len, d_v)
        attention_weights: Attention weights of shape (batch_size, n_heads, seq_len, seq_len)
    """
    d_k = query.size(-1)

    # Compute attention scores: QK^T / sqrt(d_k)
    # (batch_size, n_heads, seq_len_q, d_k) @ (batch_size, n_heads, d_k, seq_len_k)
    # -> (batch_size, n_heads, seq_len_q, seq_len_k)
    scores = torch.matmul(query, key.transpose(-2, -1)) / math.sqrt(d_k)

    # Apply mask (if provided)
    if mask is not None:
        scores = scores.masked_fill(mask == 1, -1e9)

    # Apply softmax to get attention weights
    attention_weights = F.softmax(scores, dim=-1)

    # Apply dropout (if provided)
    if dropout is not None:
        attention_weights = dropout(attention_weights)

    # Multiply by values
    # (batch_size, n_heads, seq_len_q, seq_len_k) @ (batch_size, n_heads, seq_len_k, d_v)
    # -> (batch_size, n_heads, seq_len_q, d_v)
    output = torch.matmul(attention_weights, value)

    return output, attention_weights


class MultiHeadAttention(nn.Module):
    """
    Multi-Head Attention mechanism.

    Splits the input into multiple heads, applies attention independently,
    then concatenates and projects the results.
    """

    def __init__(self, d_model, n_heads, dropout=0.1):
        """
        Args:
            d_model: Model dimension
            n_heads: Number of attention heads
            dropout: Dropout rate
        """
        super(MultiHeadAttention, self).__init__()

        assert d_model % n_heads == 0, "d_model must be divisible by n_heads"

        self.d_model = d_model
        self.n_heads = n_heads
        self.d_k = d_model // n_heads

        # Linear projections for Q, K, V
        self.W_q = nn.Linear(d_model, d_model)
        self.W_k = nn.Linear(d_model, d_model)
        self.W_v = nn.Linear(d_model, d_model)

        # Output projection
        self.W_o = nn.Linear(d_model, d_model)

        self.dropout = nn.Dropout(dropout)

    def split_heads(self, x, batch_size):
        """
        Split the last dimension into (n_heads, d_k).
        Transpose to shape: (batch_size, n_heads, seq_len, d_k)
        """
        x = x.view(batch_size, -1, self.n_heads, self.d_k)
        return x.transpose(1, 2)

    def forward(self, query, key, value, mask=None):
        """
        Forward pass for multi-head attention.

        Args:
            query: Query tensor of shape (batch_size, seq_len, d_model)
            key: Key tensor of shape (batch_size, seq_len, d_model)
            value: Value tensor of shape (batch_size, seq_len, d_model)
            mask: Optional mask tensor

        Returns:
            output: Attention output of shape (batch_size, seq_len, d_model)
            attention_weights: Attention weights
        """
        batch_size = query.size(0)

        # Linear projections
        Q = self.W_q(query)  # (batch_size, seq_len, d_model)
        K = self.W_k(key)
        V = self.W_v(value)

        # Split into multiple heads
        Q = self.split_heads(Q, batch_size)  # (batch_size, n_heads, seq_len, d_k)
        K = self.split_heads(K, batch_size)
        V = self.split_heads(V, batch_size)

        # Apply attention
        attn_output, attention_weights = scaled_dot_product_attention(
            Q, K, V, mask=mask, dropout=self.dropout
        )

        # Concatenate heads
        # (batch_size, n_heads, seq_len, d_k) -> (batch_size, seq_len, n_heads, d_k)
        attn_output = attn_output.transpose(1, 2).contiguous()

        # Reshape to (batch_size, seq_len, d_model)
        attn_output = attn_output.view(batch_size, -1, self.d_model)

        # Final linear projection
        output = self.W_o(attn_output)

        return output, attention_weights
