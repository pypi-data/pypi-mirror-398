import triton

# Benchmarking configuration
BATCH, N_HEADS, HEAD_DIM = 8, 8, 32

benchmark_configs = [
    triton.testing.Benchmark(
        x_names=["seqlen"],
        x_vals=[64, 128, 256, 512, 1024, 2048, 4096],
        line_arg="provider",
        line_vals=[
            "triton-ebt-attn",
            "torch-ebt-attn",
            "sdpa-ebt-attn",
        ],
        line_names=[
            "Triton-EBT-Attn (TFLOPS)",
            "PyTorch-EBT-Attn (TFLOPS)",
            "SDPA-EBT-Attn (TFLOPS)",
        ],
        styles=[
            ("red", "-"),
            ("blue", "--"),
            ("cyan", "-."),
        ],
        ylabel="TFLOPS",
        plot_name=f"EBT-attention-TFLOPS-comparison-batch{BATCH}-head{N_HEADS}-d{HEAD_DIM}-{mode}",
        args={
            "BATCH": BATCH,
            "H": N_HEADS,
            "HEAD_DIM": HEAD_DIM,
            "mode": mode,
        }
    )
    for mode in ["fwd", "bwd"]
]