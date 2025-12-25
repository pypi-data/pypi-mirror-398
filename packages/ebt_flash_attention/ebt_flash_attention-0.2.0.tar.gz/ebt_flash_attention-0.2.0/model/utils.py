from typing import Optional
from dataclasses import dataclass
from torch import nn


@dataclass
class EBTModelArgs:
    dim: int = 768
    n_layers: int = 12
    n_heads: int = 12
    n_kv_heads: Optional[int] = None
    ffn_dim_multiplier: Optional[float] = None
    norm_eps: float = 1e-5
    dyt_alpha_init: float = 0.5
    max_batch_size: int = 64
    max_seq_len: int = 16
    weight_initialization: str = "xavier"
    ebt_norm: str = "rms"
    ebt_act_func: str = "silu"
    weight_initialization_gain: float = 1.0

model_sizes = {
    "tiny": { # LR 0.0012
        "num_transformer_blocks": 6,
        "multiheaded_attention_heads": 6,
        "embedding_dim": 384,
    },
    "small": { # LR 0.0006
        "num_transformer_blocks": 12,
        "multiheaded_attention_heads": 12,
        "embedding_dim": 768,
    },
    "base": { # 0.0003
        "num_transformer_blocks": 24,
        "multiheaded_attention_heads": 16,
        "embedding_dim": 1024,
    },
}

def init_whole_model_weights(model, weight_initialization_method, nonlinearity='linear', weight_initialization_gain=1.0):
    def init_weights(m):
        if isinstance(m, nn.Linear):
            if weight_initialization_method == "he":
                valid_nonlinearities = ['linear', 'relu', 'leaky_relu', 'selu', 'tanh']
                if nonlinearity not in valid_nonlinearities:
                    raise ValueError(f"Unsupported nonlinearity: {nonlinearity}. Must be one of {valid_nonlinearities}")
                
                nn.init.kaiming_normal_(m.weight, nonlinearity=nonlinearity)
                if weight_initialization_gain != 1.0:
                    m.weight.data *= weight_initialization_gain
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0.)
            elif weight_initialization_method == "xavier":
                nn.init.xavier_normal_(m.weight)
                if weight_initialization_gain != 1.0:
                    m.weight.data *= weight_initialization_gain
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0.)
            else:
                raise ValueError(f"Unknown weight init method: {weight_initialization_method}")
    
    model.apply(init_weights)