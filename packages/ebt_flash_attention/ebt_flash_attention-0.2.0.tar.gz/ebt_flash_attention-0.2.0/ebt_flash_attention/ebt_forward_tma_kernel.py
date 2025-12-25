import triton
import triton.language as tl


@triton.jit
def _maybe_make_tensor_desc(desc_or_ptr, shape, strides, block_shape):
    """Maybe make a tensor descriptor from a pointer."""
    if isinstance(desc_or_ptr, tl.tensor_descriptor):
        return desc_or_ptr
    else:
        return tl.make_tensor_descriptor(desc_or_ptr, shape, strides, block_shape)
    

def _host_descriptor_pre_hook(nargs):
    """Pre-hook to set up tensor descriptors for the attention kernel.

    Args:
        nargs: A dictionary of kernel arguments.
    """
    BLOCK_M = nargs["BLOCK_M"]
    BLOCK_N = nargs["BLOCK_N"]
    HEAD_DIM = nargs["HEAD_DIM"]
    ENABLE_JVP = nargs["ENABLE_JVP"]

    nargs["desc_q_o"].block_shape = [BLOCK_M, HEAD_DIM]
    nargs["desc_q_p"].block_shape = [BLOCK_M, HEAD_DIM]
    nargs["desc_v_o"].block_shape = [BLOCK_N, HEAD_DIM]
    nargs["desc_v_p"].block_shape = [BLOCK_M, HEAD_DIM]
    nargs["desc_k_o"].block_shape = [BLOCK_N, HEAD_DIM]
    nargs["desc_k_p"].block_shape = [BLOCK_M, HEAD_DIM]
    nargs["desc_out_o"].block_shape = [BLOCK_M, HEAD_DIM]
    nargs["desc_out_p"].block_shape = [BLOCK_M, HEAD_DIM]

    if ENABLE_JVP:
        nargs["desc_t_q_o"].block_shape = [BLOCK_M, HEAD_DIM]
        nargs["desc_t_q_p"].block_shape = [BLOCK_M, HEAD_DIM]
        nargs["desc_t_v_o"].block_shape = [BLOCK_N, HEAD_DIM]
        nargs["desc_t_v_p"].block_shape = [BLOCK_M, HEAD_DIM]
        nargs["desc_t_k_o"].block_shape = [BLOCK_N, HEAD_DIM]
        nargs["desc_t_k_p"].block_shape = [BLOCK_M, HEAD_DIM]
        nargs["desc_t_out_o"].block_shape = [BLOCK_M, HEAD_DIM]
        nargs["desc_t_out_p"].block_shape = [BLOCK_M, HEAD_DIM]


def get_fwd_autotune_configs():
    configs = []
    for BLOCK_M in [32, 64, 128]:
        for BLOCK_N in [32, 64]:
            for num_warps in [4, 8]:
                for num_stages in [2, 3, 4]:
                    configs.append(
                        triton.Config(
                            {'BLOCK_M': BLOCK_M, 'BLOCK_N': BLOCK_N},
                            num_warps=num_warps,
                            num_stages=num_stages,
                            pre_hook=_host_descriptor_pre_hook,
                        )
                    )
    
    return configs
    

    

@triton.jit
def _ebt_attn_fwd_inner_oo_tma(
    acc_o,
    g_acc_o,
    l_i_o,
    m_i_o,
    mu_i_o,
    p_tv_acc_o,
    q_o, t_q_o,
    desc_k_o,
    desc_v_o,
    desc_t_k_o,
    desc_t_v_o,
    offset_y,
    mask_o_block_ptr,
    dtype: tl.constexpr, start_m, qk_scale, sm_scale,
    BLOCK_M: tl.constexpr, HEAD_DIM: tl.constexpr, BLOCK_N: tl.constexpr,
    STAGE: tl.constexpr, warp_specialize: tl.constexpr, offs_m: tl.constexpr, offs_n: tl.constexpr,
    N_CTX: tl.constexpr, ENABLE_JVP: tl.constexpr, MASK_TYPE: tl.constexpr,
    MASK_CONST: tl.constexpr = -1e9,
):
    if STAGE == 1:
        # Non-causal: iterate over all K/V blocks
        lo, hi = 0, N_CTX
    elif STAGE == 2:
        # Causal diagonal block only
        lo, hi = start_m * BLOCK_M, (start_m + 1) * BLOCK_M
        lo = tl.multiple_of(lo, BLOCK_M)
    else:
        # Causal attention: iterate up to current Q position
        lo, hi = 0, (start_m + 1) * BLOCK_M
        hi = min(hi, N_CTX)

    offsetk_y = offset_y + lo
    offsetv_y = offset_y + lo # Assuming standard layout, adj if FP8 block shapes differ

    if MASK_TYPE > 0:
        mask_o_block_ptr = tl.advance(mask_o_block_ptr, (0, lo))

    for start_n in tl.range(lo, hi, BLOCK_N, warp_specialize=warp_specialize):
        start_n = tl.multiple_of(start_n, BLOCK_N)
        
        # Load K via TMA (Transposed)
        k_o = desc_k_o.load([offsetk_y, 0]).T
        qk = tl.dot(q_o, k_o)

        qk = qk * qk_scale

        if ENABLE_JVP:
            t_k_o = desc_t_k_o.load([offsetk_y, 0]).T
            t_qk = tl.dot(t_q_o, k_o) + tl.dot(q_o, t_k_o)

        if MASK_TYPE > 0:
            mask = tl.load(mask_o_block_ptr, boundary_check=(0, 1), padding_option="zero")
            if MASK_TYPE == 1:
                qk = qk + tl.where(mask == 1, 0.0, MASK_CONST)
            else:
                is_oob = (start_n + offs_n[None, :]) >= N_CTX
                mask = tl.where(is_oob, MASK_CONST, mask)
                qk = qk + mask
            
            if STAGE == 3:
                causal_mask = offs_m[:, None] >= (start_n + offs_n[None, :])
                qk = tl.where(causal_mask, qk, MASK_CONST)

            m_curr = tl.max(qk, 1)
            m_ij = tl.maximum(m_i_o, m_curr)
            qk = qk - m_ij[:, None]

        elif STAGE == 3:
            causal_mask = offs_m[:, None] >= (start_n + offs_n[None, :])
            qk = tl.where(causal_mask, qk, MASK_CONST)
            m_curr = tl.max(qk, 1)
            m_ij = tl.maximum(m_i_o, m_curr)
            qk = qk - m_ij[:, None]

        elif STAGE == 2:
            mask = offs_m[:, None] >= (start_n + offs_n[None, :])
            qk = tl.where(mask, qk, MASK_CONST)
            m_curr = tl.max(qk, 1)
            m_ij = tl.maximum(m_i_o, m_curr)
            qk = qk - m_ij[:, None]

        else:
            # STAGE == 1: Non-causal, no mask
            m_curr = tl.max(qk, 1)
            m_ij = tl.maximum(m_i_o, m_curr)
            qk = qk - m_ij[:, None]

        p = tl.math.exp2(qk)
        
        if MASK_TYPE > 0 and STAGE == 3:
            if MASK_TYPE == 1:
                combined_mask = (mask == 1) & causal_mask
            else:
                combined_mask = causal_mask
            p = tl.where(combined_mask, p, 0.0)
            if ENABLE_JVP:
                t_qk = tl.where(combined_mask, t_qk, 0.0)
        elif MASK_TYPE == 1:
            p = tl.where(mask == 1, p, 0.0)
            if ENABLE_JVP:
                t_qk = tl.where(mask == 1, t_qk, 0.0)
        elif STAGE == 3:
            p = tl.where(causal_mask, p, 0.0)
            if ENABLE_JVP:
                t_qk = tl.where(causal_mask, t_qk, 0.0)

        l_ij = tl.sum(p, 1)
        alpha = tl.math.exp2(m_i_o - m_ij)
        l_i_o = l_i_o * alpha + l_ij
        acc_o = acc_o * alpha[:, None]
        
        v_o = desc_v_o.load([offsetv_y, 0])
        p_cast = p.to(dtype)
        acc_o = tl.dot(p_cast, v_o.to(dtype), acc_o)

        if ENABLE_JVP:
            t_v_o = desc_t_v_o.load([offsetv_y, 0])
            # dp/dqk = p * sm_scale
            dp = p_cast * (t_qk * sm_scale)
            
            g_acc_o = g_acc_o * alpha[:, None]
            g_acc_o = tl.dot(dp.to(v_o.dtype), v_o, g_acc_o)
            
            mu_ij = tl.sum(dp, 1)
            mu_i_o = mu_i_o * alpha + mu_ij
            
            p_tv_acc_o = p_tv_acc_o * alpha[:, None]
            p_tv_acc_o = tl.dot(p_cast, t_v_o.to(dtype), p_tv_acc_o)

        m_i_o = m_ij

        offsetk_y += BLOCK_N
        offsetv_y += BLOCK_N
        if MASK_TYPE > 0:
            mask_o_block_ptr = tl.advance(mask_o_block_ptr, (0, BLOCK_N))

    return acc_o, g_acc_o, l_i_o, m_i_o, mu_i_o, p_tv_acc_o


@triton.jit
def _ebt_attn_fwd_inner_op_tma(
    acc_p,
    g_acc_p,
    l_i_p,
    m_i_p,
    mu_i_p,
    p_tv_acc_p,
    q_p, t_q_p,
    desc_k_o,
    desc_v_o,
    desc_t_k_o,
    desc_t_v_o,
    desc_k_p,
    desc_v_p,
    desc_t_k_p,
    desc_t_v_p,
    offset_y,
    qo_offset_y, # specific offset for current Q row for Superdiagonal
    mask_p_block_ptr,
    Mask_p,
    stride_mpm, stride_mpn,
    dtype: tl.constexpr, start_m, qk_scale, sm_scale,
    BLOCK_M: tl.constexpr, HEAD_DIM: tl.constexpr, BLOCK_N: tl.constexpr,
    STAGE: tl.constexpr, warp_specialize: tl.constexpr, offs_m: tl.constexpr, offs_n: tl.constexpr,
    N_CTX: tl.constexpr, ENABLE_JVP: tl.constexpr, MASK_TYPE: tl.constexpr,
    MASK_CONST: tl.constexpr = -1e9,
):
    if STAGE == 1:
        lo, hi = 0, N_CTX
    elif STAGE == 2:
        lo, hi = start_m * BLOCK_M, (start_m + 1) * BLOCK_M
        lo = tl.multiple_of(lo, BLOCK_M)
    else:
        # Causal attention: iterate up to current Q position
        lo, hi = 0, (start_m + 1) * BLOCK_M
        hi = min(hi, N_CTX)

    offsetk_y = offset_y + lo
    offsetv_y = offset_y + lo 

    if MASK_TYPE > 0:
        mask_p_block_ptr = tl.advance(mask_p_block_ptr, (0, lo))

    # Cross-attention Loop: Q_p attending to K_o
    for start_n in tl.range(lo, hi, BLOCK_N, warp_specialize=warp_specialize):
        start_n = tl.multiple_of(start_n, BLOCK_N)

        k_o = desc_k_o.load([offsetk_y, 0]).T
        qk = tl.dot(q_p, k_o)

        qk = qk * qk_scale

        if ENABLE_JVP:
            t_k_o = desc_t_k_o.load([offsetk_y, 0]).T
            t_qk = tl.dot(t_q_p, k_o) + tl.dot(q_p, t_k_o)

        superdiag_mask = offs_m[:, None] != (start_n + offs_n[None, :] - 1)

        if MASK_TYPE > 0 and STAGE == 3:
            # Both explicit mask AND causal mask
            causal_mask = offs_m[:, None] >= (start_n + offs_n[None, :])
            mask = tl.load(mask_p_block_ptr, boundary_check=(0, 1), padding_option="zero")
            if MASK_TYPE == 1:
                # Boolean mask: combine with causal
                combined_mask = causal_mask & (mask == 1) & superdiag_mask
                qk = qk + tl.where(combined_mask, 0.0, MASK_CONST)
            else:
                # Float mask: add mask where causal allows, else MASK_CONST
                is_oob = (start_n + offs_n[None, :]) >= N_CTX
                mask = tl.where(is_oob, MASK_CONST, mask)
                valid_locs = causal_mask & superdiag_mask
                qk = qk + tl.where(valid_locs, mask, MASK_CONST)
            m_curr = tl.max(qk, 1)
            m_ij = tl.maximum(m_i_p, m_curr)
            qk = qk - m_ij[:, None]
            
        elif MASK_TYPE > 0:
            # mask + superdiag exclusion (no causal)
            mask = tl.load(mask_p_block_ptr, boundary_check=(0, 1), padding_option="zero")
            if MASK_TYPE == 1:
                combined_mask = (mask == 1) & superdiag_mask
                qk = qk + tl.where(combined_mask, 0.0, MASK_CONST)
            else:
                is_oob = (start_n + offs_n[None, :]) >= N_CTX
                mask = tl.where(is_oob, MASK_CONST, mask)
                qk = qk + tl.where(superdiag_mask, mask, MASK_CONST)

            m_curr = tl.max(qk, 1)
            m_ij = tl.maximum(m_i_p, m_curr)
            qk = qk - m_ij[:, None]
            
        elif STAGE == 3:
            # Causal + superdiag exclusion
            causal_mask = offs_m[:, None] >= (start_n + offs_n[None, :])
            combined_mask = causal_mask & superdiag_mask
            qk = qk + tl.where(combined_mask, 0.0, MASK_CONST)
            m_curr = tl.max(qk, 1)
            m_ij = tl.maximum(m_i_p, m_curr)
            qk = qk - m_ij[:, None]
            
        elif STAGE == 2:
            # Legacy diagonal block
            mask = offs_m[:, None] >= (start_n + offs_n[None, :])
            qk = qk + tl.where(mask, 0.0, MASK_CONST)
            m_curr = tl.max(qk, 1)
            m_ij = tl.maximum(m_i_p, m_curr)
            qk = qk - m_ij[:, None]
            
        else:
            # Non-causal, no mask, but STILL exclude superdiag position
            qk = qk + tl.where(superdiag_mask, 0.0, MASK_CONST)
            m_curr = tl.max(qk, 1)
            m_ij = tl.maximum(m_i_p, m_curr)
            qk = qk - m_ij[:, None]

        p = tl.math.exp2(qk)
        
        if MASK_TYPE > 0 and STAGE == 3:
            if MASK_TYPE == 1:
                combined_mask = causal_mask & (mask == 1) & superdiag_mask
            else:
                combined_mask = causal_mask & superdiag_mask
            p = tl.where(combined_mask, p, 0.0)
            if ENABLE_JVP:
                t_qk = tl.where(combined_mask, t_qk, 0.0)
        elif MASK_TYPE == 1:
            combined_mask = (mask == 1) & superdiag_mask
            p = tl.where(combined_mask, p, 0.0)
            if ENABLE_JVP:
                t_qk = tl.where(combined_mask, t_qk, 0.0)
        elif MASK_TYPE == 2:
            p = tl.where(superdiag_mask, p, 0.0)
            if ENABLE_JVP:
                t_qk = tl.where(superdiag_mask, t_qk, 0.0)
        elif STAGE == 3:
            combined_mask = causal_mask & superdiag_mask
            p = tl.where(combined_mask, p, 0.0)
            if ENABLE_JVP:
                t_qk = tl.where(combined_mask, t_qk, 0.0)
        else:
            # Non-causal, no mask - still zero superdiag position
            p = tl.where(superdiag_mask, p, 0.0)
            if ENABLE_JVP:
                t_qk = tl.where(superdiag_mask, t_qk, 0.0)

        l_ij = tl.sum(p, 1)
        alpha = tl.math.exp2(m_i_p - m_ij)
        l_i_p = l_i_p * alpha + l_ij
        acc_p = acc_p * alpha[:, None]

        v_o = desc_v_o.load([offsetv_y, 0])
        p_cast = p.to(dtype)

        if ENABLE_JVP:
            t_v_o = desc_t_v_o.load([offsetv_y, 0])
            dp = p_cast * (t_qk * sm_scale)
            
            g_acc_p = g_acc_p * alpha[:, None]
            g_acc_p = tl.dot(dp.to(v_o.dtype), v_o, g_acc_p)
            
            mu_ij = tl.sum(dp, 1)
            mu_i_p = mu_i_p * alpha + mu_ij
            
            p_tv_acc_p = p_tv_acc_p * alpha[:, None]
            p_tv_acc_p = tl.dot(p_cast, t_v_o.to(dtype), p_tv_acc_p)

        acc_p = tl.dot(p_cast, v_o.to(dtype), acc_p)
        m_i_p = m_ij

        offsetk_y += BLOCK_N
        offsetv_y += BLOCK_N
        if MASK_TYPE > 0:
            mask_p_block_ptr = tl.advance(mask_p_block_ptr, (0, BLOCK_N))

    # --- Superdiagonal: q_p[i] @ k_p[i] ---
    # In TMA, we load the K_p and V_p block corresponding to the current query row.
    # desc_k_p is (Y, Head_Dim), we access [qo_offset_y, 0]
    
    k_p = desc_k_p.load([qo_offset_y, 0])
    v_p = desc_v_p.load([qo_offset_y, 0])
    
    qk_superdiag = tl.sum(q_p * k_p, axis=1) * qk_scale

    if ENABLE_JVP:
        t_k_p = desc_t_k_p.load([qo_offset_y, 0])
        t_v_p = desc_t_v_p.load([qo_offset_y, 0])
        t_qk_superdiag = tl.sum(t_q_p * k_p + q_p * t_k_p, axis=1)

    superdiag_mask = tl.zeros([BLOCK_M], dtype=tl.float32)
    if MASK_TYPE > 0:
        superdiag_col = offs_m + 1 
        superdiag_mask_ptrs = Mask_p + offs_m * stride_mpm + superdiag_col * stride_mpn
        superdiag_mask = tl.load(superdiag_mask_ptrs, mask=offs_m < N_CTX, other=0.0)
        
        if MASK_TYPE == 1:
            qk_superdiag = tl.where(superdiag_mask == 1, qk_superdiag, MASK_CONST)
        else:
            qk_superdiag = qk_superdiag + superdiag_mask

    m_ij_superdiag = tl.maximum(m_i_p, qk_superdiag)
    qk_superdiag_shifted = qk_superdiag - m_ij_superdiag
    p_superdiag = tl.math.exp2(qk_superdiag_shifted)

    if MASK_TYPE == 1:
        p_superdiag = tl.where(superdiag_mask == 1, p_superdiag, 0.0)
        if ENABLE_JVP:
            t_qk_superdiag = tl.where(superdiag_mask == 1, t_qk_superdiag, 0.0)

    alpha_superdiag = tl.math.exp2(m_i_p - m_ij_superdiag)
    l_i_p = l_i_p * alpha_superdiag + p_superdiag
    
    acc_p = acc_p * alpha_superdiag[:, None]
    acc_p = acc_p + (p_superdiag[:, None] * v_p).to(acc_p.dtype)

    if ENABLE_JVP:
        dp_superdiag = p_superdiag * (t_qk_superdiag * sm_scale)
        
        g_acc_p = g_acc_p * alpha_superdiag[:, None]
        g_acc_p = g_acc_p + (dp_superdiag[:, None] * v_p).to(g_acc_p.dtype)
        
        mu_i_p = mu_i_p * alpha_superdiag + dp_superdiag
        
        p_tv_acc_p = p_tv_acc_p * alpha_superdiag[:, None]
        p_tv_acc_p = p_tv_acc_p + (p_superdiag[:, None] * t_v_p).to(p_tv_acc_p.dtype)

    m_i_p = m_ij_superdiag

    return acc_p, g_acc_p, l_i_p, m_i_p, mu_i_p, p_tv_acc_p



@triton.autotune(
    configs=get_fwd_autotune_configs(),
    key=['N_CTX', 'HEAD_DIM', 'STAGE', 'MASK_TYPE','warp_specialize'],
)
@triton.jit
def _ebt_attn_fwd_tma(
    desc_q_o, desc_k_o, desc_v_o,
    desc_q_p, desc_k_p, desc_v_p,
    desc_t_q_o, desc_t_k_o, desc_t_v_o,
    desc_t_q_p, desc_t_k_p, desc_t_v_p,
    sm_scale,
    Mask_o, Mask_p,
    desc_out_o, desc_out_p,
    desc_t_out_o, desc_t_out_p,
    M_o, M_p,
    stride_qz, stride_qh, stride_qm, stride_qk,
    stride_kz, stride_kh, stride_kn, stride_kk,
    stride_vz, stride_vh, stride_vn, stride_vk,
    stride_oz, stride_oh, stride_om, stride_ok,
    stride_mom, stride_mon,
    stride_mpm, stride_mpn,
    Z, H, N_CTX,
    HEAD_DIM: tl.constexpr,
    BLOCK_M: tl.constexpr,
    BLOCK_N: tl.constexpr,
    STAGE: tl.constexpr,
    warp_specialize: tl.constexpr,
    ENABLE_JVP: tl.constexpr,
    MASK_TYPE: tl.constexpr,
):
    tl.static_assert(BLOCK_N <= HEAD_DIM)

    start_m = tl.program_id(0)
    off_hz = tl.program_id(1)
    off_z = off_hz // H
    off_h = off_hz % H

    # 1/log(2)
    qk_scale = sm_scale * 1.4426950408889634

    offset_y = off_z * (N_CTX * H) + off_h * N_CTX
    qo_offset_y = offset_y + start_m * BLOCK_M

    # Setup O-stream Descriptors
    desc_q_o = _maybe_make_tensor_desc(desc_q_o, [Z*H*N_CTX, HEAD_DIM], [HEAD_DIM, 1], [BLOCK_M, HEAD_DIM])
    desc_k_o = _maybe_make_tensor_desc(desc_k_o, [Z*H*N_CTX, HEAD_DIM], [HEAD_DIM, 1], [BLOCK_N, HEAD_DIM])
    desc_v_o = _maybe_make_tensor_desc(desc_v_o, [Z*H*N_CTX, HEAD_DIM], [HEAD_DIM, 1], [BLOCK_N, HEAD_DIM])
    desc_out_o = _maybe_make_tensor_desc(desc_out_o, [Z*H*N_CTX, HEAD_DIM], [HEAD_DIM, 1], [BLOCK_M, HEAD_DIM])

    # Setup P-stream Descriptors
    desc_q_p = _maybe_make_tensor_desc(desc_q_p, [Z*H*N_CTX, HEAD_DIM], [HEAD_DIM, 1], [BLOCK_M, HEAD_DIM])
    desc_k_p = _maybe_make_tensor_desc(desc_k_p, [Z*H*N_CTX, HEAD_DIM], [HEAD_DIM, 1], [BLOCK_M, HEAD_DIM])
    desc_v_p = _maybe_make_tensor_desc(desc_v_p, [Z*H*N_CTX, HEAD_DIM], [HEAD_DIM, 1], [BLOCK_M, HEAD_DIM])
    desc_out_p = _maybe_make_tensor_desc(desc_out_p, [Z*H*N_CTX, HEAD_DIM], [HEAD_DIM, 1], [BLOCK_M, HEAD_DIM])

    # Setup Tangent Descriptors
    if ENABLE_JVP:
        desc_t_q_o = _maybe_make_tensor_desc(desc_t_q_o, [Z*H*N_CTX, HEAD_DIM], [HEAD_DIM, 1], [BLOCK_M, HEAD_DIM])
        desc_t_k_o = _maybe_make_tensor_desc(desc_t_k_o, [Z*H*N_CTX, HEAD_DIM], [HEAD_DIM, 1], [BLOCK_N, HEAD_DIM])
        desc_t_v_o = _maybe_make_tensor_desc(desc_t_v_o, [Z*H*N_CTX, HEAD_DIM], [HEAD_DIM, 1], [BLOCK_N, HEAD_DIM])
        desc_t_out_o = _maybe_make_tensor_desc(desc_t_out_o, [Z*H*N_CTX, HEAD_DIM], [HEAD_DIM, 1], [BLOCK_M, HEAD_DIM])
        
        desc_t_q_p = _maybe_make_tensor_desc(desc_t_q_p, [Z*H*N_CTX, HEAD_DIM], [HEAD_DIM, 1], [BLOCK_M, HEAD_DIM])
        desc_t_k_p = _maybe_make_tensor_desc(desc_t_k_p, [Z*H*N_CTX, HEAD_DIM], [HEAD_DIM, 1], [BLOCK_M, HEAD_DIM])
        desc_t_v_p = _maybe_make_tensor_desc(desc_t_v_p, [Z*H*N_CTX, HEAD_DIM], [HEAD_DIM, 1], [BLOCK_M, HEAD_DIM])
        desc_t_out_p = _maybe_make_tensor_desc(desc_t_out_p, [Z*H*N_CTX, HEAD_DIM], [HEAD_DIM, 1], [BLOCK_M, HEAD_DIM])

        t_q_o = desc_t_q_o.load([qo_offset_y, 0])
        t_q_p = desc_t_q_p.load([qo_offset_y, 0])
        
        # Init accumulators for JVP
        g_acc_o = tl.zeros([BLOCK_M, HEAD_DIM], dtype=tl.float32)
        mu_i_o = tl.zeros([BLOCK_M], dtype=tl.float32)
        p_tv_acc_o = tl.zeros([BLOCK_M, HEAD_DIM], dtype=tl.float32)
        
        g_acc_p = tl.zeros([BLOCK_M, HEAD_DIM], dtype=tl.float32)
        mu_i_p = tl.zeros([BLOCK_M], dtype=tl.float32)
        p_tv_acc_p = tl.zeros([BLOCK_M, HEAD_DIM], dtype=tl.float32)
    else:
        t_q_o, t_q_p = None, None
        desc_t_k_o, desc_t_v_o = None, None
        desc_t_k_p, desc_t_v_p = None, None
        g_acc_o, mu_i_o, p_tv_acc_o = tl.zeros([1,1], tl.float32), tl.zeros([1], tl.float32), tl.zeros([1,1], tl.float32)
        g_acc_p, mu_i_p, p_tv_acc_p = tl.zeros([1,1], tl.float32), tl.zeros([1], tl.float32), tl.zeros([1,1], tl.float32)

    # Load Queries
    q_o = desc_q_o.load([qo_offset_y, 0])
    q_p = desc_q_p.load([qo_offset_y, 0])

    # Offsets and Masks
    offs_m = start_m * BLOCK_M + tl.arange(0, BLOCK_M)
    offs_n = tl.arange(0, BLOCK_N)
    
    # ORIGINAL STREAM (O->O) ATTENTION
    m_i_o = tl.zeros([BLOCK_M], dtype=tl.float32) - float("inf")
    acc_o = tl.zeros([BLOCK_M, HEAD_DIM], dtype=tl.float32)
    l_i_o = tl.zeros([BLOCK_M], dtype=tl.float32)

    if MASK_TYPE > 0:
        mask_o_block_ptr = tl.make_block_ptr(
            base=Mask_o,
            shape=(N_CTX, N_CTX),
            strides=(stride_mom, stride_mon),
            offsets=(start_m * BLOCK_M, 0),
            block_shape=(BLOCK_M, BLOCK_N),
            order=(1, 0),
        )
    else:
        mask_o_block_ptr = None

    acc_o, g_acc_o, l_i_o, m_i_o, mu_i_o, p_tv_acc_o = _ebt_attn_fwd_inner_oo_tma(
        acc_o, g_acc_o, l_i_o, m_i_o, mu_i_o, p_tv_acc_o,
        q_o, t_q_o,
        desc_k_o, desc_v_o, desc_t_k_o, desc_t_v_o,
        offset_y,
        mask_o_block_ptr,
        q_o.dtype, start_m, qk_scale, sm_scale,
        BLOCK_M, HEAD_DIM, BLOCK_N,
        STAGE, warp_specialize, offs_m, offs_n, N_CTX,
        ENABLE_JVP, MASK_TYPE
    )

    # Epilogue O
    empty_mask_o = l_i_o == 0.0
    if empty_mask_o.sum() > 0:
        l_i_o = tl.where(empty_mask_o, 1.0, l_i_o)
    
    m_i_o = m_i_o + tl.where(empty_mask_o, 0.0, tl.math.log2(l_i_o))
    acc_o = acc_o / l_i_o[:, None]
    
    m_o_ptrs = M_o + off_hz * N_CTX + offs_m
    tl.store(m_o_ptrs, m_i_o, mask=offs_m < N_CTX)
    desc_out_o.store([qo_offset_y, 0], acc_o.to(desc_out_o.dtype))

    if ENABLE_JVP:
        t_o_v = g_acc_o / l_i_o[:, None] - (mu_i_o / l_i_o)[:, None] * acc_o
        t_yo_out = t_o_v + p_tv_acc_o / l_i_o[:, None]
        desc_t_out_o.store([qo_offset_y, 0], t_yo_out.to(desc_t_out_o.dtype))

    # PREDICTED STREAM (P->O + Superdiag) ATTENTION
    m_i_p = tl.zeros([BLOCK_M], dtype=tl.float32) - float("inf")
    acc_p = tl.zeros([BLOCK_M, HEAD_DIM], dtype=tl.float32)
    l_i_p = tl.zeros([BLOCK_M], dtype=tl.float32)

    if MASK_TYPE > 0:
        mask_p_block_ptr = tl.make_block_ptr(
            base=Mask_p,
            shape=(N_CTX, N_CTX + 1),
            strides=(stride_mpm, stride_mpn),
            offsets=(start_m * BLOCK_M, 0),
            block_shape=(BLOCK_M, BLOCK_N),
            order=(1, 0),
        )
    else:
        mask_p_block_ptr = None

    acc_p, g_acc_p, l_i_p, m_i_p, mu_i_p, p_tv_acc_p = _ebt_attn_fwd_inner_op_tma(
        acc_p, g_acc_p, l_i_p, m_i_p, mu_i_p, p_tv_acc_p,
        q_p, t_q_p,
        desc_k_o, desc_v_o, desc_t_k_o, desc_t_v_o,
        desc_k_p, desc_v_p, desc_t_k_p, desc_t_v_p,
        offset_y, qo_offset_y,
        mask_p_block_ptr, Mask_p,
        stride_mpm, stride_mpn,
        q_o.dtype, start_m, qk_scale, sm_scale,
        BLOCK_M, HEAD_DIM, BLOCK_N,
        STAGE, warp_specialize, offs_m, offs_n, N_CTX,
        ENABLE_JVP, MASK_TYPE
    )

    # Epilogue P
    empty_mask_p = l_i_p == 0.0
    if empty_mask_p.sum() > 0:
        l_i_p = tl.where(empty_mask_p, 1.0, l_i_p)

    m_i_p = m_i_p + tl.where(empty_mask_p, 0.0, tl.math.log2(l_i_p))
    acc_p = acc_p / l_i_p[:, None]

    m_p_ptrs = M_p + off_hz * N_CTX + offs_m
    tl.store(m_p_ptrs, m_i_p, mask=offs_m < N_CTX)
    desc_out_p.store([qo_offset_y, 0], acc_p.to(desc_out_p.dtype))

    if ENABLE_JVP:
        t_p_v = g_acc_p / l_i_p[:, None] - (mu_i_p / l_i_p)[:, None] * acc_p
        t_yp_out = t_p_v + p_tv_acc_p / l_i_p[:, None]
        desc_t_out_p.store([qo_offset_y, 0], t_yp_out.to(desc_t_out_p.dtype))