import triton
import triton.language as tl

def get_bwd_configs():
    return [
        triton.Config({'BLOCK_M': 128, 'BLOCK_N': 128}, num_warps=8, num_stages=1),
        triton.Config({'BLOCK_M': 128, 'BLOCK_N': 64}, num_warps=8, num_stages=1),
        triton.Config({'BLOCK_M': 64, 'BLOCK_N': 128}, num_warps=8, num_stages=1),
        triton.Config({'BLOCK_M': 64, 'BLOCK_N': 64}, num_warps=4, num_stages=1),
        triton.Config({'BLOCK_M': 32, 'BLOCK_N': 32}, num_warps=4, num_stages=1),
    ]

def get_superdiag_configs():
    return [
        triton.Config({'BLOCK_M': 128}, num_warps=4, num_stages=1),
        triton.Config({'BLOCK_M': 64}, num_warps=4, num_stages=1),
        triton.Config({'BLOCK_M': 32}, num_warps=2, num_stages=1),
    ]

@triton.autotune(
    configs=get_bwd_configs(),
    key=['HEAD_DIM', 'N_CTX', 'STAGE'],
)
@triton.jit
def _ebt_attn_bwd_dkdv(
    Q_o, Q_p, K_o, V_o, 
    DO_o, DO_p, Out_o, Out_p,
    M_o, M_p,
    Mask_o, Mask_p,
    DK_o, DV_o,
    sm_scale,
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
    MASK_TYPE: tl.constexpr,
    MASK_CONST: tl.constexpr = -1e9,
):
    start_n = tl.program_id(0)
    off_hz = tl.program_id(1)
    off_z = off_hz // H
    off_h = off_hz % H
    
    qk_scale = sm_scale * 1.4426950408889634  # 1/log(2)
    
    offs_n = start_n * BLOCK_N + tl.arange(0, BLOCK_N)
    offs_d = tl.arange(0, HEAD_DIM)
    
    q_offset = off_z * stride_qz + off_h * stride_qh
    k_offset = off_z * stride_kz + off_h * stride_kh
    v_offset = off_z * stride_vz + off_h * stride_vh
    o_offset = off_z * stride_oz + off_h * stride_oh
    
    k_o_ptrs = K_o + k_offset + (offs_n[:, None] * stride_kn + offs_d[None, :] * stride_kk)
    v_o_ptrs = V_o + v_offset + (offs_n[:, None] * stride_vn + offs_d[None, :] * stride_vk)
    
    k_o = tl.load(k_o_ptrs, mask=offs_n[:, None] < N_CTX, other=0.0)
    v_o = tl.load(v_o_ptrs, mask=offs_n[:, None] < N_CTX, other=0.0)
    
    # Initialize accumulators
    dk_o = tl.zeros([BLOCK_N, HEAD_DIM], dtype=tl.float32)
    dv_o = tl.zeros([BLOCK_N, HEAD_DIM], dtype=tl.float32)
    
    # O stream backward
    if STAGE == 1:
        lo_oo, hi_oo = 0, N_CTX
    elif STAGE == 2:
        lo_oo = start_n * BLOCK_N
        hi_oo = min(lo_oo + BLOCK_M, N_CTX)
    else:  # STAGE == 3 (Causal)
        lo_oo = start_n * BLOCK_N
        hi_oo = N_CTX
    
    for start_m in range(lo_oo, hi_oo, BLOCK_M):
        offs_m = start_m + tl.arange(0, BLOCK_M)
        
        q_o_ptrs = Q_o + q_offset + (offs_m[:, None] * stride_qm + offs_d[None, :] * stride_qk)
        q_o = tl.load(q_o_ptrs, mask=offs_m[:, None] < N_CTX, other=0.0)
        
        do_o_ptrs = DO_o + o_offset + (offs_m[:, None] * stride_om + offs_d[None, :] * stride_ok)
        do_o = tl.load(do_o_ptrs, mask=offs_m[:, None] < N_CTX, other=0.0)
        
        out_o_ptrs = Out_o + o_offset + (offs_m[:, None] * stride_om + offs_d[None, :] * stride_ok)
        out_o = tl.load(out_o_ptrs, mask=offs_m[:, None] < N_CTX, other=0.0)
        delta = tl.sum(out_o * do_o, axis=1)
        
        m = tl.load(M_o + off_hz * N_CTX + offs_m, mask=offs_m < N_CTX, other=0.0)
        
        qk = tl.dot(q_o, tl.trans(k_o))
        
        # Build combined mask
        if STAGE > 1:
            combined_mask = offs_m[:, None] >= offs_n[None, :]
        else:
            combined_mask = tl.full((BLOCK_M, BLOCK_N), 1, dtype=tl.int1)
        
        # Apply attention mask
        if MASK_TYPE > 0:
            mask_ptrs = Mask_o + (offs_m[:, None] * stride_mom + offs_n[None, :] * stride_mon)
            if MASK_TYPE == 1:  # Boolean mask
                mask_val = tl.load(
                    mask_ptrs,
                    mask=(offs_m[:, None] < N_CTX) & (offs_n[None, :] < N_CTX),
                    other=1
                )
                combined_mask = combined_mask & (mask_val == 1)
                qk = tl.where(combined_mask, qk * qk_scale, MASK_CONST)
            else:  # Additive mask
                mask_val = tl.load(
                    mask_ptrs,
                    mask=(offs_m[:, None] < N_CTX) & (offs_n[None, :] < N_CTX),
                    other=MASK_CONST
                )
                qk = qk * qk_scale + mask_val
                if STAGE > 1:
                    qk = tl.where(combined_mask, qk, MASK_CONST)
        else:
            if STAGE > 1:
                qk = tl.where(combined_mask, qk * qk_scale, MASK_CONST)
            else:
                qk = qk * qk_scale
        
        # Softmax backward
        p = tl.math.exp2(qk - m[:, None])
        if MASK_TYPE != 2 or STAGE > 1:
            p = tl.where(combined_mask, p, 0.0)
        
        # dP = dO @ V^T, dS = P * (dP - delta) * sm_scale
        dp = tl.dot(do_o, tl.trans(v_o))
        ds = p * (dp - delta[:, None]) * sm_scale
        
        if MASK_TYPE != 2 or STAGE > 1:
            ds = tl.where(combined_mask, ds, 0.0)
        
        # Accumulate gradients
        dk_o += tl.dot(tl.trans(ds.to(q_o.dtype)), q_o)
        dv_o += tl.dot(tl.trans(p.to(do_o.dtype)), do_o)
    
    # P stream backward
    if STAGE == 1:
        lo_po, hi_po = 0, N_CTX
    elif STAGE == 2:
        lo_po = start_n * BLOCK_N
        hi_po = min(lo_po + BLOCK_M, N_CTX)
    else:  # STAGE == 3
        lo_po = start_n * BLOCK_N
        hi_po = N_CTX
    
    for start_m in range(lo_po, hi_po, BLOCK_M):
        offs_m = start_m + tl.arange(0, BLOCK_M)
        
        q_p_ptrs = Q_p + q_offset + (offs_m[:, None] * stride_qm + offs_d[None, :] * stride_qk)
        q_p = tl.load(q_p_ptrs, mask=offs_m[:, None] < N_CTX, other=0.0)
        
        do_p_ptrs = DO_p + o_offset + (offs_m[:, None] * stride_om + offs_d[None, :] * stride_ok)
        do_p = tl.load(do_p_ptrs, mask=offs_m[:, None] < N_CTX, other=0.0)
        
        out_p_ptrs = Out_p + o_offset + (offs_m[:, None] * stride_om + offs_d[None, :] * stride_ok)
        out_p = tl.load(out_p_ptrs, mask=offs_m[:, None] < N_CTX, other=0.0)
        delta = tl.sum(out_p * do_p, axis=1)
        
        m = tl.load(M_p + off_hz * N_CTX + offs_m, mask=offs_m < N_CTX, other=0.0)
        
        qk = tl.dot(q_p, tl.trans(k_o))
        
        # Build mask: causal + superdiagonal exclusion
        if STAGE > 1:
            combined_mask = offs_m[:, None] >= offs_n[None, :]
        else:
            combined_mask = tl.full((BLOCK_M, BLOCK_N), 1, dtype=tl.int1)
        
        # Exclude superdiagonal: position (i, i+1) is handled separately
        superdiag_mask = offs_m[:, None] != (offs_n[None, :] - 1)
        combined_mask = combined_mask & superdiag_mask
        
        if MASK_TYPE > 0:
            mask_ptrs = Mask_p + (offs_m[:, None] * stride_mpm + offs_n[None, :] * stride_mpn)
            if MASK_TYPE == 1:
                mask_val = tl.load(
                    mask_ptrs,
                    mask=(offs_m[:, None] < N_CTX) & (offs_n[None, :] < N_CTX),
                    other=1
                )
                combined_mask = combined_mask & (mask_val == 1)
                qk = tl.where(combined_mask, qk * qk_scale, MASK_CONST)
            else:
                mask_val = tl.load(
                    mask_ptrs,
                    mask=(offs_m[:, None] < N_CTX) & (offs_n[None, :] < N_CTX),
                    other=MASK_CONST
                )
                qk = qk * qk_scale + mask_val
                qk = tl.where(combined_mask, qk, MASK_CONST)
        else:
            qk = tl.where(combined_mask, qk * qk_scale, MASK_CONST)
        
        p = tl.math.exp2(qk - m[:, None])
        p = tl.where(combined_mask, p, 0.0)
        
        dp = tl.dot(do_p, tl.trans(v_o))
        ds = p * (dp - delta[:, None]) * sm_scale
        ds = tl.where(combined_mask, ds, 0.0)
        
        dk_o += tl.dot(tl.trans(ds.to(q_p.dtype)), q_p)
        dv_o += tl.dot(tl.trans(p.to(do_p.dtype)), do_p)
    
    dk_o_ptrs = DK_o + k_offset + (offs_n[:, None] * stride_kn + offs_d[None, :] * stride_kk)
    dv_o_ptrs = DV_o + v_offset + (offs_n[:, None] * stride_vn + offs_d[None, :] * stride_vk)
    
    tl.store(dk_o_ptrs, dk_o.to(DK_o.dtype.element_ty), mask=offs_n[:, None] < N_CTX)
    tl.store(dv_o_ptrs, dv_o.to(DV_o.dtype.element_ty), mask=offs_n[:, None] < N_CTX)


@triton.autotune(
    configs=get_superdiag_configs(),
    key=['HEAD_DIM', 'N_CTX'],
)
@triton.jit
def _ebt_attn_bwd_dkdv_superdiag(
    Q_p, K_p, V_p, DO_p, Out_p,
    M_p, Mask_p,
    DK_p, DV_p,
    sm_scale,
    stride_qz, stride_qh, stride_qm, stride_qk,
    stride_kz, stride_kh, stride_kn, stride_kk,
    stride_vz, stride_vh, stride_vn, stride_vk,
    stride_oz, stride_oh, stride_om, stride_ok,
    stride_mpm, stride_mpn,
    Z, H, N_CTX,
    HEAD_DIM: tl.constexpr,
    BLOCK_M: tl.constexpr,
    MASK_TYPE: tl.constexpr,
    MASK_CONST: tl.constexpr = -1e9,
):
    start_m = tl.program_id(0)
    off_hz = tl.program_id(1)
    off_z = off_hz // H
    off_h = off_hz % H
    
    qk_scale = sm_scale * 1.4426950408889634
    
    offs_m = start_m * BLOCK_M + tl.arange(0, BLOCK_M)
    offs_d = tl.arange(0, HEAD_DIM)
    
    q_offset = off_z * stride_qz + off_h * stride_qh
    k_offset = off_z * stride_kz + off_h * stride_kh
    v_offset = off_z * stride_vz + off_h * stride_vh
    o_offset = off_z * stride_oz + off_h * stride_oh
    
    q_p_ptrs = Q_p + q_offset + (offs_m[:, None] * stride_qm + offs_d[None, :] * stride_qk)
    k_p_ptrs = K_p + k_offset + (offs_m[:, None] * stride_kn + offs_d[None, :] * stride_kk)
    v_p_ptrs = V_p + v_offset + (offs_m[:, None] * stride_vn + offs_d[None, :] * stride_vk)
    do_p_ptrs = DO_p + o_offset + (offs_m[:, None] * stride_om + offs_d[None, :] * stride_ok)
    out_p_ptrs = Out_p + o_offset + (offs_m[:, None] * stride_om + offs_d[None, :] * stride_ok)
    
    q_p = tl.load(q_p_ptrs, mask=offs_m[:, None] < N_CTX, other=0.0)
    k_p = tl.load(k_p_ptrs, mask=offs_m[:, None] < N_CTX, other=0.0)
    v_p = tl.load(v_p_ptrs, mask=offs_m[:, None] < N_CTX, other=0.0)
    do_p = tl.load(do_p_ptrs, mask=offs_m[:, None] < N_CTX, other=0.0)
    out_p = tl.load(out_p_ptrs, mask=offs_m[:, None] < N_CTX, other=0.0)

    delta = tl.sum(out_p * do_p, axis=1)
    m = tl.load(M_p + off_hz * N_CTX + offs_m, mask=offs_m < N_CTX, other=0.0)
    
    # Superdiagonal: q_p[i] @ k_p[i]
    qk_superdiag = tl.sum(q_p * k_p, axis=1) * qk_scale
    
    # Apply mask for superdiagonal position
    if MASK_TYPE > 0:
        target_cols = offs_m + 1
        mask_ptrs = Mask_p + (offs_m[:, None] * stride_mpm + target_cols[:, None] * stride_mpn)
        valid_mask_loc = offs_m[:, None] < N_CTX
        if MASK_TYPE == 1:
            mask_val = tl.load(mask_ptrs, mask=valid_mask_loc, other=1).reshape((BLOCK_M,))
            qk_superdiag = tl.where(mask_val == 1, qk_superdiag, MASK_CONST)
        else:
            mask_val = tl.load(mask_ptrs, mask=valid_mask_loc, other=MASK_CONST).reshape((BLOCK_M,))
            qk_superdiag = qk_superdiag + mask_val
    
    p_superdiag = tl.math.exp2(qk_superdiag - m)
    
    # dP = do @ v^T (but for superdiag, it's element-wise: sum(do_p * v_p, axis=1))
    dp_superdiag = tl.sum(do_p * v_p, axis=1)
    ds_superdiag = p_superdiag * (dp_superdiag - delta) * sm_scale
    
    # dK_p = ds * q_p, dV_p = p * do_p
    dk_p = ds_superdiag[:, None] * q_p
    dv_p = p_superdiag[:, None] * do_p
    
    dk_p_ptrs = DK_p + k_offset + (offs_m[:, None] * stride_kn + offs_d[None, :] * stride_kk)
    dv_p_ptrs = DV_p + v_offset + (offs_m[:, None] * stride_vn + offs_d[None, :] * stride_vk)
    
    tl.store(dk_p_ptrs, dk_p.to(DK_p.dtype.element_ty), mask=offs_m[:, None] < N_CTX)
    tl.store(dv_p_ptrs, dv_p.to(DV_p.dtype.element_ty), mask=offs_m[:, None] < N_CTX)


@triton.autotune(
    configs=get_bwd_configs(),
    key=['HEAD_DIM', 'N_CTX', 'STAGE'],
)
@triton.jit
def _ebt_attn_bwd_dq(
    Q_o, Q_p, K_o, K_p, V_o, V_p,
    DO_o, DO_p, Out_o, Out_p,
    M_o, M_p,
    Mask_o, Mask_p,
    DQ_o, DQ_p,
    sm_scale,
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
    MASK_TYPE: tl.constexpr,
    MASK_CONST: tl.constexpr = -1e9,
):
    start_m = tl.program_id(0)
    off_hz = tl.program_id(1)
    off_z = off_hz // H
    off_h = off_hz % H
    
    qk_scale = sm_scale * 1.4426950408889634
    
    offs_m = start_m * BLOCK_M + tl.arange(0, BLOCK_M)
    offs_d = tl.arange(0, HEAD_DIM)
    
    q_offset = off_z * stride_qz + off_h * stride_qh
    k_offset = off_z * stride_kz + off_h * stride_kh
    v_offset = off_z * stride_vz + off_h * stride_vh
    o_offset = off_z * stride_oz + off_h * stride_oh
    
    # O stream backward
    q_o_ptrs = Q_o + q_offset + (offs_m[:, None] * stride_qm + offs_d[None, :] * stride_qk)
    do_o_ptrs = DO_o + o_offset + (offs_m[:, None] * stride_om + offs_d[None, :] * stride_ok)
    out_o_ptrs = Out_o + o_offset + (offs_m[:, None] * stride_om + offs_d[None, :] * stride_ok)
    
    q_o = tl.load(q_o_ptrs, mask=offs_m[:, None] < N_CTX, other=0.0)
    do_o = tl.load(do_o_ptrs, mask=offs_m[:, None] < N_CTX, other=0.0)
    out_o = tl.load(out_o_ptrs, mask=offs_m[:, None] < N_CTX, other=0.0)
    
    # Inline delta computation
    delta_o = tl.sum(out_o * do_o, axis=1)
    m_o = tl.load(M_o + off_hz * N_CTX + offs_m, mask=offs_m < N_CTX, other=0.0)
    
    dq_o = tl.zeros([BLOCK_M, HEAD_DIM], dtype=tl.float32)
    
    if STAGE == 1:
        hi_oo = N_CTX
    else:
        hi_oo = min((start_m + 1) * BLOCK_M, N_CTX)
    
    for start_n in range(0, hi_oo, BLOCK_N):
        offs_n = start_n + tl.arange(0, BLOCK_N)
        
        k_o_ptrs = K_o + k_offset + (offs_n[:, None] * stride_kn + offs_d[None, :] * stride_kk)
        v_o_ptrs = V_o + v_offset + (offs_n[:, None] * stride_vn + offs_d[None, :] * stride_vk)
        k_o = tl.load(k_o_ptrs, mask=offs_n[:, None] < N_CTX, other=0.0)
        v_o = tl.load(v_o_ptrs, mask=offs_n[:, None] < N_CTX, other=0.0)
        
        qk = tl.dot(q_o, tl.trans(k_o))
        
        if STAGE > 1:
            combined_mask = offs_m[:, None] >= offs_n[None, :]
        else:
            combined_mask = tl.full((BLOCK_M, BLOCK_N), 1, dtype=tl.int1)
        
        if MASK_TYPE > 0:
            mask_ptrs = Mask_o + (offs_m[:, None] * stride_mom + offs_n[None, :] * stride_mon)
            if MASK_TYPE == 1:
                mask_val = tl.load(
                    mask_ptrs,
                    mask=(offs_m[:, None] < N_CTX) & (offs_n[None, :] < N_CTX),
                    other=0
                )
                combined_mask = combined_mask & (mask_val == 1)
                qk = tl.where(combined_mask, qk * qk_scale, MASK_CONST)
            else:
                mask_val = tl.load(
                    mask_ptrs,
                    mask=(offs_m[:, None] < N_CTX) & (offs_n[None, :] < N_CTX),
                    other=MASK_CONST
                )
                qk = qk * qk_scale + mask_val
                if STAGE > 1:
                    qk = tl.where(combined_mask, qk, MASK_CONST)
        else:
            if STAGE > 1:
                qk = tl.where(combined_mask, qk * qk_scale, MASK_CONST)
            else:
                qk = qk * qk_scale
        
        p = tl.math.exp2(qk - m_o[:, None])
        if MASK_TYPE != 2 or STAGE > 1:
            p = tl.where(combined_mask, p, 0.0)
        
        dp = tl.dot(do_o, tl.trans(v_o))
        ds = p * (dp - delta_o[:, None]) * sm_scale
        
        if MASK_TYPE != 2 or STAGE > 1:
            ds = tl.where(combined_mask, ds, 0.0)
        
        dq_o += tl.dot(ds.to(k_o.dtype), k_o)
    
    # P stream backward
    q_p_ptrs = Q_p + q_offset + (offs_m[:, None] * stride_qm + offs_d[None, :] * stride_qk)
    do_p_ptrs = DO_p + o_offset + (offs_m[:, None] * stride_om + offs_d[None, :] * stride_ok)
    out_p_ptrs = Out_p + o_offset + (offs_m[:, None] * stride_om + offs_d[None, :] * stride_ok)
    k_p_ptrs = K_p + k_offset + (offs_m[:, None] * stride_kn + offs_d[None, :] * stride_kk)
    v_p_ptrs = V_p + v_offset + (offs_m[:, None] * stride_vn + offs_d[None, :] * stride_vk)
    
    q_p = tl.load(q_p_ptrs, mask=offs_m[:, None] < N_CTX, other=0.0)
    do_p = tl.load(do_p_ptrs, mask=offs_m[:, None] < N_CTX, other=0.0)
    out_p = tl.load(out_p_ptrs, mask=offs_m[:, None] < N_CTX, other=0.0)
    k_p = tl.load(k_p_ptrs, mask=offs_m[:, None] < N_CTX, other=0.0)
    v_p = tl.load(v_p_ptrs, mask=offs_m[:, None] < N_CTX, other=0.0)
    
    delta_p = tl.sum(out_p * do_p, axis=1)
    m_p = tl.load(M_p + off_hz * N_CTX + offs_m, mask=offs_m < N_CTX, other=0.0)
    
    dq_p = tl.zeros([BLOCK_M, HEAD_DIM], dtype=tl.float32)
    
    if STAGE == 1:
        hi_po = N_CTX
    else:
        hi_po = min((start_m + 1) * BLOCK_M, N_CTX)
    
    for start_n in range(0, hi_po, BLOCK_N):
        offs_n = start_n + tl.arange(0, BLOCK_N)
        
        k_o_ptrs = K_o + k_offset + (offs_n[:, None] * stride_kn + offs_d[None, :] * stride_kk)
        v_o_ptrs = V_o + v_offset + (offs_n[:, None] * stride_vn + offs_d[None, :] * stride_vk)
        k_o = tl.load(k_o_ptrs, mask=offs_n[:, None] < N_CTX, other=0.0)
        v_o = tl.load(v_o_ptrs, mask=offs_n[:, None] < N_CTX, other=0.0)
        
        qk = tl.dot(q_p, tl.trans(k_o))
        
        if STAGE > 1:
            combined_mask = offs_m[:, None] >= offs_n[None, :]
        else:
            combined_mask = tl.full((BLOCK_M, BLOCK_N), 1, dtype=tl.int1)
        
        # Exclude superdiagonal
        superdiag_mask = offs_m[:, None] != (offs_n[None, :] - 1)
        combined_mask = combined_mask & superdiag_mask
        
        if MASK_TYPE > 0:
            mask_ptrs = Mask_p + (offs_m[:, None] * stride_mpm + offs_n[None, :] * stride_mpn)
            if MASK_TYPE == 1:
                mask_val = tl.load(
                    mask_ptrs,
                    mask=(offs_m[:, None] < N_CTX) & (offs_n[None, :] < N_CTX),
                    other=0
                )
                combined_mask = combined_mask & (mask_val == 1)
                qk = tl.where(combined_mask, qk * qk_scale, MASK_CONST)
            else:
                mask_val = tl.load(
                    mask_ptrs,
                    mask=(offs_m[:, None] < N_CTX) & (offs_n[None, :] < N_CTX),
                    other=MASK_CONST
                )
                qk = qk * qk_scale + mask_val
                qk = tl.where(combined_mask, qk, MASK_CONST)
        else:
            qk = tl.where(combined_mask, qk * qk_scale, MASK_CONST)
        
        p = tl.math.exp2(qk - m_p[:, None])
        p = tl.where(combined_mask, p, 0.0)
        
        dp = tl.dot(do_p, tl.trans(v_o))
        ds = p * (dp - delta_p[:, None]) * sm_scale
        ds = tl.where(combined_mask, ds, 0.0)
        
        dq_p += tl.dot(ds.to(k_o.dtype), k_o)
    
    # Superdiagonal backward
    qk_superdiag = tl.sum(q_p * k_p, axis=1) * qk_scale
    
    if MASK_TYPE > 0:
        target_cols = offs_m + 1
        mask_ptrs = Mask_p + (offs_m[:, None] * stride_mpm + target_cols[:, None] * stride_mpn)
        valid_mask_loc = offs_m[:, None] < N_CTX
        if MASK_TYPE == 1:
            mask_val = tl.load(mask_ptrs, mask=valid_mask_loc, other=1).reshape((BLOCK_M,))
            qk_superdiag = tl.where(mask_val == 1, qk_superdiag, MASK_CONST)
        else:
            mask_val = tl.load(mask_ptrs, mask=valid_mask_loc, other=MASK_CONST).reshape((BLOCK_M,))
            qk_superdiag = qk_superdiag + mask_val
    
    p_superdiag = tl.math.exp2(qk_superdiag - m_p)
    dp_superdiag = tl.sum(do_p * v_p, axis=1)
    ds_superdiag = p_superdiag * (dp_superdiag - delta_p) * sm_scale
    dq_p += ds_superdiag[:, None] * k_p
    
    dq_o_ptrs = DQ_o + q_offset + (offs_m[:, None] * stride_qm + offs_d[None, :] * stride_qk)
    dq_p_ptrs = DQ_p + q_offset + (offs_m[:, None] * stride_qm + offs_d[None, :] * stride_qk)
    
    tl.store(dq_o_ptrs, dq_o.to(DQ_o.dtype.element_ty), mask=offs_m[:, None] < N_CTX)
    tl.store(dq_p_ptrs, dq_p.to(DQ_p.dtype.element_ty), mask=offs_m[:, None] < N_CTX)