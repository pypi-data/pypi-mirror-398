
import math
import torch
import triton

import argparse

from utils import get_ebt_attention_fwd_flops, get_ebt_attention_bwd_flops
from config import benchmark_configs

from ebt_flash_attention.ebt_attention import ebt_attention
from pytorch_ebt_attention import pytorch_ebt_attention, SDPA_ebt_attention

torch.set_float32_matmul_precision('medium')

MASK_CONST = -1e9

def parse_args():
    parser = argparse.ArgumentParser(description="EBT Attention Benchmark")

    parser.add_argument("--causal", action="store_true", help="Enable causal attention.")
    parser.add_argument("--mask_type", type=str, default="boolean", choices=["boolean", "additive", "none"], help="Mask type used for attention.")
    parser.add_argument("--dtype", type=str, default="float32", choices=["float32", "float16", "bfloat16"], help="Data type for queries/keys/values.")

    return parser.parse_args()


@triton.testing.perf_report(benchmark_configs)
def bench_attention_comparison(BATCH, H, seqlen, HEAD_DIM, mode, provider, dtype=torch.float32):

    device = torch.device("cuda")

    q_o = torch.randn((BATCH, H, seqlen, HEAD_DIM), dtype=dtype, device=device, requires_grad=True)
    k_o = torch.randn((BATCH, H, seqlen, HEAD_DIM), dtype=dtype, device=device, requires_grad=True)
    v_o = torch.randn((BATCH, H, seqlen, HEAD_DIM), dtype=dtype, device=device, requires_grad=True)
    q_p = torch.randn((BATCH, H, seqlen, HEAD_DIM), dtype=dtype, device=device, requires_grad=True)
    k_p = torch.randn((BATCH, H, seqlen, HEAD_DIM), dtype=dtype, device=device, requires_grad=True)
    v_p = torch.randn((BATCH, H, seqlen, HEAD_DIM), dtype=dtype, device=device, requires_grad=True)
    sm_scale = 1.0 / math.sqrt(HEAD_DIM)

    # Create attention mask
    if MASK_TYPE == "boolean":
        attn_mask = torch.randn((seqlen + 1, seqlen + 1), device=device)
        attn_mask = attn_mask >= 0.0
    elif MASK_TYPE == "additive":
        attn_mask = torch.randn((seqlen + 1, seqlen + 1), device=device)
        attn_mask = torch.where(attn_mask >= 0.0, 0.0, MASK_CONST)
    else:
        attn_mask = None

    if CAUSAL and attn_mask is not None:
        causal_mask = torch.tril(torch.ones((seqlen + 1, seqlen + 1), device=device)).bool()
        if MASK_TYPE == "boolean":
            attn_mask.fill_diagonal_(True)
            attn_mask = attn_mask & causal_mask
        elif MASK_TYPE == "additive":
            attn_mask.fill_diagonal_(0.0)
            attn_mask = attn_mask + torch.where(causal_mask, 0.0, MASK_CONST)

    def forward_backward_triton():
        out_o, out_p = ebt_attention(q_o, k_o, v_o, q_p, k_p, v_p, sm_scale=sm_scale,attn_mask=attn_mask, causal=CAUSAL)
        loss = out_o.sum() + out_p.sum()
        loss.backward()
        torch.cuda.synchronize()
        # Reset gradients for next iteration
        q_o.grad = None
        k_o.grad = None
        v_o.grad = None
        q_p.grad = None
        k_p.grad = None
        v_p.grad = None

    def forward_backward_torch():
        out_o, out_p = pytorch_ebt_attention(q_o, k_o, v_o, q_p, k_p, v_p, sm_scale=sm_scale, attn_mask=attn_mask)
        loss = out_o.sum() + out_p.sum()
        loss.backward()
        torch.cuda.synchronize()
        # Reset gradients for next iteration
        q_o.grad = None
        k_o.grad = None
        v_o.grad = None
        q_p.grad = None
        k_p.grad = None
        v_p.grad = None

    def forward_backward_SDPA():
        out_o, out_p = SDPA_ebt_attention(q_o, k_o, v_o, q_p, k_p, v_p, sm_scale=sm_scale, attn_mask=attn_mask)
        loss = out_o.sum() + out_p.sum()
        loss.backward()
        torch.cuda.synchronize()
        # Reset gradients for next iteration
        q_o.grad = None
        k_o.grad = None
        v_o.grad = None
        q_p.grad = None
        k_p.grad = None
        v_p.grad = None

    if mode == "fwd":
        if provider == "triton-ebt-attn":
            fn = lambda: ebt_attention(q_o, k_o, v_o, q_p, k_p, v_p, sm_scale=sm_scale, attn_mask=attn_mask)
        elif provider == "torch-ebt-attn":
            fn = lambda: pytorch_ebt_attention(q_o, k_o, v_o, q_p, k_p, v_p, sm_scale=sm_scale, attn_mask=attn_mask)
        elif provider == "sdpa-ebt-attn":
            fn = lambda: SDPA_ebt_attention(q_o, k_o, v_o, q_p, k_p, v_p, sm_scale=sm_scale, attn_mask=attn_mask)
        else:
            raise Exception("Invalid provider \"{}\"".format(provider))
    elif mode == "bwd":
        if provider == "triton-ebt-attn":
            fn = forward_backward_triton
        elif provider == "torch-ebt-attn":
            fn = forward_backward_torch
        elif provider == "sdpa-ebt-attn":
            fn = forward_backward_SDPA
        else:
            raise Exception("Invalid provider \"{}\"".format(provider))
    else:
        raise Exception("Invalid mode \"{}\"".format(mode))

    # Run benchmark
    ms = triton.testing.do_bench(fn)

    # Calculate FLOPS
    if mode == "fwd":
        total_flops = get_ebt_attention_fwd_flops(BATCH, H, seqlen, HEAD_DIM)
    else:  # mode == "bwd"
        total_flops = get_ebt_attention_bwd_flops(BATCH, H, seqlen, HEAD_DIM)

    # Calculate TFLOPS
    tflops = total_flops * 1e-12 / (ms * 1e-3)

    # Return TFLOPS for plotting
    return tflops


if __name__ == "__main__":
    args = parse_args()

    CAUSAL = args.causal
    MASK_TYPE = args.mask_type
    DTYPE = getattr(torch, args.dtype)

    print("\nRunning performance benchmarks...")
    print("-" * 50)
    df = bench_attention_comparison.run(save_path=f"benchmark/attn/DTYPE={args.dtype}_CAUSAL={args.causal}_MASK_TYPE={args.mask_type}_results", print_data=True, return_df=True)