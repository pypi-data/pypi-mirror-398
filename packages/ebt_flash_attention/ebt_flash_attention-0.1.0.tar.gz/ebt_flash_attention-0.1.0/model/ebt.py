from typing import Optional

import math
import torch
from torch import nn
from torch.nn import functional as F

from model.utils import EBTModelArgs, init_whole_model_weights
from model.modules import DyT, RMSNorm, precompute_freqs_cis, apply_rotary_emb

from pytorch_ebt_attention import pytorch_ebt_attention
from ebt_flash_attention.ebt_attention import ebt_attention

MASK_CONST = -1e9

class Attention(nn.Module):
    """Multi-head attention module."""
    def __init__(self, args: EBTModelArgs):
        """
        Initialize the Attention module.

        Args:
            args (EBTModelArgs): Model configuration parameters.

        Attributes:
            n_heads (int): Number of query heads.
            n_kv_heads (int): Number of key and value heads.
            head_dim (int): Dimension size of each attention head.
            wq (Linear): Linear transformation for queries.
            wk (Linear): Linear transformation for keys.
            wv (Linear): Linear transformation for values.
            wo (Linear): Linear transformation for output.

        """
        super().__init__()
        self.n_heads = args.n_heads
        self.n_kv_heads = args.n_heads if args.n_kv_heads is None else args.n_kv_heads
        self.head_dim = args.dim // args.n_heads
        
        self.wq = nn.Linear(args.dim, args.n_heads * self.head_dim, bias=False)
        init_whole_model_weights(self.wq, args.weight_initialization, weight_initialization_gain=args.weight_initialization_gain)
        
        self.wk = nn.Linear(args.dim, args.n_heads * self.head_dim, bias=False)
        init_whole_model_weights(self.wk, args.weight_initialization, weight_initialization_gain=args.weight_initialization_gain)
        
        self.wv = nn.Linear(args.dim, args.n_heads * self.head_dim, bias=False)
        init_whole_model_weights(self.wv, args.weight_initialization, weight_initialization_gain=args.weight_initialization_gain)
        
        self.wo = nn.Linear(args.n_heads * self.head_dim, args.dim, bias=False)
        init_whole_model_weights(self.wo, args.weight_initialization, weight_initialization_gain=args.weight_initialization_gain)

    def forward(
        self,
        x: torch.Tensor,
        freqs_cis: torch.Tensor,
        mask: Optional[torch.Tensor],
        use_flash_attention: bool = False,
        causal: bool = False,
    ):
        """
        Forward pass of the attention module.

        Args:
            x (torch.Tensor): Input tensor.
            freqs_cis (torch.Tensor): Precomputed frequency tensor.
            mask (torch.Tensor, optional): Attention mask tensor.

        Returns:
            torch.Tensor: Output tensor after attention.

        # """
        bsz, full_seqlen, _ = x.shape # full_seqlen includes real embeds and pred embeds -> 2S
        seqlen = (full_seqlen)//2 # S
        xq, xk, xv = self.wq(x), self.wk(x), self.wv(x)

        xq = xq.view(bsz, full_seqlen, self.n_heads, self.head_dim)
        xk = xk.view(bsz, full_seqlen, self.n_kv_heads, self.head_dim)
        xv = xv.view(bsz, full_seqlen, self.n_kv_heads, self.head_dim)
        
        # _o is for original attention stuff
        xq_o = xq[:, :seqlen, :, :] #B, S, N, H
        xk_o = xk[:, :seqlen, :, :]
        xv_o = xv[:, :seqlen, :, :]
        
        # _p is for predicted attention stuff
        xq_p = xq[:, seqlen:, :, :] #B, S, N, H
        xk_p = xk[:, seqlen:, :, :]
        xv_p = xv[:, seqlen:, :, :]
        
        
        xq_o, xk_o = apply_rotary_emb(xq_o, xk_o, freqs_cis=freqs_cis[:seqlen])
        xq_p, xk_p = apply_rotary_emb(xq_p, xk_p, freqs_cis=freqs_cis[1:seqlen+1]) # use 2 since are the next preds and also have time embeddings and thus need to condition on two tokens        


        xq_o = xq_o.transpose(1, 2)  # (bs, n_local_heads, seqlen, head_dim)
        keys_o = xk_o.transpose(1, 2) # (bs, n_local_heads, seqlen, head_dim)
        values_o = xv_o.transpose(1, 2) # (bs, n_local_heads, seqlen, head_dim)

        xq_p = xq_p.transpose(1, 2)  # (bs, n_local_heads, seqlen, head_dim)
        keys_p = xk_p.transpose(1, 2) # (bs, n_local_heads, seqlen, head_dim)
        values_p = xv_p.transpose(1, 2) # (bs, n_local_heads, seqlen, head_dim)

        # Compute attention
        if use_flash_attention:
            output_o, output_p = ebt_attention(
                xq_o, keys_o, values_o,
                xq_p, keys_p, values_p,
                attn_mask=mask,
                causal=causal,
            )
        else:
            output_o, output_p = pytorch_ebt_attention(
                xq_o, keys_o, values_o,
                xq_p, keys_p, values_p,
                attn_mask=mask
            )

        output_o = output_o.transpose(1, 2).contiguous().view(bsz, seqlen, -1) # B, S, D
        output_p = output_p.transpose(1, 2).contiguous().view(bsz, seqlen, -1) # B, S, D
        
        #return linear projection of concatted outputs
        output = torch.cat((output_o, output_p), dim = 1) # B, 2S, D
        return self.wo(output)


class FeedForward(nn.Module):
    def __init__(
        self,
        dim: int,
        ffn_dim_multiplier: Optional[float],
        weight_initialization: str,
        ebt_act_func: str = "silu",
        weight_initialization_gain: float = 1.0
    ):
        super().__init__()
        hidden_dim = dim if ffn_dim_multiplier is None else int(dim*ffn_dim_multiplier)

        self.w1 = nn.Linear(dim, hidden_dim, bias=False)
        init_whole_model_weights(self.w1, weight_initialization, weight_initialization_gain=weight_initialization_gain)
        
        self.w2 = nn.Linear(hidden_dim, dim, bias=False)
        init_whole_model_weights(self.w2, weight_initialization, weight_initialization_gain=weight_initialization_gain)
        
        self.w3 = nn.Linear(dim, hidden_dim, bias=False)
        init_whole_model_weights(self.w3, weight_initialization, weight_initialization_gain=weight_initialization_gain)

        self.act_func = {
            "silu": F.silu,
            "relu": F.relu,
            "gelu": F.gelu,
            "elu": F.elu
        }[ebt_act_func]

    def forward(self, x):
        return self.w2(self.act_func(self.w1(x)) * self.w3(x))


class TransformerBlock(nn.Module):
    def __init__(self, layer_id: int, args: EBTModelArgs):
        """
        Initialize a TransformerBlock.

        Args:
            layer_id (int): Identifier for the layer.
            args (EBTModelArgs): Model configuration parameters.

        Attributes:
            n_heads (int): Number of attention heads.
            dim (int): Dimension size of the model.
            head_dim (int): Dimension size of each attention head.
            attention (Attention): Attention module.
            feed_forward (FeedForward): FeedForward module.
            layer_id (int): Identifier for the layer.
            attention_norm (RMSNorm): Layer normalization for attention output.
            ffn_norm (RMSNorm): Layer normalization for feedforward output.

        """
        super().__init__()
        self.n_heads = args.n_heads
        self.dim = args.dim
        self.head_dim = args.dim // args.n_heads
        self.attention = Attention(args)
        self.feed_forward = FeedForward(
            dim=args.dim,
            ffn_dim_multiplier=args.ffn_dim_multiplier,
            weight_initialization=args.weight_initialization,
            ebt_act_func=args.ebt_act_func,
            weight_initialization_gain=args.weight_initialization_gain
        )
        self.layer_id = layer_id
        if args.ebt_norm == "rms":
            self.attention_norm = RMSNorm(args.dim, eps=args.norm_eps)
            self.ffn_norm = RMSNorm(args.dim, eps=args.norm_eps)
        elif args.ebt_norm == "layer":
            self.attention_norm = nn.LayerNorm(args.dim)
            self.ffn_norm = nn.LayerNorm(args.dim)
        elif args.ebt_norm == "none":
            self.attention_norm = nn.Identity()
            self.ffn_norm = nn.Identity()
        elif args.ebt_norm == "dyt":
            self.attention_norm = DyT(args.dim, alpha_init_value=args.dyt_alpha_init)
            self.ffn_norm = DyT(args.dim, alpha_init_value=args.dyt_alpha_init)
        else:
            raise ValueError(f"Invalid ebt_norm value: {args.ebt_norm}")

    def forward(
        self,
        x: torch.Tensor,
        freqs_cis: torch.Tensor,
        mask: Optional[torch.Tensor],
        use_flash_attention: bool = False,
        causal: bool = False,
    ):
        """
        Perform a forward pass through the TransformerBlock.

        Args:
            x (torch.Tensor): Input tensor.
            freqs_cis (torch.Tensor): Precomputed cosine and sine frequencies.
            mask (torch.Tensor, optional): Masking tensor for attention. Defaults to None.

        Returns:
            torch.Tensor: Output tensor after applying attention and feedforward layers.

        """
        # x has shape B, 2S, D
        h = x + self.attention(
            self.attention_norm(x), freqs_cis, mask, use_flash_attention, causal,
        )
        out = h + self.feed_forward(self.ffn_norm(h))
        return out


class EBT(nn.Module):
    def __init__(self, params: EBTModelArgs, max_mcmc_steps):
        """
        Initialize a Transformer model.

        Args:
            params (EBTModelArgs): Model configuration parameters.

        Attributes:
            params (EBTModelArgs): Model configuration parameters.
            n_layers (int): Number of layers in the model.
            layers (torch.nn.ModuleList): List of Transformer blocks.
            norm (RMSNorm): Layer normalization for the model output.
            output (ColumnParallelLinear): Linear layer for final output.
            freqs_cis (torch.Tensor): Precomputed cosine and sine frequencies.

        """
        super().__init__()
        self.params = params
        self.n_layers = params.n_layers

        self.layers = torch.nn.ModuleList()
        for layer_id in range(params.n_layers):
            self.layers.append(TransformerBlock(layer_id, params))

        if params.ebt_norm == "rms":
            self.norm = RMSNorm(params.dim, eps=params.norm_eps)
        elif params.ebt_norm == "layer":
            self.norm = nn.LayerNorm(params.dim)
        elif params.ebt_norm == "none":
            self.norm = nn.Identity()
        elif params.ebt_norm == "dyt":
            self.norm = DyT(params.dim, alpha_init_value=params.dyt_alpha_init, bias_learnable=False) # no learnable bias here since grad cant be computed for a final bias term in EBT
        else:
            raise ValueError(f"Invalid ebt_norm value: {params.ebt_norm}")

        self.freqs_cis = precompute_freqs_cis(
            self.params.dim // self.params.n_heads, self.params.max_seq_len
        )

        self.time_embeddings = nn.Embedding(max_mcmc_steps, params.dim)

        self.final_layer = nn.Linear(params.dim, 1, bias=False)
        init_whole_model_weights(self.final_layer, self.params.weight_initialization)

    def forward(self, embeddings: torch.Tensor, mcmc_step = 0, use_flash_attention: bool = False, causal: bool = False, mask_type: str = "boolean"):
        """
        Perform a forward pass through the Transformer model.

        Args:
            embeds (torch.Tensor): Embeddings (instead of tokens since is for vision).
            mcmc_step (int): Current MCMC step. Defaults to 0.
            use_flash_attention (bool): Whether to use flash attention. Defaults to False.

        Returns:
            torch.Tensor: Output energies after applying the Transformer model.

        """
        assert mask_type in ["boolean", "additive", None], "mask_type must be either 'boolean', 'additive', or None"
        _bsz, seqlen = embeddings.shape[:2]
        mcmc_step = torch.full(size=(_bsz,), fill_value=mcmc_step, device=embeddings.device, dtype=torch.long)
        time_embeddings = self.time_embeddings(mcmc_step).unsqueeze(dim=1) # needs to be expanded to B, 1, D
        embeddings = embeddings + time_embeddings # B, 2S, D
        
        seqlen = (seqlen+2) // 2 # do this since passed in seqlen is 2S so add 2 div 2 = S+1 which corresponds to concatting pred & next pred
        self.freqs_cis = self.freqs_cis.to(embeddings.device)
        freqs_cis = self.freqs_cis[:seqlen]

        mask = None
        if seqlen > 1:
            if mask_type == "boolean":
                mask = torch.tril(
                    torch.ones((seqlen, seqlen), device=embeddings.device, dtype=torch.bool))
            elif mask_type == "additive":
                mask = torch.full(
                    (seqlen, seqlen), MASK_CONST, device=embeddings.device
                )
                mask = torch.triu(mask, diagonal=1)

        for i, layer in enumerate(self.layers):
            embeddings = layer(embeddings, freqs_cis, mask, use_flash_attention, causal)
        embeddings = self.norm(embeddings)
        energies = self.final_layer(embeddings)

        energies = energies[:, embeddings.shape[1] // 2:]
        return energies