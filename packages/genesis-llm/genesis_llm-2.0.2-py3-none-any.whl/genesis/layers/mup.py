"""
µP (Maximal Update Parametrization) - Genesis Implementation
=============================================================

Based on: "Tensor Programs V: Tuning Large Neural Networks via Zero-Shot
Hyperparameter Transfer" (NeurIPS 2021, Microsoft/EleutherAI)

Key Benefits:
- Optimal HPs transfer from small proxy to large model
- 2x compute savings (tune 40M, use on 1B)
- More stable training at scale
- Better scaling law fits

Implementation follows nanoGPT-mup (EleutherAI):
https://github.com/EleutherAI/nanoGPT-mup

Usage:
1. Train a small "proxy" model with base_width (e.g., 256)
2. Find optimal HPs on proxy
3. Scale up n_embd while keeping base_width fixed
4. µP ensures HPs transfer automatically

Key Formulas:
- Width multiplier: m_d = n_embd / base_width
- Hidden layer init: σ = 1 / √m_d
- Hidden layer LR: η_hidden = η_base / m_d  
- Output layer LR: η_output = η_base / m_d
- Embedding LR: η_embed = η_base (unchanged)
"""

import math
import torch
import torch.nn as nn
from typing import Dict, List, Optional, Set


def get_mup_param_groups(
    model: nn.Module,
    base_width: int,
    actual_width: int,
    base_lr: float,
    weight_decay: float = 0.0,
    no_decay_names: Optional[Set[str]] = None,
) -> List[Dict]:
    """
    Create parameter groups with µP-adjusted learning rates.
    
    Args:
        model: The Genesis model
        base_width: Width of the proxy model used for HP tuning
        actual_width: Actual model width (n_embd)
        base_lr: Base learning rate (tuned on proxy model)
        weight_decay: Weight decay coefficient
        no_decay_names: Set of parameter name patterns that should not have weight decay
        
    Returns:
        List of parameter groups for optimizer
    """
    if no_decay_names is None:
        no_decay_names = {'bias', 'norm', 'layernorm', 'rmsnorm', 'ln_'}
    
    # Width multiplier
    m_d = actual_width / base_width
    
    # Categorize parameters
    embed_params = []      # Embeddings: no LR scaling
    hidden_params = []     # Hidden layers: LR / m_d
    output_params = []     # Output projection: LR / m_d
    no_decay_params = []   # Parameters without weight decay
    
    for name, param in model.named_parameters():
        if not param.requires_grad:
            continue
            
        # Check if this param should skip weight decay
        skip_decay = any(nd in name.lower() for nd in no_decay_names)
        
        # Categorize by layer type
        if 'wte' in name or 'tok_emb' in name or 'embed' in name.lower():
            # Embeddings: standard LR
            if skip_decay:
                no_decay_params.append(param)
            else:
                embed_params.append(param)
        elif 'lm_head' in name or 'wpe' in name or name.endswith('.weight') and 'proj' not in name:
            # Output/position embeddings: scaled LR
            if skip_decay:
                no_decay_params.append(param)
            else:
                output_params.append(param)
        else:
            # Hidden layers: scaled LR
            if skip_decay:
                no_decay_params.append(param)
            else:
                hidden_params.append(param)
    
    # Create parameter groups
    param_groups = []
    
    # Embedding params: base LR, with decay
    if embed_params:
        param_groups.append({
            'params': embed_params,
            'lr': base_lr,
            'weight_decay': weight_decay,
            'mup_type': 'embed',
        })
    
    # Hidden params: scaled LR, with decay  
    if hidden_params:
        param_groups.append({
            'params': hidden_params,
            'lr': base_lr / m_d,
            'weight_decay': weight_decay,
            'mup_type': 'hidden',
        })
    
    # Output params: scaled LR, with decay
    if output_params:
        param_groups.append({
            'params': output_params,
            'lr': base_lr / m_d,
            'weight_decay': weight_decay,
            'mup_type': 'output',
        })
    
    # No decay params: various LRs depending on layer
    if no_decay_params:
        param_groups.append({
            'params': no_decay_params,
            'lr': base_lr / m_d,  # Use scaled LR as default
            'weight_decay': 0.0,
            'mup_type': 'no_decay',
        })
    
    return param_groups


def mup_init_(
    model: nn.Module,
    base_width: int,
    actual_width: int,
    init_std: float = 0.02,
):
    """
    Apply µP initialization to model parameters.
    
    Hidden layer weights are initialized with σ = init_std / √m_d
    to ensure controlled activation magnitudes across widths.
    
    Args:
        model: The Genesis model
        base_width: Width of the proxy model
        actual_width: Actual model width (n_embd)
        init_std: Base initialization std (default: 0.02)
    """
    m_d = actual_width / base_width
    scaled_std = init_std / math.sqrt(m_d)
    
    for name, param in model.named_parameters():
        if param.dim() < 2:
            # Biases and 1D params: standard init
            continue
            
        if 'wte' in name or 'tok_emb' in name or 'embed' in name.lower():
            # Embeddings: standard init
            nn.init.normal_(param, mean=0.0, std=init_std)
        elif 'lm_head' in name:
            # Output projection: zero init (following GPT-2)
            nn.init.zeros_(param)
        else:
            # Hidden layers: scaled init
            nn.init.normal_(param, mean=0.0, std=scaled_std)


def get_mup_info(base_width: int, actual_width: int) -> Dict:
    """
    Get µP configuration info for logging/debugging.
    
    Args:
        base_width: Width of the proxy model
        actual_width: Actual model width
        
    Returns:
        Dictionary with µP configuration details
    """
    m_d = actual_width / base_width
    
    return {
        'base_width': base_width,
        'actual_width': actual_width,
        'width_multiplier': m_d,
        'lr_scale_hidden': 1.0 / m_d,
        'init_scale': 1.0 / math.sqrt(m_d),
        'is_proxy': m_d == 1.0,
    }


class MuReadout(nn.Linear):
    """
    µP-aware output layer that scales logits by 1/m_d.
    
    This ensures that the output magnitude remains constant
    as model width increases, enabling HP transfer.
    """
    
    def __init__(
        self,
        in_features: int,
        out_features: int,
        bias: bool = True,
        base_width: int = 256,
    ):
        super().__init__(in_features, out_features, bias)
        self.base_width = base_width
        self._width_mult = in_features / base_width
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Scale output by 1/width_mult to maintain magnitude
        return super().forward(x) / self._width_mult


def configure_mup_optimizer(
    model: nn.Module,
    config,
    base_lr: float,
    weight_decay: float = 0.1,
    betas: tuple = (0.9, 0.95),
) -> torch.optim.AdamW:
    """
    Configure AdamW optimizer with µP parameter groups.
    
    This is a convenience function that creates the optimizer
    with proper µP learning rate scaling.
    
    Args:
        model: Genesis model
        config: GenesisConfig with mup settings
        base_lr: Base learning rate (from proxy model tuning)
        weight_decay: Weight decay coefficient
        betas: Adam betas
        
    Returns:
        Configured AdamW optimizer
    """
    if not getattr(config, 'use_mup', False):
        # Standard optimizer without µP
        decay_params = []
        no_decay_params = []
        
        for name, param in model.named_parameters():
            if not param.requires_grad:
                continue
            if 'bias' in name or 'norm' in name.lower():
                no_decay_params.append(param)
            else:
                decay_params.append(param)
        
        param_groups = [
            {'params': decay_params, 'weight_decay': weight_decay},
            {'params': no_decay_params, 'weight_decay': 0.0},
        ]
        
        return torch.optim.AdamW(param_groups, lr=base_lr, betas=betas)
    
    # µP optimizer
    base_width = getattr(config, 'mup_base_width', 256)
    actual_width = config.n_embd
    
    param_groups = get_mup_param_groups(
        model,
        base_width=base_width,
        actual_width=actual_width,
        base_lr=base_lr,
        weight_decay=weight_decay,
    )
    
    return torch.optim.AdamW(param_groups, betas=betas)
