import triton
import triton.language as tl


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
                        )
                    )
    
    return configs


@triton.jit
def _ebt_attn_fwd_inner_oo(
    acc_o,
    g_acc_o,
    l_i_o,
    m_i_o,
    mu_i_o,
    p_tv_acc_o,
    q_o, t_q_o,
    K_o_block_ptr,
    V_o_block_ptr,
    T_K_o_block_ptr,
    T_V_o_block_ptr,
    mask_o_block_ptr,
    dtype: tl.constexpr, start_m, qk_scale, sm_scale,
    BLOCK_M: tl.constexpr, HEAD_DIM: tl.constexpr, BLOCK_N: tl.constexpr,
    STAGE: tl.constexpr, offs_m: tl.constexpr, offs_n: tl.constexpr,
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

    K_o_block_ptr = tl.advance(K_o_block_ptr, (0, lo))
    V_o_block_ptr = tl.advance(V_o_block_ptr, (lo, 0))
    if ENABLE_JVP:
        T_K_o_block_ptr = tl.advance(T_K_o_block_ptr, (0, lo))
        T_V_o_block_ptr = tl.advance(T_V_o_block_ptr, (lo, 0))
    if MASK_TYPE > 0:
        mask_o_block_ptr = tl.advance(mask_o_block_ptr, (0, lo))

    for start_n in range(lo, hi, BLOCK_N):
        start_n = tl.multiple_of(start_n, BLOCK_N)
        
        k_o = tl.load(K_o_block_ptr, boundary_check=(1,), padding_option="zero")
        qk = tl.dot(q_o, k_o)

        qk = qk * qk_scale

        if ENABLE_JVP:
            t_k_o = tl.load(T_K_o_block_ptr, boundary_check=(1,), padding_option="zero")
            t_qk = tl.dot(t_q_o, k_o) + tl.dot(q_o, t_k_o)

        if MASK_TYPE > 0:
            mask = tl.load(mask_o_block_ptr, boundary_check=(0, 1), padding_option="zero")
            if MASK_TYPE == 1:
                qk = qk + tl.where(mask == 1, 0.0, MASK_CONST)
            else:
                # We must explicitly check for OOB columns.
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
        
        v_o = tl.load(V_o_block_ptr, boundary_check=(0,), padding_option="zero")
        p_cast = p.to(dtype)
        acc_o = tl.dot(p_cast, v_o.to(dtype), acc_o)

        if ENABLE_JVP:
            t_v_o = tl.load(T_V_o_block_ptr, boundary_check=(0,), padding_option="zero")
            # dp/dqk = p * sm_scale (after log2 correction already in p)
            dp = p_cast * (t_qk * sm_scale)
            
            g_acc_o = g_acc_o * alpha[:, None]
            g_acc_o = tl.dot(dp.to(v_o.dtype), v_o, g_acc_o)
            
            mu_ij = tl.sum(dp, 1)
            mu_i_o = mu_i_o * alpha + mu_ij
            
            p_tv_acc_o = p_tv_acc_o * alpha[:, None]
            p_tv_acc_o = tl.dot(p_cast, t_v_o.to(dtype), p_tv_acc_o)
            
            T_K_o_block_ptr = tl.advance(T_K_o_block_ptr, (0, BLOCK_N))
            T_V_o_block_ptr = tl.advance(T_V_o_block_ptr, (BLOCK_N, 0))

        m_i_o = m_ij

        K_o_block_ptr = tl.advance(K_o_block_ptr, (0, BLOCK_N))
        V_o_block_ptr = tl.advance(V_o_block_ptr, (BLOCK_N, 0))
        if MASK_TYPE > 0:
            mask_o_block_ptr = tl.advance(mask_o_block_ptr, (0, BLOCK_N))

    return acc_o, g_acc_o, l_i_o, m_i_o, mu_i_o, p_tv_acc_o


@triton.jit
def _ebt_attn_fwd_inner_op(
    acc_p,
    g_acc_p,
    l_i_p,
    m_i_p,
    mu_i_p,
    p_tv_acc_p,
    q_p, t_q_p,
    K_o_block_ptr,
    V_o_block_ptr,
    T_K_o_block_ptr,
    T_V_o_block_ptr,
    K_p_block_ptr,
    V_p_block_ptr,
    T_K_p_block_ptr,
    T_V_p_block_ptr,
    mask_p_block_ptr,
    Mask_p,
    off_z, off_h,
    stride_mpm, stride_mpn,
    dtype: tl.constexpr, start_m, qk_scale, sm_scale,
    BLOCK_M: tl.constexpr, HEAD_DIM: tl.constexpr, BLOCK_N: tl.constexpr,
    STAGE: tl.constexpr, offs_m: tl.constexpr, offs_n: tl.constexpr,
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

    K_o_block_ptr = tl.advance(K_o_block_ptr, (0, lo))
    V_o_block_ptr = tl.advance(V_o_block_ptr, (lo, 0))
    if ENABLE_JVP:
        T_K_o_block_ptr = tl.advance(T_K_o_block_ptr, (0, lo))
        T_V_o_block_ptr = tl.advance(T_V_o_block_ptr, (lo, 0))
    if MASK_TYPE > 0:
        mask_p_block_ptr = tl.advance(mask_p_block_ptr, (0, lo))

    # Cross-attention: q_p[i] can attend to k_o[j] only for j <= i (causal)
    for start_n in range(lo, hi, BLOCK_N):
        start_n = tl.multiple_of(start_n, BLOCK_N)

        k_o = tl.load(K_o_block_ptr, boundary_check=(1,), padding_option="zero")
        qk = tl.dot(q_p, k_o)

        qk = qk * qk_scale

        if ENABLE_JVP:
            t_k_o = tl.load(T_K_o_block_ptr, boundary_check=(1,), padding_option="zero")
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

        v_o = tl.load(V_o_block_ptr, boundary_check=(0,), padding_option="zero")
        p_cast = p.to(dtype)

        if ENABLE_JVP:
            t_v_o = tl.load(T_V_o_block_ptr, boundary_check=(0,), padding_option="zero")
            dp = p_cast * (t_qk * sm_scale)
            
            g_acc_p = g_acc_p * alpha[:, None]
            g_acc_p = tl.dot(dp.to(v_o.dtype), v_o, g_acc_p)
            
            mu_ij = tl.sum(dp, 1)
            mu_i_p = mu_i_p * alpha + mu_ij
            
            p_tv_acc_p = p_tv_acc_p * alpha[:, None]
            p_tv_acc_p = tl.dot(p_cast, t_v_o.to(dtype), p_tv_acc_p)
            
            T_K_o_block_ptr = tl.advance(T_K_o_block_ptr, (0, BLOCK_N))
            T_V_o_block_ptr = tl.advance(T_V_o_block_ptr, (BLOCK_N, 0))

        acc_p = tl.dot(p_cast, v_o.to(dtype), acc_p)
        m_i_p = m_ij

        K_o_block_ptr = tl.advance(K_o_block_ptr, (0, BLOCK_N))
        V_o_block_ptr = tl.advance(V_o_block_ptr, (BLOCK_N, 0))
        if MASK_TYPE > 0:
            mask_p_block_ptr = tl.advance(mask_p_block_ptr, (0, BLOCK_N))

    # Superdiagonal: q_p[i] @ k_p[i] - this REPLACES position (i, i+1)
    # Since (i, i+1) was zeroed in cross-attention, adding it here is equivalent
    k_p = tl.load(K_p_block_ptr, boundary_check=(0,), padding_option="zero")
    v_p = tl.load(V_p_block_ptr, boundary_check=(0,), padding_option="zero")
    
    qk_superdiag = tl.sum(q_p * k_p, axis=1) * qk_scale

    if ENABLE_JVP:
        t_k_p = tl.load(T_K_p_block_ptr, boundary_check=(0,), padding_option="zero")
        t_v_p = tl.load(T_V_p_block_ptr, boundary_check=(0,), padding_option="zero")
        t_qk_superdiag = tl.sum(t_q_p * k_p + q_p * t_k_p, axis=1)

    superdiag_mask = tl.zeros([BLOCK_M], dtype=tl.float32)
    if MASK_TYPE > 0:
        superdiag_col = offs_m + 1  # Column index for superdiagonal
        superdiag_mask_ptrs = Mask_p + offs_m * stride_mpm + superdiag_col * stride_mpn
        superdiag_mask = tl.load(superdiag_mask_ptrs, mask=offs_m < N_CTX, other=0.0)
        
        if MASK_TYPE == 1:
            # Boolean mask
            qk_superdiag = tl.where(superdiag_mask == 1, qk_superdiag, MASK_CONST)
        else:
            # Float mask
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
    key=['N_CTX', 'HEAD_DIM', 'STAGE', 'MASK_TYPE'],
)
@triton.jit
def _ebt_attn_fwd(
    Q_o, K_o, V_o,
    Q_p, K_p, V_p,
    T_Q_o, T_K_o, T_V_o,
    T_Q_p, T_K_p, T_V_p,
    sm_scale,
    Mask_o, Mask_p,
    Out_o, Out_p,
    T_Out_o, T_Out_p,
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

    qk_scale = sm_scale * 1.4426950408889634 # 1/log(2)
    
    offs_m = start_m * BLOCK_M + tl.arange(0, BLOCK_M)
    offs_n = tl.arange(0, BLOCK_N)
    offs_d = tl.arange(0, HEAD_DIM)

    # Compute base offset for this batch/head
    qkv_offset = off_z.to(tl.int64) * stride_qz + off_h.to(tl.int64) * stride_qh
    
    # ORIGINAL STREAM (O->O) ATTENTION
    Q_o_block_ptr = tl.make_block_ptr(
        base=Q_o + qkv_offset,
        shape=(N_CTX, HEAD_DIM),
        strides=(stride_qm, stride_qk),
        offsets=(start_m * BLOCK_M, 0),
        block_shape=(BLOCK_M, HEAD_DIM),
        order=(1, 0),
    )
    K_o_block_ptr = tl.make_block_ptr(
        base=K_o + qkv_offset,
        shape=(HEAD_DIM, N_CTX),
        strides=(stride_kk, stride_kn),
        offsets=(0, 0),
        block_shape=(HEAD_DIM, BLOCK_N),
        order=(0, 1),
    )
    V_o_block_ptr = tl.make_block_ptr(
        base=V_o + qkv_offset,
        shape=(N_CTX, HEAD_DIM),
        strides=(stride_vn, stride_vk),
        offsets=(0, 0),
        block_shape=(BLOCK_N, HEAD_DIM),
        order=(1, 0),
    )
    Out_o_block_ptr = tl.make_block_ptr(
        base=Out_o + qkv_offset,
        shape=(N_CTX, HEAD_DIM),
        strides=(stride_om, stride_ok),
        offsets=(start_m * BLOCK_M, 0),
        block_shape=(BLOCK_M, HEAD_DIM),
        order=(1, 0),
    )

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

    m_i_o = tl.zeros([BLOCK_M], dtype=tl.float32) - float("inf")
    acc_o = tl.zeros([BLOCK_M, HEAD_DIM], dtype=tl.float32)
    l_i_o = tl.zeros([BLOCK_M], dtype=tl.float32)

    if ENABLE_JVP:
        T_Q_o_block_ptr = tl.make_block_ptr(
            base=T_Q_o + qkv_offset,
            shape=(N_CTX, HEAD_DIM),
            strides=(stride_qm, stride_qk),
            offsets=(start_m * BLOCK_M, 0),
            block_shape=(BLOCK_M, HEAD_DIM),
            order=(1, 0),
        )
        T_K_o_block_ptr = tl.make_block_ptr(
            base=T_K_o + qkv_offset,
            shape=(HEAD_DIM, N_CTX),
            strides=(stride_kk, stride_kn),
            offsets=(0, 0),
            block_shape=(HEAD_DIM, BLOCK_N),
            order=(0, 1),
        )
        T_V_o_block_ptr = tl.make_block_ptr(
            base=T_V_o + qkv_offset,
            shape=(N_CTX, HEAD_DIM),
            strides=(stride_vn, stride_vk),
            offsets=(0, 0),
            block_shape=(BLOCK_N, HEAD_DIM),
            order=(1, 0),
        )
        T_Out_o_block_ptr = tl.make_block_ptr(
            base=T_Out_o + qkv_offset,
            shape=(N_CTX, HEAD_DIM),
            strides=(stride_om, stride_ok),
            offsets=(start_m * BLOCK_M, 0),
            block_shape=(BLOCK_M, HEAD_DIM),
            order=(1, 0),
        )
        t_q_o = tl.load(T_Q_o_block_ptr, boundary_check=(0,), padding_option="zero")
        g_acc_o = tl.zeros([BLOCK_M, HEAD_DIM], dtype=tl.float32)
        mu_i_o = tl.zeros([BLOCK_M], dtype=tl.float32)
        p_tv_acc_o = tl.zeros([BLOCK_M, HEAD_DIM], dtype=tl.float32)
    else:
        t_q_o = None
        T_K_o_block_ptr = None
        T_V_o_block_ptr = None
        g_acc_o = tl.zeros([1, 1], dtype=tl.float32)
        mu_i_o = tl.zeros([1], dtype=tl.float32)
        p_tv_acc_o = tl.zeros([1, 1], dtype=tl.float32)
    
    q_o = tl.load(Q_o_block_ptr, boundary_check=(0,), padding_option="zero")
    
    acc_o, g_acc_o, l_i_o, m_i_o, mu_i_o, p_tv_acc_o = _ebt_attn_fwd_inner_oo(
        acc_o,
        g_acc_o,
        l_i_o,
        m_i_o,
        mu_i_o,
        p_tv_acc_o,
        q_o,
        t_q_o,
        K_o_block_ptr,
        V_o_block_ptr,
        T_K_o_block_ptr,
        T_V_o_block_ptr,
        mask_o_block_ptr,
        q_o.dtype,
        start_m,
        qk_scale,
        sm_scale,
        BLOCK_M,
        HEAD_DIM,
        BLOCK_N,
        STAGE,
        offs_m,
        offs_n,
        N_CTX,
        ENABLE_JVP,
        MASK_TYPE,
    )

    empty_mask = l_i_o == 0.0
    if empty_mask.sum() > 0:
        l_i_o = tl.where(
            empty_mask, 1.0, l_i_o
        )  # NOTE: This happens if the entire block is masked out.

    m_i_o = m_i_o + tl.where(
        # NOTE: This is needed to compute the logsumexp for the backward pass.
        empty_mask,
        0.0,
        tl.math.log2(l_i_o),
    )
    
    acc_o = acc_o / l_i_o[:, None]
    m_o_ptrs = M_o + off_hz * N_CTX + offs_m

    tl.store(m_o_ptrs, m_i_o, mask=offs_m < N_CTX)
    tl.store(Out_o_block_ptr, acc_o.to(Out_o.dtype.element_ty), boundary_check=(0,))
    
    if ENABLE_JVP:
        t_o_v = g_acc_o / l_i_o[:, None] - (mu_i_o / l_i_o)[:, None] * acc_o
        t_yo_out = t_o_v + p_tv_acc_o / l_i_o[:, None]
        tl.store(T_Out_o_block_ptr, t_yo_out.to(T_Out_o.dtype.element_ty), boundary_check=(0,))
    
    # PREDICTED STREAM (P->O + SUPERDIAGONAL) ATTENTION
    Q_p_block_ptr = tl.make_block_ptr(
        base=Q_p + qkv_offset,
        shape=(N_CTX, HEAD_DIM),
        strides=(stride_qm, stride_qk),
        offsets=(start_m * BLOCK_M, 0),
        block_shape=(BLOCK_M, HEAD_DIM),
        order=(1, 0),
    )
    K_p_block_ptr = tl.make_block_ptr(
        base=K_p + qkv_offset,
        shape=(N_CTX, HEAD_DIM),
        strides=(stride_kn, stride_kk),
        offsets=(start_m * BLOCK_M, 0),
        block_shape=(BLOCK_M, HEAD_DIM),
        order=(1, 0),
    )
    V_p_block_ptr = tl.make_block_ptr(
        base=V_p + qkv_offset,
        shape=(N_CTX, HEAD_DIM),
        strides=(stride_vn, stride_vk),
        offsets=(start_m * BLOCK_M, 0),
        block_shape=(BLOCK_M, HEAD_DIM),
        order=(1, 0),
    )
    Out_p_block_ptr = tl.make_block_ptr(
        base=Out_p + qkv_offset,
        shape=(N_CTX, HEAD_DIM),
        strides=(stride_om, stride_ok),
        offsets=(start_m * BLOCK_M, 0),
        block_shape=(BLOCK_M, HEAD_DIM),
        order=(1, 0),
    )

    # Reset K_o, V_o pointers for cross-attention
    K_o_block_ptr_p = tl.make_block_ptr(
        base=K_o + qkv_offset,
        shape=(HEAD_DIM, N_CTX),
        strides=(stride_kk, stride_kn),
        offsets=(0, 0),
        block_shape=(HEAD_DIM, BLOCK_N),
        order=(0, 1),
    )
    V_o_block_ptr_p = tl.make_block_ptr(
        base=V_o + qkv_offset,
        shape=(N_CTX, HEAD_DIM),
        strides=(stride_vn, stride_vk),
        offsets=(0, 0),
        block_shape=(BLOCK_N, HEAD_DIM),
        order=(1, 0),
    )

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

    m_i_p = tl.zeros([BLOCK_M], dtype=tl.float32) - float("inf")
    acc_p = tl.zeros([BLOCK_M, HEAD_DIM], dtype=tl.float32)
    l_i_p = tl.zeros([BLOCK_M], dtype=tl.float32)
    

    if ENABLE_JVP:
        T_Q_p_block_ptr = tl.make_block_ptr(
            base=T_Q_p + qkv_offset,
            shape=(N_CTX, HEAD_DIM),
            strides=(stride_qm, stride_qk),
            offsets=(start_m * BLOCK_M, 0),
            block_shape=(BLOCK_M, HEAD_DIM),
            order=(1, 0),
        )
        T_K_p_block_ptr = tl.make_block_ptr(
            base=T_K_p + qkv_offset,
            shape=(N_CTX, HEAD_DIM),
            strides=(stride_kn, stride_kk),
            offsets=(start_m * BLOCK_M, 0),
            block_shape=(BLOCK_M, HEAD_DIM),
            order=(1, 0),
        )
        T_V_p_block_ptr = tl.make_block_ptr(
            base=T_V_p + qkv_offset,
            shape=(N_CTX, HEAD_DIM),
            strides=(stride_vn, stride_vk),
            offsets=(start_m * BLOCK_M, 0),
            block_shape=(BLOCK_M, HEAD_DIM),
            order=(1, 0),
        )
        T_Out_p_block_ptr = tl.make_block_ptr(
            base=T_Out_p + qkv_offset,
            shape=(N_CTX, HEAD_DIM),
            strides=(stride_om, stride_ok),
            offsets=(start_m * BLOCK_M, 0),
            block_shape=(BLOCK_M, HEAD_DIM),
            order=(1, 0),
        )
        T_K_o_block_ptr_p = tl.make_block_ptr(
            base=T_K_o + qkv_offset,
            shape=(HEAD_DIM, N_CTX),
            strides=(stride_kk, stride_kn),
            offsets=(0, 0),
            block_shape=(HEAD_DIM, BLOCK_N),
            order=(0, 1),
        )
        T_V_o_block_ptr_p = tl.make_block_ptr(
            base=T_V_o + qkv_offset,
            shape=(N_CTX, HEAD_DIM),
            strides=(stride_vn, stride_vk),
            offsets=(0, 0),
            block_shape=(BLOCK_N, HEAD_DIM),
            order=(1, 0),
        )
        t_q_p = tl.load(T_Q_p_block_ptr, boundary_check=(0,), padding_option="zero")
        g_acc_p = tl.zeros([BLOCK_M, HEAD_DIM], dtype=tl.float32)
        mu_i_p = tl.zeros([BLOCK_M], dtype=tl.float32)
        p_tv_acc_p = tl.zeros([BLOCK_M, HEAD_DIM], dtype=tl.float32)
    else:
        t_q_p = None
        T_K_p_block_ptr = None
        T_V_p_block_ptr = None
        T_K_o_block_ptr_p = None
        T_V_o_block_ptr_p = None
        g_acc_p = tl.zeros([1, 1], dtype=tl.float32)
        mu_i_p = tl.zeros([1], dtype=tl.float32)
        p_tv_acc_p = tl.zeros([1, 1], dtype=tl.float32)

    q_p = tl.load(Q_p_block_ptr, boundary_check=(0,), padding_option="zero")

    acc_p, g_acc_p, l_i_p, m_i_p, mu_i_p, p_tv_acc_p = _ebt_attn_fwd_inner_op(
        acc_p,
        g_acc_p,
        l_i_p,
        m_i_p,
        mu_i_p,
        p_tv_acc_p,
        q_p,
        t_q_p,
        K_o_block_ptr_p,
        V_o_block_ptr_p,
        T_K_o_block_ptr_p,
        T_V_o_block_ptr_p,
        K_p_block_ptr,
        V_p_block_ptr,
        T_K_p_block_ptr,
        T_V_p_block_ptr,
        mask_p_block_ptr,
        Mask_p,
        off_z, off_h,
        stride_mpm, stride_mpn,
        q_p.dtype,
        start_m,
        qk_scale,
        sm_scale,
        BLOCK_M,
        HEAD_DIM,
        BLOCK_N,
        STAGE,
        offs_m,
        offs_n,
        N_CTX,
        ENABLE_JVP,
        MASK_TYPE,
    )
    
    empty_mask = l_i_p == 0.0
    if empty_mask.sum() > 0:
        l_i_p = tl.where(
            empty_mask, 1.0, l_i_p
        )  # NOTE: This happens if the entire block is masked out.

    m_i_p = m_i_p + tl.where(
        # NOTE: This is needed to compute the logsumexp for the backward pass.
        empty_mask,
        0.0,
        tl.math.log2(l_i_p),
    )
    
    acc_p = acc_p / l_i_p[:, None]
    m_p_ptrs = M_p + off_hz * N_CTX + offs_m

    tl.store(m_p_ptrs, m_i_p, mask=offs_m < N_CTX)
    tl.store(Out_p_block_ptr, acc_p.to(Out_p.dtype.element_ty), boundary_check=(0,))
    
    if ENABLE_JVP:
        t_p_v = g_acc_p / l_i_p[:, None] - (mu_i_p / l_i_p)[:, None] * acc_p
        t_yp_out = t_p_v + p_tv_acc_p / l_i_p[:, None]
        tl.store(T_Out_p_block_ptr, t_yp_out.to(T_Out_p.dtype.element_ty), boundary_check=(0,))