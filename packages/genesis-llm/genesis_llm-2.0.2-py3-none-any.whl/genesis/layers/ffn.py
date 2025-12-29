"""
Feed-Forward Networks for Genesis
=================================

SwiGLU with Selective Activation for efficient LLMs.

v2.0.0: CLEANUP - Removed MoE/ExpertFFN (overhead > benefit at <1B scale)
v0.8.3: Added Selective Activation (Top-k sparsity with annealed schedule)
v0.8.0: Removed KAN (research shows SwiGLU is better for NLP)

References:
- ReLU Strikes Back (Apple, ICLR 2024): Activation sparsity for inference
- CHESS (2024): Channel-wise thresholding for LLM acceleration
- ProSparse (2025): Intrinsic activation sparsity enhancement
- Spark Transformer (Google, 2025): Shows real speedup requires sparse kernels

⚠️ IMPORTANT: Selective Activation Limitations (v2.1.0)
========================================================
The current implementation does NOT provide real GPU speedup:

1. Dense GEMMs still execute fully:
   - gate_proj(x) and up_proj(x) run as complete dense matmuls
   - Mask is applied AFTER computation: `hidden = hidden * mask`
   - down_proj(hidden) also runs as dense (zeros don't skip compute)

2. May SLOW DOWN training:
   - torch.kthvalue/topk adds overhead
   - Breaks torch.compile kernel fusion
   - Spark paper: "standard top-k leads to >10x slowdown"

3. Use case: REGULARIZATION only
   - Acts as learned dropout/pruning during training
   - Zero speedup at inference (mask disabled in eval mode)
   - For real speedup, need: N:M sparsity, Spark-style predictors, or sparse kernels

To get actual speedup, consider:
- Structured N:M sparsity with NVIDIA Ampere+ (2:4 pattern)
- Spark Transformer architecture (low-rank predictor + sparse GEMM)
- Post-training pruning + sparse inference engines
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Callable


# =============================================================================
# Selective Activation Functions (v0.8.3)
# =============================================================================

def topk_mask(x: torch.Tensor, k_ratio: float) -> torch.Tensor:
    """
    Create a mask that keeps only top-k% activations by magnitude.
    
    Args:
        x: activation tensor [..., hidden_dim]
        k_ratio: fraction of activations to keep (0.0 to 1.0)
        
    Returns:
        mask: binary mask of same shape as x
    """
    if k_ratio >= 1.0:
        return torch.ones_like(x)
    if k_ratio <= 0.0:
        return torch.zeros_like(x)
    
    # Get k for this tensor
    hidden_dim = x.shape[-1]
    k = max(1, int(hidden_dim * k_ratio))
    
    # Top-k by magnitude
    abs_x = x.abs()
    _, topk_indices = torch.topk(abs_x, k, dim=-1)
    
    # Create mask
    mask = torch.zeros_like(x)
    mask.scatter_(-1, topk_indices, 1.0)
    
    return mask


def soft_topk_mask(x: torch.Tensor, k_ratio: float, temperature: float = 1.0) -> torch.Tensor:
    """
    Soft top-k mask using sigmoid (differentiable approximation).
    
    Instead of hard threshold, uses sigmoid to create smooth mask.
    Better gradient flow during training.
    
    Args:
        x: activation tensor [..., hidden_dim]
        k_ratio: fraction of activations to keep (0.0 to 1.0)
        temperature: sharpness of the mask (lower = sharper)
        
    Returns:
        soft_mask: values between 0 and 1
    """
    if k_ratio >= 1.0:
        return torch.ones_like(x)
    
    abs_x = x.abs()
    
    # Compute threshold as the k-th percentile
    hidden_dim = x.shape[-1]
    k = max(1, int(hidden_dim * k_ratio))
    
    # Get the k-th largest value as threshold
    threshold = torch.kthvalue(abs_x, hidden_dim - k + 1, dim=-1, keepdim=True).values
    
    # Soft mask using sigmoid
    # Values above threshold -> 1, below -> 0 (smoothly)
    soft_mask = torch.sigmoid((abs_x - threshold) / (temperature + 1e-8))
    
    return soft_mask


class SparsityScheduler:
    """
    Annealed sparsity schedule for gradual sparsification.
    
    Starts with dense (k=1.0) and gradually reduces to target sparsity.
    This allows the model to learn which neurons are important before pruning.
    
    Based on: Gradual Magnitude Pruning (Zhu & Gupta, 2017)
    """
    
    def __init__(
        self,
        initial_k: float = 1.0,      # Start fully dense
        final_k: float = 0.5,        # Target 50% activation
        warmup_steps: int = 1000,    # Steps before sparsification starts
        sparsify_steps: int = 10000, # Steps to reach final sparsity
        schedule: str = "cubic",     # cubic, linear, or cosine
    ):
        self.initial_k = initial_k
        self.final_k = final_k
        self.warmup_steps = warmup_steps
        self.sparsify_steps = sparsify_steps
        self.schedule = schedule
        self._current_step = 0
        
    def step(self):
        """Advance one step."""
        self._current_step += 1
        
    def set_step(self, step: int):
        """Set current step directly."""
        self._current_step = step
        
    def freeze(self):
        """
        Freeze sparsity at current level.
        
        Call this when LR enters decay phase to preserve capacity.
        Reference: N:M Sparse Training (ICML 2022)
        """
        self._frozen = True
        self._frozen_k = self.get_k()
    
    def unfreeze(self):
        """Unfreeze sparsity schedule."""
        self._frozen = False
    
    def get_k(self) -> float:
        """Get current k ratio based on schedule."""
        # If frozen, return frozen value
        if getattr(self, '_frozen', False):
            return getattr(self, '_frozen_k', self.final_k)
        
        step = self._current_step
        
        # Warmup phase: fully dense
        if step < self.warmup_steps:
            return self.initial_k
        
        # Sparsification phase
        sparsify_step = step - self.warmup_steps
        if sparsify_step >= self.sparsify_steps:
            return self.final_k
        
        # Progress through sparsification (0 to 1)
        progress = sparsify_step / self.sparsify_steps
        
        # Apply schedule
        if self.schedule == "linear":
            factor = progress
        elif self.schedule == "cosine":
            factor = 0.5 * (1 - math.cos(math.pi * progress))
        elif self.schedule == "cubic":
            # Cubic: slow start, fast middle, slow end (recommended)
            factor = 1 - (1 - progress) ** 3
        else:
            factor = progress
        
        # Interpolate between initial and final k
        k = self.initial_k - (self.initial_k - self.final_k) * factor
        return k


class SwiGLU(nn.Module):
    """
    SwiGLU activation with linear projections.
    
    SwiGLU(x) = Swish(W_gate @ x) * (W_up @ x)
    
    Used in: LLaMA, Mistral, PaLM, and most modern LLMs.
    More expressive than simple ReLU/GELU.
    
    v0.8.3: Added Selective Activation (Top-k sparsity)
    - Keeps only top-k% neurons by magnitude after activation
    - Gradients still flow through selected neurons (STE or soft mask)
    
    ⚠️ v2.1.0 CLARIFICATION: Selective Activation is for REGULARIZATION, not speedup.
    - Dense GEMMs still run fully (no compute savings on GPU)
    - Only active during training (self.training check)
    - Use as learned sparsity/dropout, not efficiency feature
    - See module docstring for alternatives that provide real speedup
    
    Args:
        use_selective_activation: Enable top-k sparsity (regularization only)
        k_ratio: Fraction of neurons to keep (0.0-1.0), or callable that returns k
        use_soft_mask: Use differentiable soft mask instead of hard threshold
        mask_temperature: Temperature for soft mask (lower = sharper)
    """
    
    def __init__(
        self,
        in_features: int,
        hidden_features: int,
        out_features: Optional[int] = None,
        bias: bool = False,
        dropout: float = 0.0,
        use_selective_activation: bool = False,
        k_ratio: float = 0.5,
        use_soft_mask: bool = True,
        mask_temperature: float = 0.1,
        selective_activation_in_eval: bool = False,  # DEPRECATED: kept for backward compatibility
    ):
        super().__init__()
        out_features = out_features or in_features
        
        self.gate_proj = nn.Linear(in_features, hidden_features, bias=bias)
        self.up_proj = nn.Linear(in_features, hidden_features, bias=bias)
        self.down_proj = nn.Linear(hidden_features, out_features, bias=bias)
        self.dropout = nn.Dropout(dropout)
        
        # Selective activation config
        # v2.4.5: SA now always active when use_selective_activation=True
        # selective_activation_in_eval is deprecated but kept for backward compatibility
        self.use_selective_activation = use_selective_activation
        self._k_ratio = k_ratio
        self.use_soft_mask = use_soft_mask
        self.mask_temperature = mask_temperature
        
        # For metrics
        self._last_sparsity = 0.0
        
    @property
    def k_ratio(self) -> float:
        """Get current k ratio (supports callable for scheduled sparsity)."""
        if callable(self._k_ratio):
            return self._k_ratio()
        return self._k_ratio
    
    def set_k_ratio(self, k: float):
        """Set k ratio directly."""
        self._k_ratio = k
        
    def set_k_scheduler(self, scheduler: 'SparsityScheduler'):
        """Set a sparsity scheduler for annealed sparsity."""
        self._k_ratio = scheduler.get_k
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        gate = F.silu(self.gate_proj(x))
        up = self.up_proj(x)
        hidden = gate * up
        
        # Selective activation: keep only top-k% neurons by magnitude
        # v2.4.5: SA only active during INFERENCE (not training)
        # SA is designed for inference efficiency, so it should NOT run during training
        if self.use_selective_activation and not self.training:
            k = self.k_ratio
            if k < 1.0:
                hidden_for_mask = hidden.float()
                mask = topk_mask(hidden_for_mask, k)
                mask = mask.to(dtype=hidden.dtype)
                hidden = hidden * mask
                
                # Track sparsity for metrics
                with torch.no_grad():
                    self._last_sparsity = 1.0 - (mask > 0.5).float().mean().item()
        
        return self.dropout(self.down_proj(hidden))


# =============================================================================
# REMOVED: ExpertFFN and GatedExpertMoE (v2.0.0 cleanup)
# =============================================================================
# These were removed because:
# - MoE overhead > benefit at <1B scale (proven in Shakespeare tests)
# - "Efficiency First" principle: keep only what's validated
# - For future scaling to 1B+, these can be re-added from git history
# =============================================================================
