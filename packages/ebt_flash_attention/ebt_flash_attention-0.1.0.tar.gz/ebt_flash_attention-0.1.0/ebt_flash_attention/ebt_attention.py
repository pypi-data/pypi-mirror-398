from typing import Any, Literal, NamedTuple

from torch.autograd import Function
from torch.autograd.function import FunctionCtx
from torch import Tensor

import triton
import torch
import torch.autograd.forward_ad as fwAD

from ebt_flash_attention.ebt_forward_kernel import _ebt_attn_fwd
from ebt_flash_attention.ebt_forward_tma_kernel import _ebt_attn_fwd_tma
from ebt_flash_attention.ebt_backward_kernel import (
    _ebt_attn_bwd_dkdv,
    _ebt_attn_bwd_dkdv_superdiag,
    _ebt_attn_bwd_dq
)

try:
    from triton.tools.tensor_descriptor import TensorDescriptor

    HAS_TENSOR_DESC = True
except ModuleNotFoundError:
    HAS_TENSOR_DESC = False


MASK_CONST = (
    -1.0e9
)  # Use a large negative value for masking (compatible with float16, bfloat16, and float32)
MIN_SEQUENCE_LENGTH = 32


def is_hip():
    """Check if the current device is HIP."""
    try:
        return triton.runtime.driver.active.get_current_target().backend == "hip"
    except Exception:
        return False


def is_cuda():
    """Check if the current device is CUDA."""
    try:
        return triton.runtime.driver.active.get_current_target().backend == "cuda"
    except Exception:
        return False


def supports_host_descriptor():
    """Check if the current device supports host tensor descriptors."""
    try:
        return is_cuda() and torch.cuda.get_device_capability()[0] >= 9
    except Exception:
        return False
    
def supports_tma():
    """Check if the current device supports Tensor Memory Access (TMA)."""
    try:
        return HAS_TENSOR_DESC and is_cuda() and torch.cuda.get_device_capability()[0] >= 9
    except Exception:
        return False


def is_blackwell():
    """Check if the current device is Blackwell architecture."""
    try:
        return is_cuda() and torch.cuda.get_device_capability()[0] == 10
    except Exception:
        return False


def is_causal_mask(mask: Tensor) -> bool:
    """
    Check if a mask is causal (lower triangular for bool, upper triangular has mask_const for float).
    Handles both 2D (S, S) and 4D (B, H, S, S) masks.
    """
    if mask.dim() == 4:
        mask_2d = mask[0, 0]
    else:
        mask_2d = mask
    
    S = mask_2d.shape[0]

    triu_mask = torch.triu(torch.ones(S, S, dtype=torch.bool, device=mask.device), diagonal=1)
    upper_vals = mask_2d[triu_mask]

    if mask.dtype == torch.bool:
        return not upper_vals.any()
    else:
        return (upper_vals <= MASK_CONST).all()
    


class EBTAttn(Function):
    """JVP (Jacobian-Vector Product) for Attention Mechanism in EBT."""

    class Grid(NamedTuple):
        """Grid configuration for EBT Attention."""

        M_BLOCKS: int
        Z_H: int
        ONE: Literal[1]

    class FnCtx(FunctionCtx):
        """Function context for EBT Attention."""

        sm_scale: float
        HEAD_DIM_K: int
        causal: bool
        grid: 'EBTAttn.Grid'
        mask_tensor_o: Tensor
        mask_tensor_p: Tensor
        MASK_TYPE: int

    class FwdOutCtxContrib(NamedTuple):
        """Forward output context contributions for EBT Attention."""
        out_o_t: Tensor | None
        out_p_t: Tensor | None
        M_o: Tensor
        M_p: Tensor
        grid: 'EBTAttn.Grid'
        HEAD_DIM_K: int
        sm_scale: float
        mask_tensor_o: Tensor
        mask_tensor_p: Tensor
        MASK_TYPE: int

    class FwdOut(NamedTuple):
        """Forward output for EBT Attention."""

        out_o: Tensor
        out_p: Tensor
        ctx: 'EBTAttn.FwdOutCtxContrib'


    class JVPOut(NamedTuple):
        """JVP output for EBT Attention."""

        out_o: Tensor
        out_p: Tensor
        ctx: None

    class BwdOut(NamedTuple):
        """Backward output for EBT Attention."""

        q_o: Tensor
        k_o: Tensor
        v_o: Tensor
        q_p: Tensor
        k_p: Tensor
        v_p: Tensor
        q_o_t: None
        k_o_t: None
        v_o_t: None
        q_p_t: None
        k_p_t: None
        v_p_t: None
        mask_o: None
        mask_p: None
        causal: None
        sm_scale: None
        warp_specialize: None
        verify_attn_mask: None

    class Strides(NamedTuple):
        """Strides for JVP Attention."""

        z: int
        h: int
        n_ctx: int
        head_dim: int

    @staticmethod
    def forward(
        q_o: Tensor,
        k_o: Tensor,
        v_o: Tensor,
        q_p: Tensor,
        k_p: Tensor,
        v_p: Tensor,
        q_o_t: Tensor | None,
        k_o_t: Tensor | None,
        v_o_t: Tensor | None,
        q_p_t: Tensor | None,
        k_p_t: Tensor | None,
        v_p_t: Tensor | None,
        attn_mask: Tensor | None = None,
        causal: bool = False,
        sm_scale: float | None = None,
        USE_TMA: bool = True,
        warp_specialize: bool = True,
        verify_attn_mask: bool = True,
    ) -> 'EBTAttn.FwdOut':
        """Forward pass for EBT Attention.

        Args:
            q_o, k_o, v_o: Original stream tensors [Z, H, N_CTX, HEAD_DIM]
            q_p, k_p, v_p: Predicted stream tensors [Z, H, N_CTX, HEAD_DIM]
            q_o_t, k_o_t, v_o_t: Original stream tangents (for JVP)
            q_p_t, k_p_t, v_p_t: Predicted stream tangents (for JVP)
            attn_mask: Optional attention mask [S+1, S+1] or [Z, H, S+1, S+1]
                - Boolean: True = allow attention, False = block
                - Float: 0.0 = allow, MASK_CONST = block
            causal: If True, applies causal masking (can be combined with attn_mask)
            sm_scale: Softmax scale (default: 1/sqrt(HEAD_DIM))
            warp_specialize: Enable warp specialization
            verify_attn_mask: Verify mask validity
        """

        # Collect metadata
        Z, H, N_CTX, HEAD_DIM_Q = q_o.shape
        HEAD_DIM_K = k_o.shape[-1]
        HEAD_DIM_V = v_o.shape[-1]

        STAGE = 3 if causal else 1
        ENABLE_JVP = q_o_t is not None
        tma_available = N_CTX % MIN_SEQUENCE_LENGTH == 0

        assert HEAD_DIM_Q == HEAD_DIM_K and HEAD_DIM_K == HEAD_DIM_V, (
            "JVP attention requires HEAD_DIM_Q == HEAD_DIM_K == HEAD_DIM_V"
            f" but got HEAD_DIM_Q={HEAD_DIM_Q}, HEAD_DIM_K={HEAD_DIM_K}, HEAD_DIM_V={HEAD_DIM_V}"
        )
        assert HEAD_DIM_K in {16, 32, 64, 128, 256}, (
            "JVP attention only supports HEAD_DIM_K in {16, 32, 64, 128, 256},"
            f" but got HEAD_DIM_K={HEAD_DIM_K}",
        )

        if causal and attn_mask is not None:
            is_causal = is_causal_mask(attn_mask)
            assert is_causal, (
                "When causal=True, the provided attn_mask must also be causal."
                " Please ensure the mask is lower triangular (bool) or has MASK_CONST"
                " in the upper triangle (float)."
            )
        if attn_mask is not None:
            assert attn_mask.dtype in {
                torch.bool,
                q_o.dtype,
            }, "The attention mask must be of the dtype bool or that of the query tensor."
            

        # Initialize arguments and tensors
        if sm_scale is None:
            sm_scale = HEAD_DIM_K**-0.5

        out_o = torch.empty_like(q_o)
        out_p = torch.empty_like(q_p)
        out_o_t: Tensor | None = torch.empty_like(q_o_t) if ENABLE_JVP else None
        out_p_t: Tensor | None = torch.empty_like(q_p_t) if ENABLE_JVP else None
        M_o = torch.empty((Z, H, N_CTX), device=q_o.device, dtype=torch.float32)
        M_p = torch.empty((Z, H, N_CTX), device=q_p.device, dtype=torch.float32)

        # Tune kernel for custom (e.g., AMD) targets
        extra_kern_args = {}

        if is_hip():
            waves_per_eu = 3 if HEAD_DIM_K <= 64 else 2
            extra_kern_args = {"waves_per_eu": waves_per_eu, "allow_flush_denorm": True}

        if is_cuda() and warp_specialize:
            if (HEAD_DIM_K == 128 and q_o.dtype == torch.float16) or ENABLE_JVP:
                extra_kern_args["maxnreg"] = 168
            else:
                extra_kern_args["maxnreg"] = 80

        if hasattr(triton, "set_allocator") and is_cuda():
            def alloc_fn(size: int, align: int, _):
                return torch.empty(size, dtype=torch.int8, device="cuda")
            triton.set_allocator(alloc_fn)

        def strides_zhnd(t: Tensor) -> EBTAttn.Strides:
            return EBTAttn.Strides(t.stride(0), t.stride(1), t.stride(2), t.stride(3))

        if attn_mask is None:
            MASK_TYPE = 0
            mask_tensor_o = torch.empty(0, device=q_o.device, dtype=q_o.dtype)
            mask_tensor_p = torch.empty(0, device=q_p.device, dtype=q_p.dtype)
            mask_strides_o = (0, 0)
            mask_strides_p = (0, 0)
        else:
            attn_mask = attn_mask.squeeze()
            # Split mask into mask_o and mask_p
            if attn_mask.dim() == 2:
                # Mask is (S+1, S+1), split for EBT pattern
                mask_tensor_o = attn_mask[:-1, :-1]  # (S, S) for original stream
                mask_tensor_p = attn_mask[1:, :]   # (S, S+1) for predicted stream cross-attention
            else:
                raise ValueError(f"Mask must be 2D, got {attn_mask.dim()}D")

            if attn_mask.dtype == torch.bool:
                MASK_TYPE = 1
                mask_tensor_o = mask_tensor_o.contiguous()
                mask_tensor_p = mask_tensor_p.contiguous()
                mask_strides_o = (mask_tensor_o.stride(0), mask_tensor_o.stride(1))
                mask_strides_p = (mask_tensor_p.stride(0), mask_tensor_p.stride(1))
                if verify_attn_mask:
                    assert mask_tensor_o.any(
                        dim=(-1, -2)
                    ).all(), "The attention mask cannot be all False for any head."
            else:
                MASK_TYPE = 2
                mask_tensor_o = mask_tensor_o.to(q_o.dtype).contiguous()
                mask_tensor_p = mask_tensor_p.to(q_o.dtype).contiguous()
                mask_strides_o = (mask_tensor_o.stride(0), mask_tensor_o.stride(1))
                mask_strides_p = (mask_tensor_p.stride(0), mask_tensor_p.stride(1))
                if verify_attn_mask:
                    assert not torch.isinf(
                        mask_tensor_o
                    ).any(), "The attention mask cannot contain -inf or inf."
                    assert not torch.isnan(
                        mask_tensor_o
                    ).any(), "The attention mask cannot contain NaNs."
                    assert (
                        (mask_tensor_o != MASK_CONST).any(dim=(-1, -2)).all()
                    ), f"The attention mask cannot be all {MASK_CONST} for any head."

        # Set up grid for kernel launch
        Z_H = Z * H
        num_stages = (
            5
            if is_cuda() and torch.cuda.get_device_capability()[0] == 9
            else 3
        )

        def grid(META: dict[str, Any]) -> EBTAttn.Grid:
            return EBTAttn.Grid(triton.cdiv(N_CTX, META['BLOCK_M']), Z_H, 1)
        
        if USE_TMA and tma_available and supports_tma():
            y_dim = Z_H * N_CTX
            tma_block_shape = [MIN_SEQUENCE_LENGTH, HEAD_DIM_K]

            desc_q_o = TensorDescriptor(
                q_o,
                shape=[y_dim, HEAD_DIM_K],
                strides=[HEAD_DIM_K, 1],
                block_shape=tma_block_shape,
            )
            desc_q_o_t = (
                desc_q_o
                if q_o_t is None
                else TensorDescriptor(
                    q_o_t,
                    shape=[y_dim, HEAD_DIM_K],
                    strides=[HEAD_DIM_K, 1],
                    block_shape=tma_block_shape,
                )
            )

            desc_q_p = TensorDescriptor(
                q_p,
                shape=[y_dim, HEAD_DIM_K],
                strides=[HEAD_DIM_K, 1],
                block_shape=tma_block_shape,
            )
            desc_q_p_t = (
                desc_q_p
                if q_p_t is None
                else TensorDescriptor(
                    q_p_t,
                    shape=[y_dim, HEAD_DIM_K],
                    strides=[HEAD_DIM_K, 1],
                    block_shape=tma_block_shape,
                )
            )

            desc_v_o = TensorDescriptor(
                v_o,
                shape=[y_dim, HEAD_DIM_K],
                strides=[HEAD_DIM_K, 1],
                block_shape=tma_block_shape,
            )
            desc_v_o_t = (
                desc_v_o
                if v_o_t is None
                else TensorDescriptor(
                    v_o_t,
                    shape=[y_dim, HEAD_DIM_K],
                    strides=[HEAD_DIM_K, 1],
                    block_shape=tma_block_shape,
                )
            )

            desc_v_p = TensorDescriptor(
                v_p,
                shape=[y_dim, HEAD_DIM_K],
                strides=[HEAD_DIM_K, 1],
                block_shape=tma_block_shape,
            )
            desc_v_p_t = (
                desc_v_p
                if v_p_t is None
                else TensorDescriptor(
                    v_p_t,
                    shape=[y_dim, HEAD_DIM_K],
                    strides=[HEAD_DIM_K, 1],
                    block_shape=tma_block_shape,
                )
            )

            desc_k_o = TensorDescriptor(
                k_o,
                shape=[y_dim, HEAD_DIM_K],
                strides=[HEAD_DIM_K, 1],
                block_shape=tma_block_shape,
            )
            desc_k_o_t = (
                desc_k_o
                if k_o_t is None
                else TensorDescriptor(
                    k_o_t,
                    shape=[y_dim, HEAD_DIM_K],
                    strides=[HEAD_DIM_K, 1],
                    block_shape=tma_block_shape,
                )
            )

            desc_k_p = TensorDescriptor(
                k_p,
                shape=[y_dim, HEAD_DIM_K],
                strides=[HEAD_DIM_K, 1],
                block_shape=tma_block_shape,
            )
            desc_k_p_t = (
                desc_k_p
                if k_p_t is None
                else TensorDescriptor(
                    k_p_t,
                    shape=[y_dim, HEAD_DIM_K],
                    strides=[HEAD_DIM_K, 1],
                    block_shape=tma_block_shape,
                )
            )

            desc_out_o = TensorDescriptor(
                out_o,
                shape=[y_dim, HEAD_DIM_K],
                strides=[HEAD_DIM_K, 1],
                block_shape=tma_block_shape,
            )
            desc_out_o_t = (
                desc_out_o
                if out_o_t is None
                else TensorDescriptor(
                    out_o_t,
                    shape=[y_dim, HEAD_DIM_K],
                    strides=[HEAD_DIM_K, 1],
                    block_shape=tma_block_shape,
                )
            )

            desc_out_p = TensorDescriptor(
                out_p,
                shape=[y_dim, HEAD_DIM_K],
                strides=[HEAD_DIM_K, 1],
                block_shape=tma_block_shape,
            )
            desc_out_p_t = (
                desc_out_p
                if out_p_t is None
                else TensorDescriptor(
                    out_p_t,
                    shape=[y_dim, HEAD_DIM_K],
                    strides=[HEAD_DIM_K, 1],
                    block_shape=tma_block_shape,
                )
            )

            _ebt_attn_fwd_tma[grid](
                desc_q_o,
                desc_k_o,
                desc_v_o,
                desc_q_p,
                desc_k_p,
                desc_v_p,
                desc_q_o_t,
                desc_k_o_t,
                desc_v_o_t,
                desc_q_p_t,
                desc_k_p_t,
                desc_v_p_t,
                sm_scale,
                mask_tensor_o,
                mask_tensor_p,
                desc_out_o,
                desc_out_p,
                desc_out_o_t,
                desc_out_p_t,
                M_o,
                M_p,
                *strides_zhnd(q_o),
                *strides_zhnd(k_o),
                *strides_zhnd(v_o),
                *strides_zhnd(out_o),
                *mask_strides_o,
                *mask_strides_p,
                Z,
                H,
                N_CTX=N_CTX,
                HEAD_DIM=HEAD_DIM_K,
                STAGE=STAGE,
                warp_specialize=warp_specialize,
                ENABLE_JVP=ENABLE_JVP,
                MASK_TYPE=MASK_TYPE,
                **extra_kern_args,
            )
        else:
            _ebt_attn_fwd[grid](
                q_o,
                k_o,
                v_o,
                q_p,
                k_p,
                v_p,
                q_o_t,
                k_o_t,
                v_o_t,
                q_p_t,
                k_p_t,
                v_p_t,
                sm_scale,
                mask_tensor_o,
                mask_tensor_p,
                out_o,
                out_p,
                out_o_t,
                out_p_t,
                M_o,
                M_p,
                *strides_zhnd(q_o),
                *strides_zhnd(k_o),
                *strides_zhnd(v_o),
                *strides_zhnd(out_o),
                *mask_strides_o,
                *mask_strides_p,
                Z,
                H,
                N_CTX=N_CTX,
                HEAD_DIM=HEAD_DIM_K,
                STAGE=STAGE,
                warp_specialize=warp_specialize,
                ENABLE_JVP=ENABLE_JVP,
                MASK_TYPE=MASK_TYPE,
                **extra_kern_args,
            )

        return EBTAttn.FwdOut(
            out_o,
            out_p,
            EBTAttn.FwdOutCtxContrib(
                out_o_t,
                out_p_t,
                M_o,
                M_p,
                grid,
                HEAD_DIM_K,
                sm_scale,
                mask_tensor_o,
                mask_tensor_p,
                MASK_TYPE,
            ),
        )

    @staticmethod
    def setup_context(ctx: 'EBTAttn.FnCtx', inputs, outputs: 'EBTAttn.FwdOut') -> None:
        """Set up the context for JVP Attention."""
        (
            q_o, k_o, v_o, q_p, k_p, v_p,
            q_o_t, k_o_t, v_o_t, q_p_t, k_p_t, v_p_t,
            attn_mask, causal, sm_scale, warp_specialize, USE_TMA, verify_attn_mask,
        ) = inputs

        out_o, out_p, (
            out_o_t, out_p_t, M_o, M_p, grid, HEAD_DIM_K, sm_scale,
            mask_tensor_o, mask_tensor_p, MASK_TYPE,
        ) = outputs

        ctx.grid = grid
        ctx.save_for_forward(out_o_t, out_p_t)
        ctx.save_for_backward(q_o, k_o, v_o, out_o, M_o, q_p, k_p, v_p, out_p, M_p)

        ctx.sm_scale = sm_scale
        ctx.HEAD_DIM_K = HEAD_DIM_K
        ctx.causal = causal
        ctx.mask_tensor_o = mask_tensor_o
        ctx.mask_tensor_p = mask_tensor_p
        ctx.MASK_TYPE = MASK_TYPE

    @staticmethod
    def fwd(
        q_o: Tensor,
        k_o: Tensor,
        v_o: Tensor,
        q_p: Tensor,
        k_p: Tensor,
        v_p: Tensor,
        attn_mask: Tensor | None = None,
        causal: bool = False,
        sm_scale: float | None = None,
        warp_specialize: bool = True,
        USE_TMA: bool = True,
    ) -> tuple[Tensor, Tensor]:
        """Forward pass for EBT Attention."""
        if not (q_o.is_contiguous() and k_o.is_contiguous() and v_o.is_contiguous()):
            q_o, k_o, v_o = q_o.contiguous(), k_o.contiguous(), v_o.contiguous()
        if not (q_p.is_contiguous() and k_p.is_contiguous() and v_p.is_contiguous()):
            q_p, k_p, v_p = q_p.contiguous(), k_p.contiguous(), v_p.contiguous()

        fwd_out: EBTAttn.FwdOut = EBTAttn.apply(
            q_o, k_o, v_o, q_p, k_p, v_p,
            None, None, None, None, None, None,
            attn_mask, causal, sm_scale, warp_specialize, USE_TMA,
        )

        out_o, out_p, _ = fwd_out
        return out_o, out_p

    @staticmethod
    def fwd_dual(
        q_o: Tensor,
        k_o: Tensor,
        v_o: Tensor,
        q_p: Tensor,
        k_p: Tensor,
        v_p: Tensor,
        attn_mask: Tensor | None = None,
        causal: bool = False,
        sm_scale: float | None = None,
        warp_specialize: bool = True,
        USE_TMA: bool = True,
    ) -> tuple[Tensor, Tensor]:
        """Forward pass for EBT Attention with dual tensor inputs."""
        if not (q_o.is_contiguous() and k_o.is_contiguous() and v_o.is_contiguous()):
            q_o, k_o, v_o = q_o.contiguous(), k_o.contiguous(), v_o.contiguous()
        if not (q_p.is_contiguous() and k_p.is_contiguous() and v_p.is_contiguous()):
            q_p, k_p, v_p = q_p.contiguous(), k_p.contiguous(), v_p.contiguous()

        q_o, q_o_t = fwAD.unpack_dual(q_o)
        k_o, k_o_t = fwAD.unpack_dual(k_o)
        v_o, v_o_t = fwAD.unpack_dual(v_o)
        q_p, q_p_t = fwAD.unpack_dual(q_p)
        k_p, k_p_t = fwAD.unpack_dual(k_p)
        v_p, v_p_t = fwAD.unpack_dual(v_p)

        fwd_out: EBTAttn.FwdOut = EBTAttn.apply(
            q_o, k_o, v_o, q_p, k_p, v_p,
            q_o_t, k_o_t, v_o_t, q_p_t, k_p_t, v_p_t,
            attn_mask, causal, sm_scale, warp_specialize, USE_TMA,
        )

        out_o, out_p, aux_ctx = fwd_out
        out_o_t, out_p_t = aux_ctx.out_o_t, aux_ctx.out_p_t

        if out_o_t is not None:
            out_o = fwAD.make_dual(out_o, out_o_t)
        if out_p_t is not None:
            out_p = fwAD.make_dual(out_p, out_p_t)
            
        return out_o, out_p

    @staticmethod
    def jvp(ctx: 'EBTAttn.FnCtx', *_) -> 'EBTAttn.JVPOut':
        """Compute the Jacobian-vector product (JVP)."""
        return EBTAttn.JVPOut(ctx.saved_for_forward[0], ctx.saved_for_forward[1], None)

    @staticmethod
    def backward(ctx, dout_o, dout_p, _) -> 'EBTAttn.BwdOut':
        """Backward pass for EBT Attention."""
        q_o, k_o, v_o, out_o, M_o, q_p, k_p, v_p, out_p, M_p = ctx.saved_tensors
        mask_tensor_o, mask_tensor_p = ctx.mask_tensor_o, ctx.mask_tensor_p
        sm_scale = ctx.sm_scale

        STAGE = 3 if ctx.causal else 1
        
        Z, H, N_CTX, HEAD_DIM = q_o.shape
        BLOCK_MIN = MIN_SEQUENCE_LENGTH
        BLOCK_M, BLOCK_N = BLOCK_MIN, BLOCK_MIN

        # Validate contiguity
        if not (
            q_o.is_contiguous() and k_o.is_contiguous() and v_o.is_contiguous() and out_o.is_contiguous()
            and q_p.is_contiguous() and k_p.is_contiguous() and v_p.is_contiguous() and out_p.is_contiguous()
        ):
            raise ValueError("EBTAttn expected q, k, v, o to be contiguous")

        if not dout_o.is_contiguous():
            dout_o = dout_o.contiguous()
        if not dout_p.is_contiguous():
            dout_p = dout_p.contiguous()

        # Initialize gradient tensors
        dq_o = torch.empty_like(q_o)
        dk_o = torch.empty_like(k_o)
        dv_o = torch.empty_like(v_o)
        dq_p = torch.empty_like(q_p)
        dk_p = torch.empty_like(k_p)
        dv_p = torch.empty_like(v_p)
       
        if ctx.MASK_TYPE == 0:
            mask_strides_o = (0, 0)
            mask_strides_p = (0, 0)
        else:
            mask_strides_o = (mask_tensor_o.stride(0), mask_tensor_o.stride(1))
            mask_strides_p = (mask_tensor_p.stride(0), mask_tensor_p.stride(1))

        Z_H = Z * H
        num_stages = (
            5
            if is_cuda() and torch.cuda.get_device_capability()[0] == 9
            else 3
        )
        
        _ebt_attn_bwd_dkdv[lambda META: (triton.cdiv(N_CTX, META['BLOCK_N']), Z_H)](
            q_o, q_p, k_o, v_o,
            dout_o, dout_p, out_o, out_p,
            M_o, M_p,
            mask_tensor_o, mask_tensor_p,
            dk_o, dv_o,
            sm_scale,
            q_o.stride(0), q_o.stride(1), q_o.stride(2), q_o.stride(3),
            k_o.stride(0), k_o.stride(1), k_o.stride(2), k_o.stride(3),
            v_o.stride(0), v_o.stride(1), v_o.stride(2), v_o.stride(3),
            out_o.stride(0), out_o.stride(1), out_o.stride(2), out_o.stride(3),
            *mask_strides_o,
            *mask_strides_p,
            Z, H, N_CTX,
            HEAD_DIM=HEAD_DIM,
            STAGE=STAGE,
            MASK_TYPE=ctx.MASK_TYPE,
        )

        _ebt_attn_bwd_dkdv_superdiag[lambda META: (triton.cdiv(N_CTX, META['BLOCK_M']), Z_H)](
            q_p, k_p, v_p, dout_p, out_p,
            M_p, mask_tensor_p,
            dk_p, dv_p,
            sm_scale,
            q_p.stride(0), q_p.stride(1), q_p.stride(2), q_p.stride(3),
            k_p.stride(0), k_p.stride(1), k_p.stride(2), k_p.stride(3),
            v_p.stride(0), v_p.stride(1), v_p.stride(2), v_p.stride(3),
            out_p.stride(0), out_p.stride(1), out_p.stride(2), out_p.stride(3),
            *mask_strides_p,
            Z, H, N_CTX,
            HEAD_DIM=HEAD_DIM,
            MASK_TYPE=ctx.MASK_TYPE,
        )
        
        _ebt_attn_bwd_dq[lambda META: (triton.cdiv(N_CTX, META['BLOCK_M']), Z_H)](
            q_o, q_p, k_o, k_p, v_o, v_p,
            dout_o, dout_p, out_o, out_p,
            M_o, M_p,
            mask_tensor_o, mask_tensor_p,
            dq_o, dq_p,
            sm_scale,
            q_o.stride(0), q_o.stride(1), q_o.stride(2), q_o.stride(3),
            k_o.stride(0), k_o.stride(1), k_o.stride(2), k_o.stride(3),
            v_o.stride(0), v_o.stride(1), v_o.stride(2), v_o.stride(3),
            out_o.stride(0), out_o.stride(1), out_o.stride(2), out_o.stride(3),
            *mask_strides_o,
            *mask_strides_p,
            Z, H, N_CTX,
            HEAD_DIM=HEAD_DIM,
            STAGE=STAGE,
            MASK_TYPE=ctx.MASK_TYPE,
        )

        return EBTAttn.BwdOut(
            dq_o, dk_o, dv_o, dq_p, dk_p, dv_p, None, None, None, None, None, None, None, None, None, None, None, None
        )


ebt_attention = EBTAttn.fwd