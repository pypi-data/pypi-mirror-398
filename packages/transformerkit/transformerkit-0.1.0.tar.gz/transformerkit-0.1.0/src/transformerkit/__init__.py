"""
TransformerKit

A complete implementation of the Transformer architecture from the paper
"Attention Is All You Need" (Vaswani et al., 2017) in PyTorch.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__license__ = "MIT"

from .attention import MultiHeadAttention, scaled_dot_product_attention
from .components import LayerNorm, PositionalEncoding, PositionWiseFeedForward
from .config import DEFAULT_CONFIG, TransformerConfig
from .decoder import Decoder, DecoderLayer
from .encoder import Encoder, EncoderLayer
from .model import Transformer, create_transformer
from .utils import (
    beam_search_decode,
    count_parameters,
    create_look_ahead_mask,
    create_padding_mask,
    create_target_mask,
    greedy_decode,
)
from .visualization import (
    plot_attention_flow,
    plot_attention_heatmap,
    plot_layer_attention,
    plot_multihead_attention,
)

__all__ = [
    # Config
    "TransformerConfig",
    "DEFAULT_CONFIG",
    # Main model
    "Transformer",
    "create_transformer",
    # Attention
    "MultiHeadAttention",
    "scaled_dot_product_attention",
    # Components
    "PositionalEncoding",
    "PositionWiseFeedForward",
    "LayerNorm",
    # Encoder
    "Encoder",
    "EncoderLayer",
    # Decoder
    "Decoder",
    "DecoderLayer",
    # Utils
    "create_padding_mask",
    "create_look_ahead_mask",
    "create_target_mask",
    "greedy_decode",
    "beam_search_decode",
    "count_parameters",
    # Visualization
    "plot_attention_heatmap",
    "plot_multihead_attention",
    "plot_layer_attention",
    "plot_attention_flow",
]
