import argparse

import math
import torch
import torch.autograd.forward_ad as fwAD
from torch.func import jvp

from pytorch_ebt_attention import pytorch_ebt_attention
from ebt_flash_attention.ebt_attention import EBTAttn, ebt_attention

MASK_CONST = -1e9


def parse_args():
    parser = argparse.ArgumentParser(description="Run EBT attention tests.")

    parser.add_argument("--dtype", type=str, default="float32", choices=["float32", "float16", "bfloat16"], help="Data type to use for tests.")
    parser.add_argument("--mask_type", type=str, default="boolean", choices=["boolean", "additive", "none"], help="Attention mask type.")
    parser.add_argument("--causal", action="store_true", help="Enable causal masking.")
    parser.add_argument("--use_causal_flash", action="store_true", help="Use causal Flash-Attention if available.")

    parser.add_argument("--batch_size", type=int, default=16)
    parser.add_argument("--n_heads", type=int, default=8)
    parser.add_argument("--seqlen", type=int, default=128)
    parser.add_argument("--head_dim", type=int, default=32)

    return parser.parse_args()


def test_ebt_forward_correctness(
    batch_size=2,
    n_heads=4,
    seqlen=128,
    head_dim=64,
    mask_type="none",
    causal=False,
    use_causal_flash=False,
    dtype=torch.float32,
    atol=1e-2,
    rtol=1e-2,
):
    """Test forward pass correctness."""
    print(f"\n{'='*50}")
    print(f"Testing Forward:")
    print('='*50)
    
    device = torch.device('cuda')
    torch.manual_seed(42)
    
    # Create random inputs [B, N, S, H]
    q_o = torch.randn(batch_size, n_heads, seqlen, head_dim, dtype=dtype, device=device)
    q_p = torch.randn(batch_size, n_heads, seqlen, head_dim, dtype=dtype, device=device)
    k_o = torch.randn(batch_size, n_heads, seqlen, head_dim, dtype=dtype, device=device)
    k_p = torch.randn(batch_size, n_heads, seqlen, head_dim, dtype=dtype, device=device)
    v_o = torch.randn(batch_size, n_heads, seqlen, head_dim, dtype=dtype, device=device)
    v_p = torch.randn(batch_size, n_heads, seqlen, head_dim, dtype=dtype, device=device)
    
    sm_scale = 1.0 / math.sqrt(head_dim)

    # Create attention mask
    if mask_type == "boolean":
        attn_mask = torch.randn((seqlen + 1, seqlen + 1), device=device)
        attn_mask = attn_mask >= 0.0
    elif mask_type == "additive":
        attn_mask = torch.randn((seqlen + 1, seqlen + 1), device=device)
        attn_mask = torch.where(attn_mask >= 0.0, 0.0, MASK_CONST)
    else:
        attn_mask = None

    if causal and attn_mask is not None:
        causal_mask = torch.tril(torch.ones((seqlen + 1, seqlen + 1), device=device)).bool()
        if mask_type == "boolean":
            attn_mask.fill_diagonal_(True)
            attn_mask = attn_mask & causal_mask
        elif mask_type == "additive":
            attn_mask.fill_diagonal_(0.0)
            attn_mask = attn_mask + torch.where(causal_mask, 0.0, MASK_CONST)
    
    # PyTorch reference
    ref_out_o, ref_out_p = pytorch_ebt_attention(
        q_o, k_o, v_o, q_p, k_p, v_p, sm_scale=sm_scale, attn_mask=attn_mask,
    )
    

    # Triton kernel
    tri_out_o, tri_out_p = ebt_attention(
        q_o, k_o, v_o, q_p, k_p, v_p, sm_scale=sm_scale, attn_mask=attn_mask, causal=(causal and use_causal_flash),
    )
    
    # Compare outputs
    diff_o = (ref_out_o - tri_out_o).abs()
    diff_p = (ref_out_p - tri_out_p).abs()
    
    max_diff_o = diff_o.max().item()
    max_diff_p = diff_p.max().item()
    mean_diff_o = diff_o.mean().item()
    mean_diff_p = diff_p.mean().item()
    
    print(f"\nOriginal stream (out_o):")
    print(f"  Max diff:  {max_diff_o:.6e}")
    print(f"  Mean diff: {mean_diff_o:.6e}")
    
    print(f"\nPredicted stream (out_p):")
    print(f"  Max diff:  {max_diff_p:.6e}")
    print(f"  Mean diff: {mean_diff_p:.6e}")
    
    # Check correctness
    correct_o = torch.allclose(ref_out_o, tri_out_o, atol=atol, rtol=rtol)
    correct_p = torch.allclose(ref_out_p, tri_out_p, atol=atol, rtol=rtol) 
    
    return correct_o and correct_p


def test_ebt_backward_correctness(
    batch_size=2,
    n_heads=4,
    seqlen=128,
    head_dim=64,
    mask_type="none",
    causal=False,
    use_causal_flash=False,
    dtype=torch.float32,
    atol=1e-2,
    rtol=1e-2,
):
    """Test backward pass correctness."""
    print(f"\n{'='*50}")
    print(f"Testing Backward:")
    print('='*50)
    
    device = torch.device('cuda')
    torch.manual_seed(42)
    
    data_q_o = torch.randn(batch_size, n_heads, seqlen, head_dim, dtype=dtype, device=device)
    data_k_o = torch.randn(batch_size, n_heads, seqlen, head_dim, dtype=dtype, device=device)
    data_v_o = torch.randn(batch_size, n_heads, seqlen, head_dim, dtype=dtype, device=device)
    data_q_p = torch.randn(batch_size, n_heads, seqlen, head_dim, dtype=dtype, device=device)
    data_k_p = torch.randn(batch_size, n_heads, seqlen, head_dim, dtype=dtype, device=device)
    data_v_p = torch.randn(batch_size, n_heads, seqlen, head_dim, dtype=dtype, device=device)
    
    # Upstream gradients (dy)
    do_o = torch.randn_like(data_q_o)
    do_p = torch.randn_like(data_q_p)
    
    sm_scale = 1.0 / math.sqrt(head_dim)

    # Create attention mask
    if mask_type == "boolean":
        attn_mask = torch.randn((seqlen + 1, seqlen + 1), device=device)
        attn_mask = attn_mask >= 0.0
    elif mask_type == "additive":
        attn_mask = torch.randn((seqlen + 1, seqlen + 1), device=device)
        attn_mask = torch.where(attn_mask >= 0.0, 0.0, MASK_CONST)
    else:
        attn_mask = None

    if causal and attn_mask is not None:
        causal_mask = torch.tril(torch.ones((seqlen + 1, seqlen + 1), device=device)).bool()
        if mask_type == "boolean":
            attn_mask.fill_diagonal_(True)
            attn_mask = attn_mask & causal_mask
        elif mask_type == "additive":
            attn_mask.fill_diagonal_(0.0)
            attn_mask = attn_mask + torch.where(causal_mask, 0.0, MASK_CONST)

    # Reference Backward
    ref_q_o = data_q_o.clone().detach().requires_grad_(True)
    ref_k_o = data_k_o.clone().detach().requires_grad_(True)
    ref_v_o = data_v_o.clone().detach().requires_grad_(True)
    ref_q_p = data_q_p.clone().detach().requires_grad_(True)
    ref_k_p = data_k_p.clone().detach().requires_grad_(True)
    ref_v_p = data_v_p.clone().detach().requires_grad_(True)
    
    ref_out_o, ref_out_p = pytorch_ebt_attention(
        ref_q_o, ref_k_o, ref_v_o, ref_q_p, ref_k_p, ref_v_p, sm_scale=sm_scale, attn_mask=attn_mask,
    )
    
    ref_loss = (ref_out_o * do_o).sum() + (ref_out_p * do_p).sum()
    ref_loss.backward()
    
    # Triton Backward
    tri_q_o = data_q_o.clone().detach().requires_grad_(True)
    tri_k_o = data_k_o.clone().detach().requires_grad_(True)
    tri_v_o = data_v_o.clone().detach().requires_grad_(True)
    tri_q_p = data_q_p.clone().detach().requires_grad_(True)
    tri_k_p = data_k_p.clone().detach().requires_grad_(True)
    tri_v_p = data_v_p.clone().detach().requires_grad_(True)
    

    tri_out_o, tri_out_p = ebt_attention(
        tri_q_o, tri_k_o, tri_v_o, tri_q_p, tri_k_p, tri_v_p, sm_scale=sm_scale, attn_mask=attn_mask, causal=(causal and use_causal_flash),
    )
    
    tri_loss = (tri_out_o * do_o).sum() + (tri_out_p * do_p).sum()
    tri_loss.backward()

    grads = {
        "dQ_o": (ref_q_o.grad, tri_q_o.grad),
        "dK_o": (ref_k_o.grad, tri_k_o.grad),
        "dV_o": (ref_v_o.grad, tri_v_o.grad),
        "dQ_p": (ref_q_p.grad, tri_q_p.grad),
        "dK_p": (ref_k_p.grad, tri_k_p.grad),
        "dV_p": (ref_v_p.grad, tri_v_p.grad),
    }
    
    results = {}
    passed = True
    
    for name, (ref_g, tri_g) in grads.items():
        if tri_g is None:
            print(f"{name}: Gradient is None! (Check requires_grad or backward graph)")
            passed = False
            continue
            
        diff = (ref_g - tri_g).abs()
        max_diff = diff.max().item()
        mean_diff = diff.mean().item()
        
        is_close = torch.allclose(ref_g, tri_g, atol=atol, rtol=rtol)
        results[name] = (max_diff, mean_diff, is_close)
        
        if not is_close:
            passed = False
            
        print(f"{name}:")
        print(f"  Max diff:  {max_diff:.6e}")
        print(f"  Mean diff: {mean_diff:.6e}")
    
    return passed


def test_ebt_jvp_correctness(
    batch_size=2,
    n_heads=4,
    seqlen=128,
    head_dim=64,
    mask_type="none",
    causal=False,
    use_causal_flash=False,
    dtype=torch.float32,
    atol=1e-2,
    rtol=1e-2,
):
    """Test JVP correctness."""
    print(f"\n{'='*50}")
    print(f"Testing JVP:")
    print('='*50)
    device = torch.device('cuda')
    torch.manual_seed(42)
    
    # Create Primals
    q_o = torch.randn(batch_size, n_heads, seqlen, head_dim, dtype=dtype, device=device)
    k_o = torch.randn(batch_size, n_heads, seqlen, head_dim, dtype=dtype, device=device)
    v_o = torch.randn(batch_size, n_heads, seqlen, head_dim, dtype=dtype, device=device)
    q_p = torch.randn(batch_size, n_heads, seqlen, head_dim, dtype=dtype, device=device)
    k_p = torch.randn(batch_size, n_heads, seqlen, head_dim, dtype=dtype, device=device)
    v_p = torch.randn(batch_size, n_heads, seqlen, head_dim, dtype=dtype, device=device)
    # Create Tangents (Perturbations)
    t_q_o = torch.randn_like(q_o)
    t_k_o = torch.randn_like(k_o)
    t_v_o = torch.randn_like(v_o)
    t_q_p = torch.randn_like(q_p)
    t_k_p = torch.randn_like(k_p)
    t_v_p = torch.randn_like(v_p)

    sm_scale = 1.0 / math.sqrt(head_dim)
    
    # Create attention mask
    if mask_type == "boolean":
        attn_mask = torch.randn((seqlen + 1, seqlen + 1), device=device)
        attn_mask = attn_mask >= 0.0
    elif mask_type == "additive":
        attn_mask = torch.randn((seqlen + 1, seqlen + 1), device=device)
        attn_mask = torch.where(attn_mask >= 0.0, 0.0, MASK_CONST)
    else:
        attn_mask = None

    if causal and attn_mask is not None:
        causal_mask = torch.tril(torch.ones((seqlen + 1, seqlen + 1), device=device)).bool()
        if mask_type == "boolean":
            attn_mask.fill_diagonal_(True)
            attn_mask = attn_mask & causal_mask
        elif mask_type == "additive":
            attn_mask.fill_diagonal_(0.0)
            attn_mask = attn_mask + torch.where(causal_mask, 0.0, MASK_CONST)

    
    # Wrapper for torch.func to handle static args
    def ref_func(qo, ko, vo, qp, kp, vp):
        return pytorch_ebt_attention(
            qo, ko, vo, qp, kp, vp,
            sm_scale=sm_scale, attn_mask=attn_mask
        )
    
    primals = (q_o, k_o, v_o, q_p, k_p, v_p)
    tangents = (t_q_o, t_k_o, t_v_o, t_q_p, t_k_p, t_v_p)
    
    # Get Ground Truth Primal Outputs and Tangent Outputs
    (ref_out_o, ref_out_p), (ref_t_o, ref_t_p) = jvp(ref_func, primals, tangents)

    with fwAD.dual_level():
        # Pack primals and tangents into Dual Tensors
        dual_q_o = fwAD.make_dual(q_o, t_q_o)
        dual_k_o = fwAD.make_dual(k_o, t_k_o)
        dual_v_o = fwAD.make_dual(v_o, t_v_o)
        dual_q_p = fwAD.make_dual(q_p, t_q_p)
        dual_k_p = fwAD.make_dual(k_p, t_k_p)
        dual_v_p = fwAD.make_dual(v_p, t_v_p)
        
        # Call the static method designed for duals
        tri_dual_out_o, tri_dual_out_p = EBTAttn.fwd_dual(
            dual_q_o, dual_k_o, dual_v_o,
            dual_q_p, dual_k_p, dual_v_p,
            sm_scale=sm_scale,
            attn_mask=attn_mask,
            causal=(causal and use_causal_flash),
        )
        
        # Unpack the results back into primals and tangents
        tri_out_o = fwAD.unpack_dual(tri_dual_out_o).primal
        tri_t_o   = fwAD.unpack_dual(tri_dual_out_o).tangent
        tri_out_p = fwAD.unpack_dual(tri_dual_out_p).primal
        tri_t_p   = fwAD.unpack_dual(tri_dual_out_p).tangent

    # Compare Primals (Sanity Check)
    diff_o = (ref_out_o - tri_out_o).abs().max().item()
    diff_p = (ref_out_p - tri_out_p).abs().max().item()
    
    # Compare Tangents (JVP Check)
    diff_t_o = (ref_t_o - tri_t_o).abs()
    diff_t_p = (ref_t_p - tri_t_p).abs()
    
    max_diff_t_o = diff_t_o.max().item()
    max_diff_t_p = diff_t_p.max().item()
    
    print(f"Tangent O Max Diff: {max_diff_t_o:.6e}")
    print(f"Tangent P Max Diff: {max_diff_t_p:.6e}")

    passed_o = torch.allclose(ref_t_o, tri_t_o, atol=atol, rtol=rtol)
    passed_p = torch.allclose(ref_t_p, tri_t_p,  atol=atol, rtol=rtol)

    return passed_o and passed_p


def run_checks(
    batch_size=2,
    n_heads=4,
    seqlen=128,
    head_dim=64,
    mask_type="none",
    causal=False,
    use_causal_flash=False,
    dtype=torch.float32,
    atol=None,
    rtol=None,
):
    """Run forward, backward, and JVP tests with a shared config."""

    # Default tolerances
    if atol is None:
        atol = 1e-2 if dtype == torch.float32 else 3e-2
    if rtol is None:
        rtol = 1e-2 if dtype == torch.float32 else 3e-2

    print("\n============== RUNNING ALL EBT TESTS ==============\n")
    print(f"Config:")
    print(f"  batch_size={batch_size}")
    print(f"  n_heads={n_heads}")
    print(f"  seqlen={seqlen}")
    print(f"  head_dim={head_dim}")
    print(f"  mask_type={mask_type}")
    print(f"  causal={causal}")
    print(f"  use_causal_flash={use_causal_flash}")
    print(f"  dtype={dtype}")
    print(f"  atol={atol}, rtol={rtol}")
    print("\n" + "="*50 + "\n")

    # Run tests
    fwd_ok = test_ebt_forward_correctness(
        batch_size=batch_size,
        n_heads=n_heads,
        seqlen=seqlen,
        head_dim=head_dim,
        mask_type=mask_type,
        causal=causal,
        use_causal_flash=use_causal_flash,
        dtype=dtype,
        atol=atol,
        rtol=rtol,
    )

    bwd_ok = test_ebt_backward_correctness(
        batch_size=batch_size,
        n_heads=n_heads,
        seqlen=seqlen,
        head_dim=head_dim,
        mask_type=mask_type,
        causal=causal,
        use_causal_flash=use_causal_flash,
        dtype=dtype,
        atol=atol,
        rtol=rtol,
    )

    jvp_ok = test_ebt_jvp_correctness(
        batch_size=batch_size,
        n_heads=n_heads,
        seqlen=seqlen,
        head_dim=head_dim,
        mask_type=mask_type,
        causal=causal,
        use_causal_flash=use_causal_flash,
        dtype=dtype,
        atol=atol,
        rtol=rtol,
    )

    # Summary
    print("\n==================== SUMMARY ====================")
    print(f"Forward : {'PASS' if fwd_ok else 'FAIL'}")
    print(f"Backward: {'PASS' if bwd_ok else 'FAIL'}")
    print(f"JVP     : {'PASS' if jvp_ok else 'FAIL'}")

    all_ok = fwd_ok and bwd_ok and jvp_ok
    print(f"\nOverall : {'ALL TESTS PASSED' if all_ok else 'SOME TESTS FAILED'}")
    print("="*50 + "\n")

    return all_ok



if __name__ == "__main__":
    args = parse_args()

    run_checks(
        batch_size=args.batch_size,
        n_heads=args.n_heads,
        seqlen=args.seqlen,
        head_dim=args.head_dim,
        mask_type=args.mask_type,
        causal=args.causal,
        use_causal_flash=args.use_causal_flash,
        dtype=getattr(torch, args.dtype),
    )