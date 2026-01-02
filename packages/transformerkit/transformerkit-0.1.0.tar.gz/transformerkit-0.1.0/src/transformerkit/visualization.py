"""
Visualization utilities for the Transformer model.
Provides functions to visualize attention weights and patterns.
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import torch


def plot_attention_heatmap(
    attention_weights,
    src_tokens=None,
    tgt_tokens=None,
    title="Attention Weights",
    figsize=(10, 8),
    cmap="viridis",
):
    """
    Plot a single attention heatmap.

    Args:
        attention_weights: Attention weights tensor of shape (tgt_len, src_len)
        src_tokens: Optional list of source tokens for x-axis labels
        tgt_tokens: Optional list of target tokens for y-axis labels
        title: Title for the plot
        figsize: Figure size (width, height)
        cmap: Colormap name

    Returns:
        fig, ax: Matplotlib figure and axis objects
    """
    if isinstance(attention_weights, torch.Tensor):
        attention_weights = attention_weights.detach().cpu().numpy()

    fig, ax = plt.subplots(figsize=figsize)

    # Create heatmap
    sns.heatmap(
        attention_weights,
        cmap=cmap,
        annot=False,
        fmt=".2f",
        cbar=True,
        square=True,
        ax=ax,
        xticklabels=src_tokens if src_tokens else "auto",
        yticklabels=tgt_tokens if tgt_tokens else "auto",
    )

    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel("Source Tokens", fontsize=12)
    ax.set_ylabel("Target Tokens", fontsize=12)

    plt.tight_layout()
    return fig, ax


def plot_multihead_attention(
    attention_weights,
    n_heads=8,
    layer_idx=0,
    src_tokens=None,
    tgt_tokens=None,
    figsize=(20, 12),
):
    """
    Plot attention patterns for all heads in a grid.

    Args:
        attention_weights: Attention weights of shape (n_heads, tgt_len, src_len)
        n_heads: Number of attention heads
        layer_idx: Layer index for title
        src_tokens: Optional list of source tokens
        tgt_tokens: Optional list of target tokens
        figsize: Figure size

    Returns:
        fig: Matplotlib figure object
    """
    if isinstance(attention_weights, torch.Tensor):
        attention_weights = attention_weights.detach().cpu().numpy()

    # Calculate grid dimensions
    n_cols = int(np.ceil(np.sqrt(n_heads)))
    n_rows = int(np.ceil(n_heads / n_cols))

    fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)
    axes = axes.flatten() if n_heads > 1 else [axes]

    for head_idx in range(n_heads):
        ax = axes[head_idx]

        sns.heatmap(
            attention_weights[head_idx],
            cmap="viridis",
            cbar=True,
            square=True,
            ax=ax,
            xticklabels=src_tokens if src_tokens else False,
            yticklabels=tgt_tokens if tgt_tokens else False,
        )

        ax.set_title(f"Head {head_idx + 1}", fontsize=10, fontweight="bold")

        if head_idx % n_cols == 0:
            ax.set_ylabel("Target", fontsize=9)
        if head_idx >= n_heads - n_cols:
            ax.set_xlabel("Source", fontsize=9)

    # Hide unused subplots
    for idx in range(n_heads, len(axes)):
        axes[idx].axis("off")

    fig.suptitle(
        f"Multi-Head Attention - Layer {layer_idx + 1}",
        fontsize=16,
        fontweight="bold",
        y=1.00,
    )

    plt.tight_layout()
    return fig


def plot_layer_attention(
    attention_weights_list,
    head_idx=0,
    src_tokens=None,
    tgt_tokens=None,
    figsize=(20, 5),
):
    """
    Compare attention patterns across different layers.

    Args:
        attention_weights_list: List of attention weights, one per layer
                               Each of shape (n_heads, tgt_len, src_len)
        head_idx: Which attention head to visualize
        src_tokens: Optional list of source tokens
        tgt_tokens: Optional list of target tokens
        figsize: Figure size

    Returns:
        fig: Matplotlib figure object
    """
    n_layers = len(attention_weights_list)

    fig, axes = plt.subplots(1, n_layers, figsize=figsize)
    if n_layers == 1:
        axes = [axes]

    for layer_idx, attention in enumerate(attention_weights_list):
        if isinstance(attention, torch.Tensor):
            attention = attention.detach().cpu().numpy()

        ax = axes[layer_idx]

        # Extract specific head
        head_attention = attention[head_idx]

        sns.heatmap(
            head_attention,
            cmap="viridis",
            cbar=True,
            square=True,
            ax=ax,
            xticklabels=src_tokens if src_tokens else False,
            yticklabels=tgt_tokens if (layer_idx == 0 and tgt_tokens) else False,
        )

        ax.set_title(f"Layer {layer_idx + 1}", fontsize=12, fontweight="bold")

        if layer_idx == 0:
            ax.set_ylabel("Target", fontsize=10)
        ax.set_xlabel("Source", fontsize=10)

    fig.suptitle(
        f"Attention Across Layers (Head {head_idx + 1})",
        fontsize=14,
        fontweight="bold",
    )

    plt.tight_layout()
    return fig


def plot_attention_flow(attention_weights, src_tokens, tgt_tokens, threshold=0.1, figsize=(12, 8)):
    """
    Visualize attention flow with arrows showing strong connections.

    Args:
        attention_weights: Attention weights of shape (tgt_len, src_len)
        src_tokens: List of source tokens
        tgt_tokens: List of target tokens
        threshold: Minimum attention weight to display (0-1)
        figsize: Figure size

    Returns:
        fig, ax: Matplotlib figure and axis objects
    """
    if isinstance(attention_weights, torch.Tensor):
        attention_weights = attention_weights.detach().cpu().numpy()

    fig, ax = plt.subplots(figsize=figsize)

    # Positions
    src_len = len(src_tokens)
    tgt_len = len(tgt_tokens)

    src_positions = np.arange(src_len)
    tgt_positions = np.arange(tgt_len)

    # Draw tokens
    for i, token in enumerate(src_tokens):
        ax.text(
            i,
            0,
            token,
            ha="center",
            va="center",
            fontsize=10,
            bbox=dict(boxstyle="round", facecolor="lightblue"),
        )

    for i, token in enumerate(tgt_tokens):
        ax.text(
            i,
            1,
            token,
            ha="center",
            va="center",
            fontsize=10,
            bbox=dict(boxstyle="round", facecolor="lightgreen"),
        )

    # Draw attention connections
    for tgt_idx in range(tgt_len):
        for src_idx in range(src_len):
            weight = attention_weights[tgt_idx, src_idx]
            if weight > threshold:
                # Draw arrow with alpha proportional to weight
                ax.annotate(
                    "",
                    xy=(src_idx, 0),
                    xytext=(tgt_idx, 1),
                    arrowprops=dict(arrowstyle="->", lw=weight * 3, alpha=weight, color="gray"),
                )

    ax.set_xlim(-0.5, max(src_len, tgt_len) - 0.5)
    ax.set_ylim(-0.3, 1.3)
    ax.axis("off")
    ax.set_title("Attention Flow", fontsize=14, fontweight="bold")

    plt.tight_layout()
    return fig, ax


def extract_attention_weights(model, src, tgt, src_mask=None, tgt_mask=None):
    """
    Extract attention weights from a forward pass.

    Note: This requires the model to be modified to return attention weights.

    Args:
        model: Transformer model
        src: Source sequence
        tgt: Target sequence
        src_mask: Optional source mask
        tgt_mask: Optional target mask

    Returns:
        dict: Dictionary containing encoder and decoder attention weights
    """
    # This is a placeholder - the actual implementation depends on
    # modifying the model to return attention weights
    raise NotImplementedError(
        "Attention weight extraction requires model modification. "
        "See demo.ipynb for examples of how to access attention weights."
    )
