def get_ebt_attention_fwd_flops(
    batch_size: int,
    num_heads: int,
    seq_len: int,
    head_dim: int,
    is_jvp: bool = False,
) -> int:
    """Calculate FLOPs for EBT attention operations.
    
    EBT has three components:
    1. Original stream (O->O): Q_o attends to K_o
    2. Predicted stream (P->O): Q_p attends to K_o (cross-attention)
    3. Superdiagonal (P->P): Q_p[i] attends to K_p[i] (element-wise)
    
    Args:
        batch_size: Batch size.
        num_heads: Number of attention heads.
        seq_len: Sequence length.
        head_dim: Dimension of each attention head.
        is_jvp: Whether to include JVP (Jacobian-vector product) FLOPs.
    
    Returns:
        The total FLOPs for the EBT attention operation.
    """
    B, H, S, D = batch_size, num_heads, seq_len, head_dim

    qk_o_flops = 2 * B * H * S * S * D
    softmax_o_flops = 5 * B * H * S * S
    av_o_flops = 2 * B * H * S * S * D
    
    stream_o_flops = qk_o_flops + softmax_o_flops + av_o_flops

    qk_p_flops = 2 * B * H * S * S * D
    softmax_p_flops = 5 * B * H * S * S
    av_p_flops = 2 * B * H * S * S * D
    
    stream_p_flops = qk_p_flops + softmax_p_flops + av_p_flops

    qk_superdiag_flops = 2 * B * H * S * D
    softmax_superdiag_flops = 5 * B * H * S
    av_superdiag_flops = 2 * B * H * S * D
    
    superdiag_flops = qk_superdiag_flops + softmax_superdiag_flops + av_superdiag_flops
    
    total_flops = stream_o_flops + stream_p_flops + superdiag_flops

    if is_jvp:
        total_flops = total_flops * 2
    
    return total_flops


def get_ebt_attention_bwd_flops(
    batch_size: int,
    num_heads: int,
    seq_len: int,
    head_dim: int,
) -> int:
    """Calculate FLOPs for EBT attention backward pass.
    
    Backward pass computes:
    1. dQ_o, dK_o, dV_o from original stream
    2. dQ_p, dK_o (additional), dV_o (additional) from predicted stream
    3. dQ_p (additional), dK_p, dV_p from superdiagonal
    
    Args:
        batch_size: Batch size.
        num_heads: Number of attention heads.
        seq_len: Sequence length.
        head_dim: Dimension of each attention head.
    
    Returns:
        The total FLOPs for the EBT attention backward pass.
    """
    B, H, S, D = batch_size, num_heads, seq_len, head_dim
    
    # Preprocessing FLOPs
    delta_o_flops = B * H * S * D  # Sum over D dimension
    delta_p_flops = B * H * S * D
    preprocess_flops = delta_o_flops + delta_p_flops
    
    # Original Stream Backward FLOPs
    dv_o_flops = 2 * B * H * S * S * D
    dp_o_flops = 2 * B * H * S * D * S
    softmax_bwd_o_flops = 5 * B * H * S * S
    dq_o_flops = 2 * B * H * S * S * D
    dk_o_flops = 2 * B * H * S * S * D
    
    stream_o_bwd_flops = (
        dv_o_flops + dp_o_flops + softmax_bwd_o_flops + 
        dq_o_flops + dk_o_flops
    )

    # Predicted Stream Backward FLOPs
    dv_o_cross_flops = 2 * B * H * S * S * D
    dp_p_flops = 2 * B * H * S * D * S
    softmax_bwd_p_flops = 5 * B * H * S * S
    dq_p_cross_flops = 2 * B * H * S * S * D
    dk_o_cross_flops = 2 * B * H * S * S * D
    
    stream_p_bwd_flops = (
        dv_o_cross_flops + dp_p_flops + softmax_bwd_p_flops + 
        dq_p_cross_flops + dk_o_cross_flops
    )
    
    # Superdiagonal Backward FLOPs
    dv_p_superdiag_flops = 2 * B * H * S * D
    dp_superdiag_flops = 2 * B * H * S * D
    softmax_bwd_superdiag_flops = 5 * B * H * S
    ds_superdiag_flops = 2 * B * H * S
    dq_p_superdiag_flops = 2 * B * H * S * D
    dk_p_superdiag_flops = 2 * B * H * S * D
    
    superdiag_bwd_flops = (
        dv_p_superdiag_flops + dp_superdiag_flops + 
        softmax_bwd_superdiag_flops + ds_superdiag_flops +
        dq_p_superdiag_flops + dk_p_superdiag_flops
    )
    
    # Total Backward FLOPs
    total_bwd_flops = (
        preprocess_flops + 
        stream_o_bwd_flops + 
        stream_p_bwd_flops + 
        superdiag_bwd_flops
    )
    
    return total_bwd_flops