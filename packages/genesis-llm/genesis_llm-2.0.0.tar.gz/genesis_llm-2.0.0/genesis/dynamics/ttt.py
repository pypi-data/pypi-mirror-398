"""
Test-Time Training for Genesis - OPTIMIZED
==========================================

Parallel TTT using mini-batch processing and dual form.

Key Innovation: Instead of sequential per-token updates,
process tokens in mini-batches with matrix operations.

Based on: "Learning to (Learn at Test Time)" (Sun et al., 2024)
Reference: https://github.com/test-time-training/ttt-lm-pytorch

Optimizations:
- Mini-batch TTT (parallel over tokens)
- Dual form for efficient gradient computation
- Low-rank updates for memory efficiency
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple, Dict
from dataclasses import dataclass


@dataclass
class TTTMetrics:
    """Metrics from TTT forward pass."""
    reconstruction_loss: float = 0.0
    gradient_norm: float = 0.0
    state_change: float = 0.0
    learning_rate: float = 0.0
    activated: bool = False


class TTTLayer(nn.Module):
    """
    Test-Time Training Layer - OPTIMIZED with dual form.
    
    Two computation modes:
    - "minibatch": Process tokens in chunks (good balance)
    - "dual": Fully parallel dual form (fastest, per TTT paper)
    
    The dual form computes gradients in closed form for linear models,
    enabling full parallelization across the sequence.
    
    Based on: "Learning to (Learn at Test Time)" (Sun et al., 2024)
    """
    
    def __init__(
        self,
        n_embd: int,
        inner_lr: float = 0.1,
        rank: int = 8,
        corruption_rate: float = 0.3,
        mini_batch_size: int = 16,
        mode: str = "dual",  # "dual" or "minibatch"
        lr_cap: Optional[float] = None,
        inference_fast_path: bool = True,
    ):
        super().__init__()
        self.n_embd = n_embd
        self.inner_lr = inner_lr
        self.rank = rank
        self.corruption_rate = corruption_rate
        self.mini_batch_size = mini_batch_size
        self.mode = mode
        self.lr_cap = lr_cap
        self.inference_fast_path = inference_fast_path
        
        # Initial W for the inner linear model (low-rank for efficiency)
        # W = W0 + A @ B where A: [n_embd, rank], B: [rank, n_embd]
        self.W0 = nn.Parameter(torch.eye(n_embd) * 0.1)
        self.A_init = nn.Parameter(torch.randn(n_embd, rank) * 0.01)
        self.B_init = nn.Parameter(torch.zeros(rank, n_embd))
        
        # Learnable learning rate (per-dimension)
        self.log_lr = nn.Parameter(torch.ones(n_embd) * math.log(inner_lr))
        
        # Input/output projections (Q, K, V style for dual form)
        self.q_proj = nn.Linear(n_embd, n_embd, bias=False)
        self.k_proj = nn.Linear(n_embd, n_embd, bias=False)
        self.v_proj = nn.Linear(n_embd, n_embd, bias=False)
        self.out_proj = nn.Linear(n_embd, n_embd, bias=False)
        
        # Layer norm for stability
        self.norm = nn.LayerNorm(n_embd)
        
        # Output gate
        self.output_gate = nn.Linear(n_embd, n_embd, bias=False)
        
        # LayerScale for training stability (Going Deeper with Image Transformers)
        # Initialize to small value - allows gradual contribution increase
        from ..layers.norms import LayerScale
        self.layer_scale = LayerScale(n_embd, init_value=1e-4)
        
        self.last_metrics: Optional[TTTMetrics] = None
        
    def _dual_form_forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Improved dual form TTT - closer to MIT paper (arXiv:2407.04620).
        
        The dual form insight: For a linear model with squared loss,
        the optimal weights after seeing t examples can be computed as:
        W_t = W_0 - lr * sum_{i<t} (K_i^T @ error_i)
        
        This can be parallelized using cumulative sums.
        
        Key improvement over previous version:
        - Use proper causal cumsum for gradient accumulation
        - Better scaling based on FLA/linear attention research
        - More stable inter/intra chunk combination
        """
        B, T, C = x.shape
        
        if (not self.training) and self.inference_fast_path:
            Q = x
            K = x
            V = x
        else:
            Q = self.q_proj(x)
            K = self.k_proj(x)
            V = self.v_proj(x)
        
        lr = torch.exp(self.log_lr)
        if self.lr_cap is not None:
            lr = lr.clamp(max=float(self.lr_cap))
        else:
            lr = lr.clamp(max=1.0)
        
        diag = torch.diagonal(self.W0, 0)
        offdiag_max = (self.W0 - torch.diag_embed(diag)).abs().max()
        if (not self.training) and offdiag_max.item() < 1e-6:
            y0 = K * diag.view(1, 1, -1)
        else:
            y0 = torch.matmul(K, self.W0)
        
        y0 = y0 + torch.matmul(torch.matmul(K, self.A_init), self.B_init)
        
        error = y0 - V
        
        # === IMPROVED DUAL FORM ===
        # Use causal cumulative sum for proper TTT dynamics
        # gradient_t = K_t * error_t (element-wise for diagonal approximation)
        # cumsum_t = sum_{i<t} gradient_i
        # correction_t = Q_t * lr * cumsum_t
        
        Kf = K.float()
        Qf = Q.float()
        error_f = error.float()
        
        gradient = Kf * error_f
        
        # Causal cumulative sum: each position sees sum of all previous gradients
        # Shift by 1 to ensure position t only sees gradients from positions < t
        grad_cumsum = torch.cumsum(gradient, dim=1)
        # Shift: position t should use cumsum up to t-1
        grad_cumsum_shifted = torch.cat([
            torch.zeros(B, 1, C, device=x.device, dtype=grad_cumsum.dtype),
            grad_cumsum[:, :-1, :]
        ], dim=1)
        
        # Apply correction: Q * lr * cumsum (element-wise)
        correction = Qf * lr.view(1, 1, -1).float() * grad_cumsum_shifted
        
        # Scale correction for numerical stability (based on sequence position)
        # Later positions have more accumulated gradients, need dampening
        position_scale = torch.arange(1, T + 1, device=x.device, dtype=correction.dtype)
        position_scale = 1.0 / (1.0 + 0.1 * torch.log(position_scale))
        position_scale = position_scale.view(1, -1, 1)
        correction = correction * position_scale
        
        # Output: initial prediction minus learned correction
        output = y0.float() - correction
        
        return output.to(dtype=x.dtype), error_f.pow(2).mean()
    
    def _minibatch_forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, float]:
        """Mini-batch TTT forward (original implementation)."""
        B, T, C = x.shape
        device = x.device
        dtype = x.dtype
        
        # Use Q proj as input proj for compatibility
        h = self.q_proj(x)
        
        # Initialize W for each batch (low-rank)
        W = (self.W0 + self.A_init @ self.B_init).unsqueeze(0).expand(B, -1, -1).clone()
        
        # Learning rate
        lr = torch.exp(self.log_lr)
        
        mb_size = self.mini_batch_size
        n_batches = (T + mb_size - 1) // mb_size
        
        outputs = []
        total_loss = 0.0
        
        for mb_idx in range(n_batches):
            start = mb_idx * mb_size
            end = min(start + mb_size, T)
            
            h_mb = h[:, start:end]
            mb_len = end - start
            
            # Corruption
            if self.training:
                mask = torch.bernoulli(torch.ones_like(h_mb) * self.corruption_rate)
                h_corrupted = h_mb * (1 - mask)
            else:
                h_corrupted = h_mb.clone()
                h_corrupted[..., ::3] = 0
            
            h_target = h_mb
            
            # Forward and gradient
            y = torch.bmm(h_corrupted, W)
            error = y - h_target
            grad_W = torch.bmm(h_corrupted.transpose(-2, -1), error) / mb_len
            
            # Update
            W = W - lr.view(1, -1, 1) * grad_W
            
            total_loss += error.pow(2).mean().item()
            
            # Output
            out_mb = torch.bmm(h_mb, W)
            outputs.append(out_mb)
        
        output = torch.cat(outputs, dim=1)
        return output, total_loss / n_batches
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, TTTMetrics]:
        """
        Forward with TTT - supports dual form and minibatch modes.
        """
        B, T, C = x.shape
        
        # Normalize input
        h = self.norm(x)
        
        # Choose computation mode
        if self.mode == "dual":
            output, loss = self._dual_form_forward(h)
        else:
            output, loss = self._minibatch_forward(h)
        
        # Output gating
        gate = torch.sigmoid(self.output_gate(x))
        output = output * gate
        
        # Project output
        output = self.out_proj(output)
        
        # Apply LayerScale before residual (training stability)
        output = self.layer_scale(output)
        
        # Residual connection
        output = x + output
        
        # Learning rate for metrics
        lr = torch.exp(self.log_lr)
        
        self.last_metrics = TTTMetrics(
            reconstruction_loss=loss if isinstance(loss, float) else loss.item(),
            gradient_norm=0.0,  # Not tracked in dual form
            state_change=0.0,
            learning_rate=lr.mean().item(),
            activated=True,
        )
        
        return output, self.last_metrics


class GenesisMetacognition(nn.Module):
    """
    Genesis Metacognition - Self-aware computation.
    
    The model:
    1. Predicts its own future state
    2. Measures surprise (prediction error)
    3. Adjusts confidence based on surprise
    4. Learns from mistakes in real-time (TTT)
    
    This implements true recursive self-awareness.
    """
    
    def __init__(
        self,
        n_embd: int,
        rank: int = 8,
        surprise_threshold: float = 0.5,
        inner_lr: float = 0.01,
        mode: str = "dual",
        lr_cap: Optional[float] = None,
        inference_fast_path: bool = True,
    ):
        super().__init__()
        self.n_embd = n_embd
        self.surprise_threshold = surprise_threshold
        
        # Self-model: predicts own state
        self.self_model = nn.Linear(n_embd, n_embd, bias=False)
        
        self.ttt = TTTLayer(
            n_embd,
            inner_lr=inner_lr,
            rank=rank,
            mode=mode,
            lr_cap=lr_cap,
            inference_fast_path=inference_fast_path,
        )
        
        # Confidence estimator
        self.confidence = nn.Sequential(
            nn.Linear(n_embd * 2, n_embd // 2),
            nn.SiLU(),
            nn.Linear(n_embd // 2, 1),
            nn.Sigmoid(),
        )
        
        # Reflection generator
        self.reflection = nn.Linear(n_embd * 2, n_embd, bias=False)
        
        # Track self-evolution
        self.register_buffer('evolution_history', torch.zeros(100))
        self.register_buffer('evolution_idx', torch.tensor(0))
        
        self.last_metrics: Optional[Dict] = None
        
    def forward(
        self,
        x: torch.Tensor,
    ) -> Tuple[torch.Tensor, torch.Tensor, Dict]:
        """
        Forward with metacognition.
        
        Returns:
            output: adapted representation
            reflection: metacognitive insight
            metrics: self-awareness data
        """
        B, T, _ = x.shape
        
        # Self-prediction: what do I expect?
        expected = self.self_model(x)
        
        # TTT processing: adapt to actual input
        adapted, ttt_metrics = self.ttt(x)
        
        # Surprise: how different from expectation?
        surprise = F.mse_loss(expected, adapted, reduction='none').mean(dim=-1)
        
        # High surprise → activate deeper processing
        high_surprise = (surprise > self.surprise_threshold).float()
        
        # Confidence: based on surprise level
        combined = torch.cat([expected, adapted], dim=-1)
        conf = self.confidence(combined).squeeze(-1)
        
        # Reflection: understanding the discrepancy
        reflection = self.reflection(combined)
        
        # v2.4.3: Return raw adapted instead of mixing here
        # Mixing will be handled in model.py for better control
        output = adapted
        
        # Metrics - capture_scalar_outputs=True permite .item()
        with torch.no_grad():
            idx = int(self.evolution_idx) % 100
            self.evolution_history[idx] = surprise.mean()
            self.evolution_idx += 1
        
        self.last_metrics = {
            'surprise': surprise.mean().item(),
            'confidence': conf.mean().item(),
            'high_surprise_ratio': high_surprise.mean().item(),
            'ttt_loss': ttt_metrics.reconstruction_loss,
            'evolution_trend': self.evolution_history[:min(idx+1, 100)].mean().item(),
        }
        
        return output, reflection, self.last_metrics
    
    def get_self_analysis(self) -> Dict:
        """Analyze self-evolution patterns."""
        idx = min(int(self.evolution_idx), 100)
        history = self.evolution_history[:idx]
        
        if idx < 5:
            return {'status': 'insufficient_data'}
        
        # Analyze trends
        recent = history[-10:] if idx > 10 else history
        early = history[:10] if idx > 10 else history
        
        return {
            'mean_surprise': history.mean().item(),
            'recent_surprise': recent.mean().item(),
            'improvement': (early.mean() - recent.mean()).item(),
            'stability': 1.0 / (history.std().item() + 1e-6),
            'total_observations': idx,
        }
