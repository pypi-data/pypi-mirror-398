"""
Core components for the Transformer model.
Includes positional encoding, feed-forward networks, and layer normalization.
"""

import math

import torch
import torch.nn as nn


class PositionalEncoding(nn.Module):
    """
    Positional encoding using sinusoidal functions.

    PE(pos, 2i) = sin(pos / 10000^(2i/d_model))
    PE(pos, 2i+1) = cos(pos / 10000^(2i/d_model))
    """

    def __init__(self, d_model, max_seq_length=5000, dropout=0.1):
        """
        Args:
            d_model: Model dimension
            max_seq_length: Maximum sequence length
            dropout: Dropout rate
        """
        super(PositionalEncoding, self).__init__()
        self.dropout = nn.Dropout(p=dropout)

        # Create positional encoding matrix
        pe = torch.zeros(max_seq_length, d_model)
        position = torch.arange(0, max_seq_length, dtype=torch.float).unsqueeze(1)

        # Compute the exponential term: 10000^(2i/d_model)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))

        # Apply sin to even indices
        pe[:, 0::2] = torch.sin(position * div_term)

        # Apply cos to odd indices
        pe[:, 1::2] = torch.cos(position * div_term)

        # Add batch dimension: (1, max_seq_length, d_model)
        pe = pe.unsqueeze(0)

        # Register as buffer (not a parameter, but should be saved with the model)
        self.register_buffer("pe", pe)

    def forward(self, x):
        """
        Add positional encoding to input.

        Args:
            x: Input tensor of shape (batch_size, seq_len, d_model)

        Returns:
            Output tensor of shape (batch_size, seq_len, d_model)
        """
        # Add positional encoding
        x = x + self.pe[:, : x.size(1), :]
        return self.dropout(x)


class PositionWiseFeedForward(nn.Module):
    """
    Position-wise Feed-Forward Network.

    FFN(x) = max(0, xW_1 + b_1)W_2 + b_2

    Two linear transformations with ReLU activation in between.
    """

    def __init__(self, d_model, d_ff, dropout=0.1):
        """
        Args:
            d_model: Model dimension
            d_ff: Hidden dimension of feed-forward network
            dropout: Dropout rate
        """
        super(PositionWiseFeedForward, self).__init__()

        self.linear1 = nn.Linear(d_model, d_ff)
        self.linear2 = nn.Linear(d_ff, d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        """
        Forward pass.

        Args:
            x: Input tensor of shape (batch_size, seq_len, d_model)

        Returns:
            Output tensor of shape (batch_size, seq_len, d_model)
        """
        # (batch_size, seq_len, d_model) -> (batch_size, seq_len, d_ff)
        x = self.linear1(x)
        x = torch.relu(x)
        x = self.dropout(x)

        # (batch_size, seq_len, d_ff) -> (batch_size, seq_len, d_model)
        x = self.linear2(x)
        return x


class LayerNorm(nn.Module):
    """
    Layer Normalization.

    Normalizes the inputs across the features dimension.
    """

    def __init__(self, features, eps=1e-6):
        """
        Args:
            features: Number of features (d_model)
            eps: Small constant for numerical stability
        """
        super(LayerNorm, self).__init__()

        # Learnable parameters
        self.gamma = nn.Parameter(torch.ones(features))
        self.beta = nn.Parameter(torch.zeros(features))
        self.eps = eps

    def forward(self, x):
        """
        Forward pass.

        Args:
            x: Input tensor of shape (batch_size, seq_len, d_model)

        Returns:
            Normalized tensor of shape (batch_size, seq_len, d_model)
        """
        # Compute mean and std along the last dimension
        mean = x.mean(-1, keepdim=True)
        std = x.std(-1, keepdim=True)

        # Normalize and apply learnable parameters
        return self.gamma * (x - mean) / (std + self.eps) + self.beta
