<div align="center">

# EBT Flash Attention

<a href="https://pytorch.org/get-started/locally/"><img alt="PyTorch" src="https://img.shields.io/badge/PyTorch-ee4c2c?logo=pytorch&logoColor=white"></a>
[![DOI](https://zenodo.org/badge/1110690696.svg)](https://doi.org/10.5281/zenodo.18025835)
[![PyPI version](https://badge.fury.io/py/ebt_flash_attention.svg)](https://badge.fury.io/py/ebt_flash_attention)
[![Project Status: Active – The project has reached a stable, usable state and is being actively developed.](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<img src="assets/energy_landscape.png" width="480">

</div>

## Description

EBT Flash Attention is an efficient Triton implementation of the [Energy Based Transformer](https://arxiv.org/abs/2507.02092) (EBT) Attention algorithm, optimized for large scale EBTs with reduced memory usage and improved speed. It supports second-order derivatives, inspired by the [JVP Flash Attention](https://github.com/amorehead/jvp_flash_attention) implementation, to enable second-order differentiation needed for Loss Computation.

## Features

This implementation includes:
- **Flexible Sequence Length**: Can be used with any sequence length without any constraints.
- **TMA Support**: supports Tensor Memory Accelerator (TMA) for Hopper Architecture (H100 GPUs) and above, improving memory bandwidth and overall performance.
- **Multiple Data Types support**: Compatible with multiple data types including float32, float16 and bfloat16.
- **Second-Order Derivatives**: Supports second-order differentiation with JVPs (Jacobian-Vector Product) and HVPs (Hessian-Vector Product), needed to compute the training loss in EBTs.
- **Causal and Masked Attention**: Supports both causal attention and various attention masks (boolean and additive).

> Note: The TMA support is only available for sequence lengths that are multiples of 32.

## Requirements

- Python >= 3.10
- PyTorch >= 2.9.1
- Triton >= 3.5.1

## Installation

You can install EBT Flash Attention via pip as follows:

```bash
pip install ebt_flash_attention
```

or via source:

```bash
git clone https://github.com/emiledgl/ebt_flash_attention.git
cd ebt_flash_attention
pip install -e .
```

## Usage

Once installed, you can use the `ebt_attention` function to compute the EBT Attention in place of the PyTorch's implementation as follows:

```python
import torch
from ebt_flash_attention.ebt_attention import ebt_attention

device = torch.device("cuda")
dtype = torch.float32

batch_size = 16
n_heads = 8
seqlen = 128
head_dim = 32

# Create random Q, K, V tensors for input & prediction
q_o = torch.randn(batch_size, n_heads, seqlen, head_dim, dtype=dtype, device=device)
q_p = torch.randn(batch_size, n_heads, seqlen, head_dim, dtype=dtype, device=device)
k_o = torch.randn(batch_size, n_heads, seqlen, head_dim, dtype=dtype, device=device)
k_p = torch.randn(batch_size, n_heads, seqlen, head_dim, dtype=dtype, device=device)
v_o = torch.randn(batch_size, n_heads, seqlen, head_dim, dtype=dtype, device=device)
v_p = torch.randn(batch_size, n_heads, seqlen, head_dim, dtype=dtype, device=device)

# Scaling factor for softmax
sm_scale = 1.0 / (head_dim ** 0.5)

# Create causal boolean attention mask
attn_mask = torch.tril(torch.ones((seqlen + 1, seqlen + 1), device=device)).bool()

# Compute EBT Attention
# Output is a tuple containing input & prediction attention outputs
out_o, out_p = ebt_attention(
    q_o, k_o, v_o,
    q_p, k_p, v_p,
    sm_scale=sm_scale,
    attn_mask=attn_mask,
    causal=True,
)
```

If you want to check the forward, backward and second-order backward passes of any configuration, you can use the `check.py` script as follows:

```python 
python check.py --dtype float32 --mask_type boolean --causal --batch_size 8 --n_heads 8 --seqlen 128 --head_dim 32
```

## Results

The following plots show the TFLOPS comparison between the standard implementation in PyTorch (with and without torch.compile) and the EBT Flash Attention implementation for additive & boolean masks with causal attention enabled.

These benchmarks were performed on an NVIDIA H100 GPU with float32 data type, batch size of 8, n_heads of size 8 and head dimension of size 32.

The following plot shows the results for additive masks:

<p align="center">
    <img src="assets/tflops_comparison-dtype=float32-causal=True-mask=additive-batch8-head8-d32.png" width="800"/>
</p>

This plot shows the results for boolean masks:

<p align="center">
    <img src="assets/tflops_comparison-dtype=float32-causal=True-mask=boolean-batch8-head8-d32.png" width="800"/>
</p>

- Backward pass manages to achieve similar speedups as forward pass.
- The difference in TFLOPS between additive and boolean masks is marginal. Boolean mask seems to perform better on lower sequence lengths while additive mask is slightly better on higher sequence lengths.

## Benchmarks

### Training

The training benchmark consists of running a full training step with forward, backward and second-order backward passes.
We compare the standard PyTorch implementation of the EBT with the implementation using EBT Flash Attention, on a 12 layers model, with batch size of 16, n_heads of size 12 and head dimension of size 32.

The training step computes 3 MCMC steps on the prediction sequence (with create_graph=True) and the backward pass.

These benchmarks were performed on an NVIDIA H100 GPU with float32 data type.

> Note: "OOM" indicates that the standard implementation ran out of memory for that configuration.

```
====================================================================================================
TRAINING BENCHMARK SUMMARY (DTYPE=float32)
====================================================================================================
Seq Len    Causal     Mask         Method       Time (ms)    Mem (GB)     Max Error    Grad
----------------------------------------------------------------------------------------------------
32         True       additive     sdpa         425.266      2.50         baseline     
32         True       additive     ebt_attn     211.737      2.13         0.00e+00     OK

32         True       boolean      sdpa         440.307      2.50         baseline     
32         True       boolean      ebt_attn     211.747      2.13         3.60e-07     OK

32         False      additive     sdpa         427.207      2.50         baseline     
32         False      additive     ebt_attn     207.932      2.13         0.00e+00     OK

32         False      boolean      sdpa         436.109      2.50         baseline     
32         False      boolean      ebt_attn     206.128      2.13         3.60e-07     OK

64         True       additive     sdpa         296.357      5.39         baseline     
64         True       additive     ebt_attn     219.284      4.14         2.40e-07     OK

64         True       boolean      sdpa         305.656      5.39         baseline     
64         True       boolean      ebt_attn     219.791      4.14         2.40e-07     OK

64         False      additive     sdpa         297.423      5.39         baseline     
64         False      additive     ebt_attn     215.720      4.14         2.40e-07     OK

64         False      boolean      sdpa         303.493      5.39         baseline     
64         False      boolean      ebt_attn     213.720      4.14         2.40e-07     OK

128        True       additive     sdpa         367.238      12.15        baseline     
128        True       additive     ebt_attn     253.925      7.93         1.20e-07     OK

128        True       boolean      sdpa         376.429      12.15        baseline     
128        True       boolean      ebt_attn     254.534      7.93         1.20e-07     OK

128        False      additive     sdpa         368.169      12.15        baseline     
128        False      additive     ebt_attn     248.946      7.93         1.20e-07     OK

128        False      boolean      sdpa         377.645      12.15        baseline     
128        False      boolean      ebt_attn     248.656      7.93         1.20e-07     OK

256        True       additive     sdpa         502.706      31.02        baseline     
256        True       additive     ebt_attn     363.066      15.58        3.60e-07     OK

256        True       boolean      sdpa         510.318      31.02        baseline     
256        True       boolean      ebt_attn     363.155      15.57        3.60e-07     OK

256        False      additive     sdpa         503.836      31.02        baseline     
256        False      additive     ebt_attn     359.674      15.58        3.60e-07     OK

256        False      boolean      sdpa         508.400      31.02        baseline     
256        False      boolean      ebt_attn     358.361      15.57        3.60e-07     OK

512        True       additive     sdpa         OOM          N/A          baseline     
512        True       additive     ebt_attn     534.945      30.76        N/A          OK

512        True       boolean      sdpa         OOM          N/A          baseline     
512        True       boolean      ebt_attn     535.033      30.71        N/A          OK

512        False      additive     sdpa         OOM          N/A          baseline     
512        False      additive     ebt_attn     537.632      30.76        N/A          OK

512        False      boolean      sdpa         OOM          N/A          baseline     
512        False      boolean      ebt_attn     535.801      30.71        N/A          OK

1024       True       additive     sdpa         OOM          N/A          baseline     
1024       True       additive     ebt_attn     782.558      61.17        N/A          OK

1024       True       boolean      sdpa         OOM          N/A          baseline     
1024       True       boolean      ebt_attn     782.632      60.98        N/A          OK

1024       False      additive     sdpa         OOM          N/A          baseline     
1024       False      additive     ebt_attn     842.437      61.17        N/A          OK

1024       False      boolean      sdpa         OOM          N/A          baseline     
1024       False      boolean      ebt_attn     845.735      60.98        N/A          OK

=====================================================================================
PERFORMANCE STATISTICS
=====================================================================================
Average Speedup:        1.58x
Max Speedup:            2.12x
  -> Config: Seq=32, Causal=False, Mask=boolean
--------------------------------------------------
Average Mem Reduction:  1.50x
Max Mem Reduction:      1.99x
  -> Config: Seq=256, Causal=True, Mask=boolean
--------------------------------------------------
```


### Inference

The inference benchmark consists of running a forward pass with Test-Time Optimization.
We compare the standard PyTorch implementation of the EBT with the implementation using EBT Flash Attention, on a 12 layers model, with batch size of 16, n_heads of size 12 and head dimension of size 32.

The inference step computes the forward pass for 3 MCMC steps on the prediction sequence (here create_graph=False).

These benchmarks were performed on an NVIDIA H100 GPU with float32 data type.

```
================================================================================
INFERENCE BENCHMARK SUMMARY (DTYPE=float32)
================================================================================
Seq Len    Causal     Mask         Method       Time (ms)    Mem (GB)    
--------------------------------------------------------------------------------
32         True       additive     sdpa         210.581      0.45        
32         True       additive     ebt_attn     106.064      0.40        

32         True       boolean      sdpa         217.091      0.45        
32         True       boolean      ebt_attn     101.613      0.40        

32         False      additive     sdpa         210.173      0.45        
32         False      additive     ebt_attn     100.353      0.40        

32         False      boolean      sdpa         219.407      0.45        
32         False      boolean      ebt_attn     96.534       0.40        

64         True       additive     sdpa         106.014      0.87        
64         True       additive     ebt_attn     102.161      0.69        

64         True       boolean      sdpa         107.572      0.87        
64         True       boolean      ebt_attn     98.608       0.69        

64         False      additive     sdpa         104.716      0.87        
64         False      additive     ebt_attn     97.219       0.69        

64         False      boolean      sdpa         107.027      0.87        
64         False      boolean      ebt_attn     93.470       0.69        

128        True       additive     sdpa         115.635      1.87        
128        True       additive     ebt_attn     106.811      1.24        

128        True       boolean      sdpa         117.889      1.87        
128        True       boolean      ebt_attn     102.387      1.24        

128        False      additive     sdpa         114.614      1.87        
128        False      additive     ebt_attn     101.511      1.24        

128        False      boolean      sdpa         116.341      1.87        
128        False      boolean      ebt_attn     97.803       1.24        

256        True       additive     sdpa         136.719      4.76        
256        True       additive     ebt_attn     120.794      2.37        

256        True       boolean      sdpa         137.041      4.76        
256        True       boolean      ebt_attn     115.902      2.37        

256        False      additive     sdpa         136.573      4.76        
256        False      additive     ebt_attn     114.754      2.37        

256        False      boolean      sdpa         136.924      4.76        
256        False      boolean      ebt_attn     110.083      2.37        

512        True       additive     sdpa         330.848      14.00       
512        True       additive     ebt_attn     184.090      4.64        

512        True       boolean      sdpa         330.176      14.00       
512        True       boolean      ebt_attn     179.398      4.63        

512        False      additive     sdpa         330.329      14.00       
512        False      additive     ebt_attn     184.211      4.64        

512        False      boolean      sdpa         330.236      14.00       
512        False      boolean      ebt_attn     181.261      4.63        

1024       True       additive     sdpa         984.174      46.64       
1024       True       additive     ebt_attn     334.150      9.20        

1024       True       boolean      sdpa         981.342      46.64       
1024       True       boolean      ebt_attn     333.425      9.16        

1024       False      additive     sdpa         982.682      46.64       
1024       False      additive     ebt_attn     367.921      9.20        

1024       False      boolean      sdpa         983.099      46.64       
1024       False      boolean      ebt_attn     370.282      9.16        

2048       True       additive     sdpa         OOM          N/A         
2048       True       additive     ebt_attn     734.583      18.39       

2048       True       boolean      sdpa         OOM          N/A         
2048       True       boolean      ebt_attn     739.771      18.23       

2048       False      additive     sdpa         OOM          N/A         
2048       False      additive     ebt_attn     917.307      18.39       

2048       False      boolean      sdpa         OOM          N/A         
2048       False      boolean      ebt_attn     934.070      18.24       

=====================================================================================
PERFORMANCE STATISTICS
=====================================================================================
Average Speedup:        1.69x
Max Speedup:            2.95x
  -> Config: Seq=1024, Causal=True, Mask=additive
--------------------------------------------------
Average Mem Reduction:  2.34x
Max Mem Reduction:      5.09x
  -> Config: Seq=1024, Causal=True, Mask=boolean
--------------------------------------------------
```

There is nearly no difference in speedup or memory reduction between boolean and additive masks.

The training benchmark manages to achieve an average speedup of 1.58x during training with a maximum speedup of 2.12x on sequence length of 32.

The inference benchmark achieves an average speedup of 1.69x during inference with a maximum speedup of 2.95x on sequence length of 1024.
The results are similar with float16 and bfloat16 data types.

## Future Improvements

- Add attention dropout support.
- Improve TMA support for non-multiple of 32 sequence lengths.

## Citation
If you find this implementation useful and use it in your research, please consider citing:
```bibtex
@software{Dugelay_EBT_Flash_Attention_2025,
  author = {Dugelay, Emile},
  doi = {10.5281/zenodo.18025836},
  license = {MIT},
  month = dec,
  title = {{EBT Flash Attention}},
  url = {https://github.com/emiledgl/ebt_flash_attention},
  version = {0.2.0},
  year = {2025}
}
```

## License

This project is covered under the **MIT License**.

## Acknowledgements

- This work is primarly made for and build upon the [Energy Based Transformer](https://github.com/alexiglad/EBT) framework.
- The implementation of second-order derivatives is inspired by the [JVP Flash Attention](https://github.com/amorehead/jvp_flash_attention) implementation.
- The efficient attention mechanism is inspired by the [Flash Attention](https://github.com/Dao-AILab/flash-attention) implementation.

Thank you for making this work possible!