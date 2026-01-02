"""
Complete Transformer model implementation.
Combines encoder and decoder into a full seq2seq transformer.
"""

import torch
import torch.nn as nn

from transformerkit.config import TransformerConfig
from transformerkit.decoder import Decoder
from transformerkit.encoder import Encoder


class Transformer(nn.Module):
    """
    Complete Transformer model for sequence-to-sequence tasks.

    Consists of:
    - Encoder stack
    - Decoder stack
    - Final linear projection to vocabulary
    """

    def __init__(self, config: TransformerConfig):
        """
        Args:
            config: TransformerConfig object with model hyperparameters
        """
        super(Transformer, self).__init__()

        self.config = config

        # Encoder
        self.encoder = Encoder(
            vocab_size=config.vocab_size,
            d_model=config.d_model,
            n_layers=config.n_layers,
            n_heads=config.n_heads,
            d_ff=config.d_ff,
            max_seq_length=config.max_seq_length,
            dropout=config.dropout,
        )

        # Decoder
        self.decoder = Decoder(
            vocab_size=config.vocab_size,
            d_model=config.d_model,
            n_layers=config.n_layers,
            n_heads=config.n_heads,
            d_ff=config.d_ff,
            max_seq_length=config.max_seq_length,
            dropout=config.dropout,
        )

        # Final linear projection to vocabulary
        self.fc_out = nn.Linear(config.d_model, config.vocab_size)

        # Initialize parameters
        self._init_parameters()

    def _init_parameters(self):
        """
        Initialize model parameters using Xavier/Glorot initialization.
        """
        for p in self.parameters():
            if p.dim() > 1:
                nn.init.xavier_uniform_(p)

    def forward(self, src, tgt, src_mask=None, tgt_mask=None):
        """
        Forward pass through the transformer.

        Args:
            src: Source sequence token IDs (batch_size, src_seq_len)
            tgt: Target sequence token IDs (batch_size, tgt_seq_len)
            src_mask: Optional source mask
            tgt_mask: Optional target mask (look-ahead mask)

        Returns:
            output: Logits of shape (batch_size, tgt_seq_len, vocab_size)
        """
        # Encode source sequence
        encoder_output = self.encoder(src, src_mask)

        # Decode target sequence
        decoder_output = self.decoder(tgt, encoder_output, src_mask, tgt_mask)

        # Project to vocabulary
        output = self.fc_out(decoder_output)

        return output

    def encode(self, src, src_mask=None):
        """
        Encode source sequence (useful for inference).

        Args:
            src: Source sequence token IDs (batch_size, src_seq_len)
            src_mask: Optional source mask

        Returns:
            encoder_output: Encoded representation (batch_size, src_seq_len, d_model)
        """
        return self.encoder(src, src_mask)

    def decode(self, tgt, encoder_output, src_mask=None, tgt_mask=None):
        """
        Decode target sequence (useful for inference).

        Args:
            tgt: Target sequence token IDs (batch_size, tgt_seq_len)
            encoder_output: Encoder output (batch_size, src_seq_len, d_model)
            src_mask: Optional source mask
            tgt_mask: Optional target mask

        Returns:
            output: Logits of shape (batch_size, tgt_seq_len, vocab_size)
        """
        decoder_output = self.decoder(tgt, encoder_output, src_mask, tgt_mask)
        return self.fc_out(decoder_output)


def create_transformer(config=None, **kwargs):
    """
    Factory function to create a Transformer model.

    Args:
        config: Optional TransformerConfig object
        **kwargs: Optional keyword arguments to override config values

    Returns:
        Transformer model instance
    """
    if config is None:
        config = TransformerConfig(**kwargs)
    else:
        # Update config with any provided kwargs
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)

    return Transformer(config)
