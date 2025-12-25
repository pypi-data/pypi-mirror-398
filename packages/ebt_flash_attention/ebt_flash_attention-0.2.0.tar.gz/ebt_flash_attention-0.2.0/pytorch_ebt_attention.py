import math
import torch
import torch.nn.functional as F

MASK_CONST = -1e9


def pytorch_ebt_attention(
    q_o, k_o, v_o, q_p, k_p, v_p, sm_scale=None, attn_mask=None,
):
    """
    PyTorch reference implementation.
    Inputs: [B, N, S, H] (batch, heads, seqlen, head_dim)
    """
    bsz, n_heads, seqlen, head_dim = q_o.shape
    dtype = q_o.dtype
    
    if sm_scale is None:
        sm_scale = 1.0 / math.sqrt(head_dim)
    
    scores_o = torch.matmul(q_o, k_o.transpose(-2, -1)) * sm_scale
    
    if attn_mask is not None:
        o_mask = attn_mask[:-1, :-1]
        if o_mask.dtype == torch.bool:
            scores_o = scores_o + torch.where(o_mask, 0.0, MASK_CONST)
        else:
            scores_o = scores_o + o_mask
    
    scores_o = F.softmax(scores_o, dim=-1)
    output_o = torch.matmul(scores_o.to(dtype=dtype), v_o)
    
    scores_p = torch.matmul(q_p, k_o.transpose(-2, -1)) * sm_scale
    
    # Append column for superdiagonal
    temp_append = torch.zeros(
        (bsz, n_heads, seqlen, 1), dtype=scores_p.dtype, device=scores_p.device
    )
    scores_p = torch.cat((scores_p, temp_append), dim=-1)  # [B, N, S, S+1]
    
    # Compute superdiagonal self-attention scores
    insertion_superdiagonal = (q_p * k_p).sum(dim=-1) * sm_scale  # [B, N, S]
    
    superdiag_rows = torch.arange(seqlen, device=scores_p.device)
    superdiag_cols = torch.arange(1, seqlen + 1, device=scores_p.device)
    
    # Zero out superdiagonal positions (differentiable)
    diagonal_removal_mask = torch.ones_like(scores_p)
    diagonal_removal_mask[:, :, superdiag_rows, superdiag_cols] = 0.0
    scores_p = scores_p * diagonal_removal_mask
    
    # Insert self-attention scores at superdiagonal
    diagonal_addition_mask = torch.zeros_like(scores_p)
    diagonal_addition_mask[:, :, superdiag_rows, superdiag_cols] = insertion_superdiagonal
    scores_p = scores_p + diagonal_addition_mask
    
    # Apply mask
    if attn_mask is not None:
        p_mask = attn_mask[1:, :]  # [S, S+1]
        if p_mask.dtype == torch.bool:
            scores_p = scores_p + torch.where(p_mask, 0.0, MASK_CONST)
        else:
            scores_p = scores_p + p_mask
    
    # Softmax over entire row (cross-attn + self-attn)
    scores_p = F.softmax(scores_p, dim=-1)
    
    # Extract superdiagonal after softmax
    scores_p_superdiagonal = scores_p[:, :, superdiag_rows, superdiag_cols].clone()
    
    # Zero out superdiagonal for matmul
    scores_p = scores_p * diagonal_removal_mask
    scores_p = scores_p[:, :, :, :-1]  # [B, N, S, S]
    
    # Cross-attention output
    output_p = torch.matmul(scores_p.to(dtype=dtype), v_o)
    
    # Add self-attention contribution
    output_p = output_p + v_p * scores_p_superdiagonal.unsqueeze(-1).to(dtype=dtype)
    
    return output_o, output_p


def SDPA_ebt_attention(
    q_o, k_o, v_o, q_p, k_p, v_p, sm_scale=None, attn_mask=None,
):
    """
    PyTorch compiled SDPA reference implementation.
    Inputs: [B, N, S, H] (batch, heads, seqlen, head_dim)
    """
    compiled_fn = torch.compile(pytorch_ebt_attention, mode="max-autotune")
    return compiled_fn(
        q_o, k_o, v_o, q_p, k_p, v_p, sm_scale=sm_scale, attn_mask=attn_mask,
    )