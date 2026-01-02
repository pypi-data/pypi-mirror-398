"""
Utility functions for the Transformer model.
Includes mask creation and sequence generation helpers.
"""

import torch


def create_padding_mask(seq, pad_idx=0):
    """
    Create padding mask for a sequence.

    Args:
        seq: Sequence tensor of shape (batch_size, seq_len)
        pad_idx: Padding token index (default: 0)

    Returns:
        mask: Boolean mask of shape (batch_size, 1, 1, seq_len)
              True where tokens are padding tokens
    """
    # Create mask: True for padding tokens
    mask = seq == pad_idx

    # Add dimensions for broadcasting: (batch_size, 1, 1, seq_len)
    mask = mask.unsqueeze(1).unsqueeze(2)

    return mask


def create_look_ahead_mask(size):
    """
    Create look-ahead mask for decoder self-attention.
    Prevents attending to future positions.

    Args:
        size: Sequence length

    Returns:
        mask: Boolean mask of shape (1, 1, size, size)
              True for positions that should be masked
    """
    # Create upper triangular matrix (excluding diagonal)
    mask = torch.triu(torch.ones(size, size), diagonal=1).bool()

    # Add batch and head dimensions
    mask = mask.unsqueeze(0).unsqueeze(0)

    return mask


def create_target_mask(tgt, pad_idx=0):
    """
    Create combined mask for decoder: padding mask + look-ahead mask.

    Args:
        tgt: Target sequence of shape (batch_size, tgt_seq_len)
        pad_idx: Padding token index (default: 0)

    Returns:
        mask: Combined mask of shape (batch_size, 1, tgt_seq_len, tgt_seq_len)
    """
    batch_size, tgt_len = tgt.size()

    # Padding mask
    tgt_padding_mask = create_padding_mask(tgt, pad_idx)  # (batch_size, 1, 1, tgt_len)

    # Look-ahead mask
    tgt_look_ahead_mask = create_look_ahead_mask(tgt_len).to(tgt.device)  # (1, 1, tgt_len, tgt_len)

    # Combine masks (logical OR)
    # Broadcasting: (batch_size, 1, 1, tgt_len) | (1, 1, tgt_len, tgt_len)
    # -> (batch_size, 1, tgt_len, tgt_len)
    tgt_mask = tgt_padding_mask | tgt_look_ahead_mask

    return tgt_mask


def greedy_decode(model, src, src_mask, max_len, start_idx, end_idx):
    """
    Greedy decoding for sequence generation.

    Args:
        model: Transformer model
        src: Source sequence (batch_size, src_len)
        src_mask: Source mask
        max_len: Maximum length to generate
        start_idx: Start token index
        end_idx: End token index

    Returns:
        decoded: Generated sequence (batch_size, generated_len)
    """
    batch_size = src.size(0)
    device = src.device

    # Encode source
    encoder_output = model.encode(src, src_mask)

    # Initialize decoder input with start token
    decoder_input = torch.full((batch_size, 1), start_idx, dtype=torch.long, device=device)

    for _ in range(max_len - 1):
        # Create target mask
        tgt_mask = create_look_ahead_mask(decoder_input.size(1)).to(device)

        # Decode
        output = model.decode(decoder_input, encoder_output, src_mask, tgt_mask)

        # Get next token (greedy selection)
        next_token = output[:, -1, :].argmax(dim=-1, keepdim=True)

        # Append to decoder input
        decoder_input = torch.cat([decoder_input, next_token], dim=1)

        # Check if all sequences have generated end token
        if (next_token == end_idx).all():
            break

    return decoder_input


def beam_search_decode(model, src, src_mask, max_len, start_idx, end_idx, beam_width=5):
    """
    Beam search decoding for sequence generation.

    Args:
        model: Transformer model
        src: Source sequence (1, src_len) - single example only
        src_mask: Source mask
        max_len: Maximum length to generate
        start_idx: Start token index
        end_idx: End token index
        beam_width: Beam width for beam search

    Returns:
        decoded: Best generated sequence (1, generated_len)
    """
    device = src.device

    # Encode source
    encoder_output = model.encode(src, src_mask)

    # Initialize beams: [(sequence, score)]
    beams = [(torch.tensor([[start_idx]], device=device), 0.0)]

    for _ in range(max_len - 1):
        candidates = []

        for seq, score in beams:
            # If sequence ends with end_idx, add to candidates without extending
            if seq[0, -1].item() == end_idx:
                candidates.append((seq, score))
                continue

            # Create target mask
            tgt_mask = create_look_ahead_mask(seq.size(1)).to(device)

            # Decode
            output = model.decode(seq, encoder_output, src_mask, tgt_mask)

            # Get log probabilities for next token
            log_probs = torch.log_softmax(output[:, -1, :], dim=-1)

            # Get top k tokens
            top_log_probs, top_indices = log_probs.topk(beam_width)

            # Create new candidates
            for i in range(beam_width):
                next_token = top_indices[0, i].unsqueeze(0).unsqueeze(0)
                new_seq = torch.cat([seq, next_token], dim=1)
                new_score = score + top_log_probs[0, i].item()
                candidates.append((new_seq, new_score))

        # Select top beam_width candidates
        beams = sorted(candidates, key=lambda x: x[1], reverse=True)[:beam_width]

        # Check if best beam has ended
        if beams[0][0][0, -1].item() == end_idx:
            break

    # Return best sequence
    return beams[0][0]


def count_parameters(model):
    """
    Count the number of trainable parameters in the model.

    Args:
        model: PyTorch model

    Returns:
        total: Total number of trainable parameters
    """
    return sum(p.numel() for p in model.parameters() if p.requires_grad)
