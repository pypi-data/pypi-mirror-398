import os
import time
import csv
import torch

import argparse

from model.utils import EBTModelArgs
from model.ebt import EBT

# Tolerance for gradient checking
GRADIENT_ATOL = 5e-4

device = torch.device("cuda")

def parse_args():
    parser = argparse.ArgumentParser(
        description="EBT Training Benchmark: Standard vs Flash Attention"
    )

    parser.add_argument("--batch_size", type=int, default=16, help="Training batch size.")
    parser.add_argument("--dtype", type=str, default="float32", choices=["float32", "float16", "bfloat16"], help="Data type for model weights & activations.")
    parser.add_argument("--causal", action="store_true", help="Enable causal attention.")
    parser.add_argument("--mask_type", type=str, default="boolean", choices=["boolean", "additive", "none"], help="Mask type: boolean | additive | none")
    parser.add_argument("--size", type=str, default="base", choices=["small", "base"], help="Model size: small or base")
    parser.add_argument("--n_steps", type=int, default=3, help="Number of MCMC steps.")
    parser.add_argument("--alpha", type=float, default=0.1, help="Step size for the MCMC update.")
    parser.add_argument(
        "--seq_lengths",
        type=int,
        nargs="+",
        default=[32, 64, 128, 256, 512, 1024, 2048],
        help="List of sequence lengths to benchmark (space-separated)."
    )

    return parser.parse_args()


def get_batch(batch_size, seq_len, dim, dtype=torch.float32, device='cuda'):
    x = torch.randn(batch_size, seq_len + 1, dim, dtype=dtype, device=device)
    return x[:, :-1, :], x[:, 1:, :]


def reset_memory():
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()


def get_peak_memory():
    # Returns memory in GB
    return torch.cuda.max_memory_allocated() / (1024 ** 3)


def run_training_step(energy_net, x, p_init, p_target, n_steps, alpha, use_flash_attention, causal, mask_type):
    """
    Executes one full training iteration (MCMC loop + Backward).
    Returns loss and gradients.
    """
    p_current = p_init.clone().detach().requires_grad_(True)
    total_loss = 0.0

    with torch.set_grad_enabled(True):
        for mcmc_step in range(n_steps):
            input = torch.cat((x, p_current), dim=1)
            energy = energy_net(input, mcmc_step, use_flash_attention=use_flash_attention, causal=causal, mask_type=mask_type)
            grad_p = torch.autograd.grad(energy.sum(), p_current, create_graph=True)[0]
            p_current = p_current - alpha * grad_p
            total_loss = total_loss + ((p_current - p_target) ** 2).mean()

    L = total_loss / n_steps
    energy_net.zero_grad()
    L.backward()
    
    return L, energy_net.parameters()


def test_training(
    energy_net,
    x,
    p_init,
    p_target,
    n_steps,
    alpha,
    use_flash_attention=False,
    causal=False,
    mask_type="boolean",
    warmup_iters=0,
    num_runs=3
):
    """
    Run training with multiple iterations and return average metrics.
    Returns None if OOM or other error occurs.
    """
    try:
        energy_net.train()
        
        # Warmup for flash attention (compile Triton kernels)
        if use_flash_attention and warmup_iters > 0:
            for _ in range(warmup_iters):
                run_training_step(energy_net, x, p_init, p_target, n_steps, alpha, use_flash_attention, causal, mask_type)
            torch.cuda.synchronize()

        # Run multiple times and average
        times = []
        mems = []
        
        for run_idx in range(num_runs):
            reset_memory()
            torch.cuda.synchronize()
            start_time = time.perf_counter()

            L, params = run_training_step(energy_net, x, p_init, p_target, n_steps, alpha, use_flash_attention, causal, mask_type)

            torch.cuda.synchronize()
            end_time = time.perf_counter()
            
            times.append(end_time - start_time)
            mems.append(get_peak_memory())

        # Get gradients from last run
        grads = [p.grad.clone() if p.grad is not None else torch.zeros_like(p) for p in params]
        grad_norm = sum(g.norm().item()**2 for g in grads)**0.5
        
        avg_time = sum(times) / len(times)
        avg_mem = sum(mems) / len(mems)
        
        return L.item(), grads, grad_norm, avg_time, avg_mem
    
    except RuntimeError as e:
        error_msg = str(e)
        if "out of memory" in error_msg.lower():
            print(f"OOM Error")
        else:
            print(f"Runtime Error: {error_msg}")
        reset_memory()
        return None


def compare_gradients(grads1, grads2, atol=GRADIENT_ATOL):
    """Compare two sets of gradients. Returns None if either is None."""
    if grads1 is None or grads2 is None:
        return None, None, None
    
    total_params = len(grads1)
    matching_params = 0
    max_diff = 0.0
    
    for g1, g2 in zip(grads1, grads2):
        if torch.allclose(g1, g2, atol=atol):
            matching_params += 1
        diff = (g1 - g2).abs().max().item()
        max_diff = max(max_diff, diff)
    
    return matching_params, total_params, max_diff


def benchmark_sequence_length(seq_len, config, args_template):
    """Benchmark a single sequence length."""
    print(f"\n{'='*70}")
    print(f"Benchmarking Sequence Length: {seq_len}")
    print(f"{'='*70}")
    
    # Update args for this sequence length
    args = EBTModelArgs(
        dim=config["dim"],
        n_layers=args_template.n_layers,
        n_heads=args_template.n_heads,
        norm_eps=args_template.norm_eps,
        dyt_alpha_init=args_template.dyt_alpha_init,
        max_batch_size=config["batch_size"],
        max_seq_len=seq_len + 1,
        weight_initialization=args_template.weight_initialization,
        ebt_norm=args_template.ebt_norm,
        ebt_act_func=args_template.ebt_act_func,
        weight_initialization_gain=args_template.weight_initialization_gain,
    )
    
    # Setup
    torch.manual_seed(42)
    x, p_target = get_batch(config["batch_size"], seq_len, config["dim"], dtype=config["dtype"], device=device)
    p_init = torch.randn(config["batch_size"], seq_len, config["dim"], dtype=config["dtype"], device=device)
    
    torch.manual_seed(100)
    energy_net = EBT(args, max_mcmc_steps=config["n_steps"]).to(device)
    
    num_params = sum(p.numel() for p in energy_net.parameters())
    print(f"Model: {num_params:,} parameters")
    batch_size, dim = config["batch_size"], config["dim"]
    print(f"Config: B={batch_size}, S={seq_len}, D={dim}")
    
    results = {}
    
    # Test 1: Standard Attention
    print("Standard Attention:")
    std_result = test_training(
        energy_net, x, p_init, p_target, config["n_steps"], config["alpha"],
        use_flash_attention=False,
        causal=config["causal"],
        mask_type=config["mask_type"],
        warmup_iters=0,
        num_runs=3
    )
    
    if std_result is not None:
        loss1, grads1, grad_norm1, time_1, mem_1 = std_result
        results['standard'] = {
            'loss': loss1,
            'grad_norm': grad_norm1,
            'time': time_1,
            'memory': mem_1,
            'grads': grads1,
            'success': True
        }
        print(f"    Time: {time_1:.4f}s | Memory: {mem_1:.2f} GB")
    else:
        results['standard'] = {
            'loss': None,
            'grad_norm': None,
            'time': None,
            'memory': None,
            'grads': None,
            'success': False
        }
        print(f"Failed -> skipping")
    
    # Test 2: Flash Attention
    print("Flash Attention:")
    flash_nc_result = test_training(
        energy_net, x, p_init, p_target, config["n_steps"], config["alpha"],
        use_flash_attention=True,
        causal=config["causal"],
        mask_type=config["mask_type"],
        warmup_iters=5,
        num_runs=3
    )
    
    if flash_nc_result is not None:
        loss2, grads2, grad_norm2, time_2, mem_2 = flash_nc_result
        results['flash'] = {
            'loss': loss2,
            'grad_norm': grad_norm2,
            'time': time_2,
            'memory': mem_2,
            'grads': grads2,
            'success': True
        }
        print(f"    Time: {time_2:.4f}s | Memory: {mem_2:.2f} GB")
    else:
        results['flash'] = {
            'loss': None,
            'grad_norm': None,
            'time': None,
            'memory': None,
            'grads': None,
            'success': False
        }
        print(f"Failed -> skipping")
    
    # Gradient comparison (only if standard succeeded)
    if results['standard']['success']:
        print("\n  Gradient Verification:")
        grads1 = results['standard']['grads']
        
        if results['flash']['success']:
            grads2 = results['flash']['grads']
            match, total, max_diff = compare_gradients(grads1, grads2)
            print(f"    Standard vs Flash: {match}/{total} match (max diff: {max_diff:.2e})")
            results['grad_match'] = match
            results['grad_max_diff'] = max_diff
        else:
            print(f"    Standard vs Flash: N/A (Flash failed)")
            results['grad_match'] = None
            results['grad_max_diff'] = None
    else:
        print("\n  Gradient Verification: N/A (Standard failed)")
        results['grad_match'] = None
        results['grad_max_diff'] = None
    
    # Calculate speedups and memory savings (only if both succeeded)
    if results['standard']['success'] and results['flash']['success']:
        time_1 = results['standard']['time']
        time_2 = results['flash']['time']
        mem_1 = results['standard']['memory']
        mem_2 = results['flash']['memory']
        
        results['speedup'] = time_1 / time_2
        results['mem_reduc'] = mem_1 / mem_2
    else:
        results['speedup'] = None
        results['mem_reduc'] = None
    
    return results


def format_value(value, format_str="{:.2f}", na_str="N/A"):
    """Format a value or return N/A if None."""
    if value is None:
        return na_str
    return format_str.format(value)


def save_results_csv(all_results, filename):
    """Save results to CSV file."""

    output_dir = "benchmark/training"
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Write header
        writer.writerow([
            "seq_len",
            "std_time_s", "flash_time_s",
            "std_mem_gb", "flash_mem_gb",
            "speedup",
            "mem_reduc",
            "std_loss", "flash_loss",
            "std_grad_norm", "flash_grad_norm",
            "grad_match",
            "grad_max_diff",
            "std_success", "flash_success"
        ])
        
        # Write data
        for seq_len in sorted(all_results.keys()):
            results = all_results[seq_len]
            
            def csv_format(value, precision=6):
                """Format value for CSV, use NA for None."""
                if value is None:
                    return "NA"
                if isinstance(value, bool):
                    return str(value)
                if isinstance(value, int):
                    return str(value)
                return f"{value:.{precision}f}"
            
            writer.writerow([
                seq_len,
                csv_format(results['standard']['time']),
                csv_format(results['flash']['time']),
                csv_format(results['standard']['memory'], 4),
                csv_format(results['flash']['memory'], 4),
                csv_format(results['speedup'], 2),
                csv_format(results['mem_reduc'], 2),
                csv_format(results['standard']['loss'], 8),
                csv_format(results['flash']['loss'], 8),
                csv_format(results['standard']['grad_norm'], 8),
                csv_format(results['flash']['grad_norm'], 8),
                csv_format(results['grad_match'], 0) if results['grad_match'] is not None else "NA",
                csv_format(results['grad_max_diff'], 2) if results['grad_max_diff'] is not None else "NA",
                results['standard']['success'],
                results['flash']['success'],
            ])
    
    print(f"\nResults saved to: {filepath}")
    return filepath


def main():
    """Main benchmark execution."""
    args = parse_args()
    config = dict(
        batch_size=args.batch_size,
        dtype=getattr(torch, args.dtype),
        causal=args.causal,
        mask_type=args.mask_type,
        n_steps=args.n_steps,
        alpha=args.alpha,
        norm_eps=1e-5,
        dyt_alpha_init=0.5,
        max_batch_size=64,
        weight_initialization="xavier",
        ebt_norm="rms",
        ebt_act_func="silu",
        weight_initialization_gain=1.0,
    )

    seq_lengths = args.seq_lengths

    if args.size == "small":
        config.update(
            dim=192,
            n_layers=6,
            n_heads=6,
        )
    elif args.size == "base":
        config.update(
            dim=384,
            n_layers=12,
            n_heads=12,
        )

    print("\n" + "="*70)
    print("EBT ATTENTION BENCHMARK: Standard vs Flash Attention")
    print("="*70)
    print(f"Batch Size: {config['batch_size']}")
    print(f"Model Dim: {config['dim']}")
    print(f"Layers: {config['n_layers']}")
    print(f"Heads: {config['n_heads']}")
    print(f"MCMC Steps: {config['n_steps']}")
    print(f"Sequence Lengths: {seq_lengths}")
    print(f"Runs per config: 3 (averaged)")
    print("="*70 + "\n")
    
    # Create template args
    args_template = EBTModelArgs(
        dim=config["dim"],
        n_layers=config["n_layers"],
        n_heads=config["n_heads"],
        norm_eps=config["norm_eps"],
        dyt_alpha_init=config["dyt_alpha_init"],
        max_batch_size=config["max_batch_size"],
        max_seq_len=512,  # Will be updated per seq_len
        weight_initialization=config["weight_initialization"],
        ebt_norm=config["ebt_norm"],
        ebt_act_func=config["ebt_act_func"],
        weight_initialization_gain=config["weight_initialization_gain"],
    )
    
    # Run benchmarks for each sequence length
    all_results = {}
    
    for seq_len in seq_lengths:
        results = benchmark_sequence_length(
            seq_len, config, args_template
        )
        all_results[seq_len] = results
    
    # Print summary
    if all_results:
        save_results_csv(all_results, filename=f"size={args.size}_batch={args.batch_size}_DTYPE={args.dtype}_CAUSAL={args.causal}_MASK_TYPE={args.mask_type}_results.csv")
        
        print("\n" + "="*70)
        print("BENCHMARK COMPLETE")
        print("="*70)
        
        # Print key insights (only from successful runs)
        successful_results = {
            seq_len: res for seq_len, res in all_results.items()
            if res['standard']['success'] and res['flash']['success']
        }
        
        if successful_results:
            print("\nKey Insights (from successful runs):")
            avg_speedup = sum(r['speedup'] for r in successful_results.values()) / len(successful_results)
            avg_mem_reduc = sum(r['mem_reduc'] for r in successful_results.values()) / len(successful_results)
            
            print(f"Average speedup:          {avg_speedup:.2f}x")
            print(f"Average memory reduction: {avg_mem_reduc:.2f}x")
            
            # Count successes
            total_tests = len(all_results) * 2
            successful_tests = sum(
                res['standard']['success'] + res['flash']['success']
                for res in all_results.values()
            )
            print(f"Success rate: {successful_tests}/{total_tests} tests passed")
            
            # Find best performing config
            best_speedup_seq = max(successful_results.items(), key=lambda x: x[1]['speedup'])
            print(f"Best speedup at seq_len={best_speedup_seq[0]}: {best_speedup_seq[1]['speedup']:.2f}x")
        else:
            print("\nNo successful comparison runs (standard failed for all sequences)")
    else:
        print("\nNo benchmarks completed")


if __name__ == "__main__":
    main()