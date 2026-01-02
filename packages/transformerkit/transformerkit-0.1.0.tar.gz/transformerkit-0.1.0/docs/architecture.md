# Transformer Architecture Documentation

This document provides a detailed explanation of the Transformer architecture as implemented in this project.

## Overview

The Transformer is a neural network architecture based entirely on attention mechanisms, introduced in the paper ["Attention Is All You Need"](https://arxiv.org/abs/1706.03762) by Vaswani et al. (2017). It revolutionized sequence-to-sequence tasks by eliminating recurrence and relying solely on attention.

## Architecture Components

### 1. Scaled Dot-Product Attention

The fundamental building block of the Transformer is scaled dot-product attention:

```
Attention(Q, K, V) = softmax(QK^T / √d_k) V
```

**Components:**
- **Q (Query)**: What we're looking for (shape: `[batch, seq_len, d_k]`)
- **K (Key)**: What we're matching against (shape: `[batch, seq_len, d_k]`)
- **V (Value)**: The actual information to retrieve (shape: `[batch, seq_len, d_v]`)
- **d_k**: Dimension of keys (used for scaling)

**Why scaling?** Dividing by √d_k prevents the dot products from getting too large, which would push the softmax into regions with small gradients.

**Implementation:** `transformer.attention.scaled_dot_product_attention()`

### 2. Multi-Head Attention

Instead of performing a single attention function, multi-head attention runs multiple attention operations in parallel:

```
MultiHead(Q, K, V) = Concat(head_1, ..., head_h)W^O
where head_i = Attention(QW_i^Q, KW_i^K, VW_i^V)
```

**Benefits:**
- Allows the model to attend to information from different representation subspaces
- Each head can learn different types of relationships
- Increases model capacity without sequential computation

**Default configuration:** 8 heads with d_model=512 → each head has dimension 64

**Implementation:** `transformer.attention.MultiHeadAttention`

### 3. Positional Encoding

Since the Transformer has no recurrence or convolution, it has no inherent notion of sequence order. Positional encodings add information about token positions:

```
PE(pos, 2i) = sin(pos / 10000^(2i/d_model))
PE(pos, 2i+1) = cos(pos / 10000^(2i/d_model))
```

**Properties:**
- Deterministic (not learned)
- Allows the model to generalize to longer sequences
- Different frequencies for different dimensions
- Enables relative position learning

**Implementation:** `transformer.components.PositionalEncoding`

### 4. Position-wise Feed-Forward Networks

Each layer contains a fully connected feed-forward network applied independently to each position:

```
FFN(x) = max(0, xW_1 + b_1)W_2 + b_2
```

**Structure:**
- Two linear transformations with ReLU activation
- Same across all positions, but different across layers
- Typically expands dimension by 4x (d_model → d_ff → d_model)
- Default: 512 → 2048 → 512

**Implementation:** `transformer.components.PositionWiseFeedForward`

### 5. Layer Normalization

Applied after each sub-layer to stabilize training:

```
LayerNorm(x) = γ ⊙ (x - μ) / σ + β
```

- **μ**: Mean across features
- **σ**: Standard deviation across features
- **γ, β**: Learnable scale and shift parameters

**Implementation:** `transformer.components.LayerNorm`

## Encoder Architecture

The encoder consists of N=6 identical layers (by default).

### Encoder Layer

Each encoder layer has two sub-layers:

1. **Multi-Head Self-Attention**
   - Attends to all positions in the input sequence
   - Allows each position to gather information from all other positions
   
2. **Position-wise Feed-Forward Network**
   - Applies the same FFN to each position independently

Each sub-layer is wrapped with:
- **Residual connection:** `output = sublayer(x) + x`
- **Layer normalization:** `output = LayerNorm(sublayer(x) + x)`

**Forward Pass:**
```
x = LayerNorm(x + MultiHeadAttention(x, x, x))
x = LayerNorm(x + FeedForward(x))
```

### Full Encoder Stack

```
Input (token IDs)
    ↓
Embedding × √d_model
    ↓
+ Positional Encoding
    ↓
Encoder Layer 1
    ↓
Encoder Layer 2
    ↓
...
    ↓
Encoder Layer N
    ↓
Output (contextual representations)
```

**Implementation:** `transformer.encoder.Encoder`, `transformer.encoder.EncoderLayer`

## Decoder Architecture

The decoder also consists of N=6 identical layers.

### Decoder Layer

Each decoder layer has three sub-layers:

1. **Masked Multi-Head Self-Attention**
   - Attends only to earlier positions in the output sequence
   - Prevents information flow from future tokens (autoregressive)
   
2. **Multi-Head Cross-Attention**
   - Attends to the encoder's output
   - Query from decoder, Key and Value from encoder
   
3. **Position-wise Feed-Forward Network**

Each sub-layer has residual connections and layer normalization.

**Forward Pass:**
```
x = LayerNorm(x + MaskedMultiHeadAttention(x, x, x))
x = LayerNorm(x + MultiHeadAttention(x, encoder_output, encoder_output))
x = LayerNorm(x + FeedForward(x))
```

### Full Decoder Stack

```
Input (token IDs)
    ↓
Embedding × √d_model
    ↓
+ Positional Encoding
    ↓
Decoder Layer 1 ←─┐
    ↓             │
Decoder Layer 2   │ (receives encoder output)
    ↓             │
...               │
    ↓             │
Decoder Layer N ──┘
    ↓
Linear (to vocab size)
    ↓
Softmax
    ↓
Output Probabilities
```

**Implementation:** `transformer.decoder.Decoder`, `transformer.decoder.DecoderLayer`

## Complete Transformer

### Forward Pass

```python
# Encode source sequence
encoder_output = encoder(src, src_mask)

# Decode target sequence
decoder_output = decoder(tgt, encoder_output, src_mask, tgt_mask)

# Project to vocabulary
logits = linear(decoder_output)

# Get probabilities
probs = softmax(logits)
```

### Masking

**1. Padding Mask** (for both encoder and decoder):
- Prevents attention to padding tokens
- Applied to source and target sequences

**2. Look-Ahead Mask** (decoder only):
- Prevents attending to future positions
- Ensures autoregressive property
- Upper triangular matrix of True values

**3. Combined Target Mask**:
- Combines padding mask and look-ahead mask
- Used in decoder self-attention

**Implementation:** `transformer.utils.create_*_mask()`

## Training

### Loss Function

Cross-entropy loss between predicted and target tokens:
```python
loss = CrossEntropyLoss(predictions, targets)
```

### Optimization

**Adam optimizer** with custom learning rate schedule:
```
lr = d_model^(-0.5) × min(step^(-0.5), step × warmup_steps^(-1.5))
```

- Warmup for first 4000 steps
- Then decay proportional to inverse square root of step number

### Label Smoothing (optional)

Instead of hard targets (0 or 1), use soft targets:
- Correct class: 0.9
- Other classes: 0.1 / (vocab_size - 1)

Helps prevent overfitting and improves generalization.

## Inference

### Greedy Decoding

Select the most likely token at each step:
```python
while not finished:
    logits = model(src, tgt)
    next_token = argmax(logits[-1])
    tgt = concat(tgt, next_token)
```

### Beam Search

Maintain top-k hypotheses:
- More expensive but better quality
- Typical beam width: 4-10

**Implementation:** `transformer.utils.greedy_decode()`, `transformer.utils.beam_search_decode()`

## Hyperparameters

### Base Model
- **d_model:** 512 (model dimension)
- **n_heads:** 8 (number of attention heads)
- **d_ff:** 2048 (feed-forward dimension)
- **n_layers:** 6 (encoder and decoder layers)
- **dropout:** 0.1
- **Parameters:** ~65M

### Big Model
- **d_model:** 1024
- **n_heads:** 16
- **d_ff:** 4096
- **n_layers:** 6
- **dropout:** 0.3
- **Parameters:** ~213M

## Key Innovations

1. **Parallel Computation**: Unlike RNNs, all positions can be processed in parallel
2. **Long-Range Dependencies**: Direct connections between any two positions
3. **Interpretability**: Attention weights show what the model focuses on
4. **Transfer Learning**: Pre-training on large corpora, fine-tuning on specific tasks

## Complexity Analysis

- **Self-Attention:** O(n² × d)
  - n = sequence length
  - d = model dimension
  - Quadratic in sequence length!

- **Feed-Forward:** O(n × d²)
  - Linear in sequence length

For **very long sequences**, self-attention becomes a bottleneck. Solutions:
- Sparse attention patterns
- Local attention windows
- Low-rank approximations

## References

- [Attention Is All You Need (Vaswani et al., 2017)](https://arxiv.org/abs/1706.03762)
- [The Illustrated Transformer](http://jalammar.github.io/illustrated-transformer/)
- [The Annotated Transformer](http://nlp.seas.harvard.edu/2018/04/03/attention.html)
