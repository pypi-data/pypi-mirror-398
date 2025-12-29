"""
Forgetting Attention (FoX) v2.2.0
=================================

Softmax attention with a data-dependent forget gate.

Based on: "Forgetting Transformer" (ICLR 2025)
Paper: https://arxiv.org/abs/2503.02130

v2.2.0: fla-org/flash-linear-attention integration
- Uses Triton kernels from fla.ops.forgetting_attn when available
- Falls back to SDPA (slower) if fla not installed
- Install: pip install git+https://github.com/fla-org/flash-linear-attention

Features:
- Forget gate as attn_mask (additive bias)
- Pro design: output gate, QK-norm, short convolutions
- NoPE: No positional embeddings (forget gate provides implicit position)
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple
from dataclasses import dataclass

from ..layers.norms import RMSNorm, FusedRMSNormSwishGate

# Try to import fla-org Triton kernels for FoX
FLA_FOX_AVAILABLE = False
try:
    from fla.ops.forgetting_attn.parallel import parallel_forgetting_attn
    FLA_FOX_AVAILABLE = True
except ImportError:
    pass


@dataclass
class FoXMetrics:
    """Metrics from FoX forward pass."""
    avg_forget_gate: float = 0.0
    attention_entropy: float = 0.0
    effective_context: float = 0.0


class ShortConvolution(nn.Module):
    """
    Short 1D convolution for K/V shifting (FoX Pro design).
    
    Provides local context aggregation before attention.
    """
    
    def __init__(
        self,
        hidden_size: int,
        kernel_size: int = 4,
        groups: Optional[int] = None,
    ):
        super().__init__()
        self.hidden_size = hidden_size
        self.kernel_size = kernel_size
        groups = groups or hidden_size  # Depthwise by default
        
        self.conv = nn.Conv1d(
            hidden_size,
            hidden_size,
            kernel_size=kernel_size,
            padding=kernel_size - 1,
            groups=groups,
            bias=False,
        )
        self.activation = nn.SiLU()
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: [B, T, C]
        Returns:
            [B, T, C]
        """
        # [B, T, C] -> [B, C, T]
        x = x.transpose(1, 2)
        # Causal convolution
        x = self.conv(x)[..., :x.size(-1)]
        x = self.activation(x)
        # [B, C, T] -> [B, T, C]
        return x.transpose(1, 2)


class GroupRMSNorm(nn.Module):
    """
    Grouped RMSNorm for QK-norm in multi-head attention.
    
    Normalizes each head independently.
    """
    
    def __init__(
        self,
        hidden_size: int,
        num_groups: int,
        eps: float = 1e-6,
    ):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_groups = num_groups
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(hidden_size))
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: [..., hidden_size]
        Returns:
            [..., hidden_size]
        """
        orig_shape = x.shape
        group_size = self.hidden_size // self.num_groups
        
        # Reshape to groups
        x = x.view(*orig_shape[:-1], self.num_groups, group_size)
        
        # RMS norm per group
        rms = x.float().pow(2).mean(dim=-1, keepdim=True).add(self.eps).sqrt()
        x = x / rms
        
        # Reshape back and apply weight
        x = x.view(*orig_shape)
        weight = self.weight.view(1, 1, -1) if x.dim() == 3 else self.weight
        
        return (x * weight).to(orig_shape[0].dtype if hasattr(orig_shape[0], 'dtype') else x.dtype)


class ForgettingAttention(nn.Module):
    """
    Forgetting Attention (FoX) v2.0.0
    
    The forget gate down-weights attention scores in a data-dependent way:
    attn_weights[i,j] = softmax(q_i @ k_j / sqrt(d) + cumsum(log_fgate)[i] - cumsum(log_fgate)[j])
    
    Pro Design (kept):
    - Output gate (like GLA)
    - QK-norm for stability
    - Short convolution on K, V
    - FusedRMSNormSwishGate for output
    """
    
    def __init__(
        self,
        n_embd: int,
        n_head: int,
        n_kv_head: Optional[int] = None,
        head_dim: Optional[int] = None,
        dropout: float = 0.0,
        use_output_gate: bool = True,
        use_output_norm: bool = True,
        use_qk_norm: bool = True,
        use_k_shift: bool = True,
        use_v_shift: bool = True,
        layer_idx: int = 0,
        n_layer: int = 12,
        conv_kernel_size: int = 4,
        bias: bool = False,
    ):
        super().__init__()
        self.n_embd = n_embd
        self.n_head = n_head
        self.n_kv_head = n_kv_head or n_head
        self.head_dim = head_dim or (n_embd // n_head)
        self.dropout = dropout
        
        # Pro design flags
        self.use_output_gate = use_output_gate
        self.use_output_norm = use_output_norm
        self.use_qk_norm = use_qk_norm
        self.use_k_shift = use_k_shift
        self.use_v_shift = use_v_shift
        
        # Dimensions
        self.q_dim = self.n_head * self.head_dim
        self.kv_dim = self.n_kv_head * self.head_dim
        self.v_dim = self.n_head * self.head_dim
        
        # Projections
        self.q_proj = nn.Linear(n_embd, self.q_dim, bias=bias)
        self.k_proj = nn.Linear(n_embd, self.kv_dim, bias=bias)
        self.v_proj = nn.Linear(n_embd, self.v_dim, bias=bias)
        self.o_proj = nn.Linear(self.v_dim, n_embd, bias=bias)
        
        # Forget gate projection - per head
        self.fgate_proj = nn.Linear(n_embd, self.n_head, bias=True)
        nn.init.constant_(self.fgate_proj.bias, 2.0)  # sigmoid(2) ≈ 0.88
        
        # Output gate (Pro design)
        if use_output_gate:
            self.ogate_proj = nn.Linear(n_embd, self.v_dim, bias=bias)
        
        # Output norm (Pro design)
        if use_output_norm:
            self.output_norm = FusedRMSNormSwishGate(self.head_dim, eps=1e-6)
        
        # QK-norm (Pro design)
        if use_qk_norm:
            self.q_norm = GroupRMSNorm(self.q_dim, self.n_head)
            self.k_norm = GroupRMSNorm(self.kv_dim, self.n_kv_head)
        
        # Short convolution for K, V (Pro design)
        if use_k_shift:
            self.k_conv = ShortConvolution(self.kv_dim, conv_kernel_size)
        if use_v_shift:
            self.v_conv = ShortConvolution(self.v_dim, conv_kernel_size)
        
        self.attn_dropout = nn.Dropout(dropout)
        self.scale = 1.0 / math.sqrt(self.head_dim)
        self.chunk_size = 128
        
        self.last_metrics: Optional[FoXMetrics] = None
        self.use_fla = FLA_FOX_AVAILABLE
    
    def _build_fox_mask(self, cumsum_log_fgate: torch.Tensor, T: int, device: torch.device) -> torch.Tensor:
        """
        Build the FoX attention mask combining forget gate decay with causal mask.
        
        v2.1.0: Optimized mask construction
        - Uses additive bias (not boolean mask) for SDPA compatibility
        - Pre-computed causal mask cached as buffer
        
        Args:
            cumsum_log_fgate: [B, H, T] cumulative sum of log forget gates
            T: sequence length
            device: target device
            
        Returns:
            attn_mask: [B, H, T, T] combined mask for SDPA
        """
        # Decay matrix from forget gate: [B, H, T, T]
        # decay[i,j] = cumsum[i] - cumsum[j] (vectorized, no loop)
        decay = cumsum_log_fgate.unsqueeze(-1) - cumsum_log_fgate.unsqueeze(-2)
        
        # Causal mask: upper triangle = -inf (cached if possible)
        if not hasattr(self, '_causal_cache') or self._causal_cache.shape[0] < T:
            self._causal_cache = torch.triu(
                torch.full((T, T), float('-inf'), device=device, dtype=decay.dtype),
                diagonal=1
            )
        causal_mask = self._causal_cache[:T, :T]
        
        # Combine: decay + causal (in-place if safe)
        return decay + causal_mask
    
    def _sdpa_attention(self, q, k, v, cumsum_log_fgate, device):
        """
        SDPA-based attention with FoX forget gate.
        
        v2.1.0: Optimized implementation
        - For short sequences (T <= chunk_size): use SDPA with mask
        - For long sequences: chunked approach with FlashAttention per chunk
        
        Note: Using attn_mask disables FlashAttention kernel.
        For maximum performance on long sequences, use fla-org Triton kernels.
        """
        B, H, T, D = q.shape
        
        # For shorter sequences, direct SDPA is efficient enough
        # The mask overhead is acceptable for T <= 512
        if T <= 512:
            attn_mask = self._build_fox_mask(cumsum_log_fgate, T, device)
            return F.scaled_dot_product_attention(
                q, k, v,
                attn_mask=attn_mask,
                dropout_p=self.dropout if self.training else 0.0,
                is_causal=False,
                scale=self.scale,
            )
        
        # For longer sequences, use chunked attention
        # This amortizes the mask overhead across chunks
        chunk_size = self.chunk_size
        n_chunks = (T + chunk_size - 1) // chunk_size
        
        outputs = []
        for c in range(n_chunks):
            start = c * chunk_size
            end = min(start + chunk_size, T)
            
            q_c = q[:, :, start:end]
            k_c = k[:, :, :end]  # All previous keys
            v_c = v[:, :, :end]  # All previous values
            cumsum_c = cumsum_log_fgate[:, :, :end]
            
            # Build mask for this chunk
            attn_mask_c = self._build_fox_mask(cumsum_c, end, device)
            # Only need rows for current chunk
            attn_mask_c = attn_mask_c[:, :, start:end, :end]
            
            out_c = F.scaled_dot_product_attention(
                q_c, k_c, v_c,
                attn_mask=attn_mask_c,
                dropout_p=self.dropout if self.training else 0.0,
                is_causal=False,
                scale=self.scale,
            )
            outputs.append(out_c)
        
        return torch.cat(outputs, dim=2)
    
    def _fallback_attention(self, q, k, v, cumsum_log_fgate, device):
        """
        Fallback attention for cases where SDPA doesn't support the mask.
        Used when attn_mask causes issues (rare edge cases).
        """
        B, H, T, D = q.shape
        
        # Compute attention scores
        attn_scores = torch.matmul(q, k.transpose(-2, -1)) * self.scale
        
        # Decay matrix from forget gate
        decay = cumsum_log_fgate.unsqueeze(-1) - cumsum_log_fgate.unsqueeze(-2)
        attn_scores = attn_scores + decay
        
        # Causal mask
        causal_mask = torch.triu(torch.ones(T, T, device=device, dtype=torch.bool), diagonal=1)
        attn_scores = attn_scores.masked_fill(causal_mask, float('-inf'))
        
        # Softmax + dropout
        attn_weights = F.softmax(attn_scores, dim=-1)
        attn_weights = self.attn_dropout(attn_weights)
        
        return torch.matmul(attn_weights, v)
        
    def _repeat_kv(self, x: torch.Tensor, n_rep: int) -> torch.Tensor:
        """Repeat KV heads to match Q heads (for GQA)."""
        if n_rep == 1:
            return x
        B, T, n_kv, D = x.shape
        x = x.unsqueeze(-2).expand(B, T, n_kv, n_rep, D)
        return x.reshape(B, T, n_kv * n_rep, D)
    
    def forward(
        self,
        x: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
        past_key_value: Optional[Tuple[torch.Tensor, torch.Tensor, torch.Tensor]] = None,
        use_cache: bool = False,
    ) -> Tuple[torch.Tensor, FoXMetrics, Optional[Tuple[torch.Tensor, torch.Tensor, torch.Tensor]]]:
        """
        Forward with forgetting attention (OPTIMIZED v2.0).
        
        Args:
            x: [B, T, C] input
            mask: Optional attention mask
            past_key_value: (k, v, cumsum_log_fgate) cache
            use_cache: whether to return new cache
            
        Returns:
            output: [B, T, C]
            metrics: FoXMetrics
            current_key_value: new cache if use_cache=True
        """
        B, T, C = x.shape
        
        # Q, K, V projections
        q = self.q_proj(x)
        k = self.k_proj(x)
        v = self.v_proj(x)
        k_raw, v_raw = k, v
        
        # Short convolution (Pro design)
        if self.use_k_shift:
            if use_cache and T == 1 and getattr(self, "_k_conv_cache", None) is not None:
                kk = self.k_conv.kernel_size - 1
                k_cat = torch.cat([self._k_conv_cache, k], dim=1)
                k = self.k_conv(k_cat)[:, -1:, :]
                self._k_conv_cache = k_cat[:, -kk:, :]
            else:
                k = self.k_conv(k)
                if use_cache:
                    kk = self.k_conv.kernel_size - 1
                    if kk > 0:
                        if T >= kk:
                            self._k_conv_cache = k_raw[:, -kk:, :].detach()
                        else:
                            pad = torch.zeros(B, kk - T, k_raw.shape[-1], device=k_raw.device, dtype=k_raw.dtype)
                            self._k_conv_cache = torch.cat([pad, k_raw.detach()], dim=1)

        if self.use_v_shift:
            if use_cache and T == 1 and getattr(self, "_v_conv_cache", None) is not None:
                kv = self.v_conv.kernel_size - 1
                v_cat = torch.cat([self._v_conv_cache, v], dim=1)
                v = self.v_conv(v_cat)[:, -1:, :]
                self._v_conv_cache = v_cat[:, -kv:, :]
            else:
                v = self.v_conv(v)
                if use_cache:
                    kv = self.v_conv.kernel_size - 1
                    if kv > 0:
                        if T >= kv:
                            self._v_conv_cache = v_raw[:, -kv:, :].detach()
                        else:
                            pad = torch.zeros(B, kv - T, v_raw.shape[-1], device=v_raw.device, dtype=v_raw.dtype)
                            self._v_conv_cache = torch.cat([pad, v_raw.detach()], dim=1)
        
        # QK-norm (Pro design)
        if self.use_qk_norm:
            q = self.q_norm(q)
            k = self.k_norm(k)
        
        # Reshape for multi-head attention
        q = q.view(B, T, self.n_head, self.head_dim)
        k = k.view(B, T, self.n_kv_head, self.head_dim)
        v = v.view(B, T, self.n_head, self.head_dim)
        
        # Repeat KV for GQA
        n_rep = self.n_head // self.n_kv_head
        k = self._repeat_kv(k, n_rep)
        
        # Transpose for attention: [B, H, T, D]
        q = q.transpose(1, 2)
        k = k.transpose(1, 2)
        v = v.transpose(1, 2)
        
        # Forget gate
        fgate_logit = self.fgate_proj(x)  # [B, T, n_head]
        log_fgate = F.logsigmoid(fgate_logit.float()) # [B, T, H]
        
        # Cumulative sum of log forget gates [B, H, T]
        # We need to handle history if caching
        log_fgate_transposed = log_fgate.transpose(1, 2)
        
        if past_key_value is not None:
            _, _, past_cumsum = past_key_value
            # past_cumsum: [B, H, T_past]
            last_cumsum = past_cumsum[:, :, -1:]
            cumsum_log_fgate = torch.cumsum(log_fgate_transposed, dim=-1) + last_cumsum
        else:
            cumsum_log_fgate = torch.cumsum(log_fgate_transposed, dim=-1)
            
        # KV Cache Update
        if past_key_value is not None:
            past_k, past_v, past_cumsum = past_key_value
            k = torch.cat([past_k, k], dim=2)
            v = torch.cat([past_v, v], dim=2)
            cumsum_full = torch.cat([past_cumsum, cumsum_log_fgate], dim=2)
        else:
            cumsum_full = cumsum_log_fgate
            
        current_key_value = None
        if use_cache:
            current_key_value = (k, v, cumsum_full)
            
        # v2.2.6: Use fla Triton kernels - force fp32 for dtype consistency
        # fla-org keeps internal state in fp32 for numerical stability,
        # so ALL inputs must be fp32 to avoid Triton dtype mismatch errors
        # Note: If using cache (generation), we skip fla kernel and use SDPA with mask
        if self.use_fla and x.is_cuda and past_key_value is None:
            original_dtype = q.dtype
            
            # fla uses seq-first format: [B, T, H, D] - all in fp32
            # q, k, v are already [B, H, T, D], need to transpose
            q_fla = q.transpose(1, 2).float()  # [B, T, H, D]
            k_fla = k.transpose(1, 2).float()
            v_fla = v.transpose(1, 2).float()
            
            # fla expects log_fgate as [B, T, H], already fp32 from .float() call
            out = parallel_forgetting_attn(q_fla, k_fla, v_fla, log_fgate)
            # Convert output back to original dtype for downstream ops
            out = out.to(original_dtype)
            
            # Transpose back: [B, T, H, D] -> [B, H, T, D] -> [B, T, H, D]
            # out from fla is [B, T, H, D]
            out = out.transpose(1, 2) # [B, H, T, D] for consistency with SDPA path below
            out = out.transpose(1, 2) # [B, T, H, D]
        else:
            # Fallback to SDPA (slower, no FlashAttention with mask)
            # Or Generation Mode
            
            if past_key_value is not None:
                # Generation mode: T=1 usually
                # q: [B, H, 1, D]
                # k: [B, H, T_total, D]
                # cumsum_full: [B, H, T_total]
                
                decay = cumsum_log_fgate.unsqueeze(-1) - cumsum_full.unsqueeze(-2) # [B, H, 1, T_total]
                
                # SDPA
                out = F.scaled_dot_product_attention(
                    q, k, v,
                    attn_mask=decay,
                    dropout_p=0.0,
                    is_causal=False
                )
            else:
                try:
                    out = self._sdpa_attention(q, k, v, cumsum_log_fgate, x.device)
                except RuntimeError:
                    out = self._fallback_attention(q, k, v, cumsum_log_fgate, x.device)
            
            # Transpose back: [B, H, T, D] -> [B, T, H, D]
            out = out.transpose(1, 2)
        
        out = out.contiguous().to(x.dtype)
        
        # Output norm with gating (Pro design)
        if self.use_output_norm and self.use_output_gate:
            ogate = self.ogate_proj(x).view(B, T, self.n_head, self.head_dim)
            out = self.output_norm(out, ogate)
        elif self.use_output_gate:
            ogate = torch.sigmoid(self.ogate_proj(x))
            out = out.view(B, T, -1) * ogate
            out = out.view(B, T, self.n_head, self.head_dim)
        
        # Reshape and project output
        out = out.view(B, T, self.v_dim)
        out = self.o_proj(out)
        
        # Metrics
        with torch.no_grad():
            avg_fgate = torch.sigmoid(fgate_logit).mean().item()
            
        self.last_metrics = FoXMetrics(
            avg_forget_gate=avg_fgate,
            effective_context=1.0 / (1.0 - avg_fgate + 1e-6)
        )
        
        if use_cache:
            return out, self.last_metrics, current_key_value
        return out, self.last_metrics


class FoXLayer(nn.Module):
    """Complete FoX layer with pre-norm and residual connection."""
    
    def __init__(
        self,
        n_embd: int,
        n_head: int,
        n_kv_head: Optional[int] = None,
        dropout: float = 0.0,
        use_pro_design: bool = True,
    ):
        super().__init__()
        
        self.norm = RMSNorm(n_embd)
        self.attn = ForgettingAttention(
            n_embd=n_embd,
            n_head=n_head,
            n_kv_head=n_kv_head,
            dropout=dropout,
            use_output_gate=use_pro_design,
            use_output_norm=use_pro_design,
            use_qk_norm=use_pro_design,
            use_k_shift=use_pro_design,
            use_v_shift=use_pro_design,
        )
        
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, FoXMetrics]:
        h = self.norm(x)
        out, metrics = self.attn(h)
        return x + out, metrics
