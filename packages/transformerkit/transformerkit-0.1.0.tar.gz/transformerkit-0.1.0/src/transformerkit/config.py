"""
Configuration parameters for the Transformer model.
"""


class TransformerConfig:
    """Configuration class for Transformer hyperparameters."""

    def __init__(
        self,
        d_model: int = 512,  # Model dimension (embedding size)
        n_heads: int = 8,  # Number of attention heads
        n_layers: int = 6,  # Number of encoder/decoder layers
        d_ff: int = 2048,  # Feed-forward network dimension
        dropout: float = 0.1,  # Dropout rate
        max_seq_length: int = 5000,  # Maximum sequence length
        vocab_size: int = 10000,  # Vocabulary size
    ):
        self.d_model = d_model
        self.n_heads = n_heads
        self.n_layers = n_layers
        self.d_ff = d_ff
        self.dropout = dropout
        self.max_seq_length = max_seq_length
        self.vocab_size = vocab_size

        # Derived parameters
        assert d_model % n_heads == 0, "d_model must be divisible by n_heads"
        self.d_k = d_model // n_heads  # Dimension per head
        self.d_v = d_model // n_heads  # Dimension per head (same as d_k)

    def __repr__(self):
        return (
            f"TransformerConfig(\n"
            f"  d_model={self.d_model},\n"
            f"  n_heads={self.n_heads},\n"
            f"  n_layers={self.n_layers},\n"
            f"  d_ff={self.d_ff},\n"
            f"  dropout={self.dropout},\n"
            f"  max_seq_length={self.max_seq_length},\n"
            f"  vocab_size={self.vocab_size}\n"
            f")"
        )


# Default configuration
DEFAULT_CONFIG = TransformerConfig()
