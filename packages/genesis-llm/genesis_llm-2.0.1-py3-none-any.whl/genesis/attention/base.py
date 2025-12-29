"""
Gated DeltaNet v2.2.0
=====================

O(n) linear attention based on NVIDIA Gated DeltaNet (ICLR 2025).

v2.2.0: fla-org/flash-linear-attention integration
- Uses Triton kernels from fla.ops.gla when available (GPU-parallelized)
- Falls back to pure PyTorch if fla not installed
- Install: pip install git+https://github.com/fla-org/flash-linear-attention

Features:
- L2 normalization for Q/K
- Mamba-style gating for forget gate
- Short convolution on Q, K, V
- Delta rule for memory updates

References:
- NVlabs/GatedDeltaNet (ICLR 2025)
- Qwen3-Next (uses Gated DeltaNet)
- fla-org/flash-linear-attention (Triton kernels)
"""

import math
import os
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple
from dataclasses import dataclass

from .utils import chunk_linear_attention, repeat_kv, ShortConvolution
from ..layers.norms import l2_norm, L2Norm, ZeroCenteredRMSNorm, FusedRMSNormSwishGate

# Try to import fla-org Triton kernels
FLA_AVAILABLE = False
try:
    from fla.ops.gla import chunk_gla, fused_recurrent_gla
    FLA_AVAILABLE = True
except ImportError:
    pass


@dataclass
class GLAMetrics:
    """Metrics from GLA forward pass."""
    gate_openness: float = 0.0
    state_norm: float = 0.0
    forget_rate: float = 0.0
    chunk_efficiency: float = 0.0


class GatedLinearAttention(nn.Module):
    """
    Gated DeltaNet v2.0.0 - O(n) Linear Attention.
    
    Based on NVIDIA (ICLR 2025) + Qwen3-Next.
    """
    
    def __init__(
        self,
        n_embd: int,
        n_head: int,
        n_kv_head: Optional[int] = None,
        head_dim: Optional[int] = None,
        expand_k: float = 1.0,
        expand_v: float = 1.0,
        gate_fn: str = "swish",
        use_short_conv: bool = True,
        conv_size: int = 4,
        dropout: float = 0.0,
        norm_eps: float = 1e-5,
        chunk_size: int = 64,
        use_delta_rule: bool = True,
        qk_norm: str = "l2",
        use_mamba_gate: bool = True,
        gate_logit_normalizer: int = 16,
        fuse_norm_gate: bool = True,
        use_dynamic_lr: bool = True,
    ):
        super().__init__()
        self.n_embd = n_embd
        self.n_head = n_head
        self.n_kv_head = n_kv_head or n_head
        self.head_dim = head_dim or (n_embd // n_head)
        self.chunk_size = chunk_size
        self.use_delta_rule = use_delta_rule
        self.qk_norm_type = qk_norm
        self.use_mamba_gate = use_mamba_gate
        self.gate_logit_normalizer = gate_logit_normalizer
        self.fuse_norm_gate = fuse_norm_gate
        
        # State dimensions (no expansion by default for efficiency)
        self.key_dim = int(n_head * self.head_dim * expand_k)
        self.value_dim = int(n_head * self.head_dim * expand_v)
        self.head_qk_dim = self.key_dim // n_head
        self.head_v_dim = self.value_dim // n_head
        
        # GQA support
        self.num_kv_groups = self.n_head // self.n_kv_head
        self.key_dim_per_group = self.key_dim // self.num_kv_groups
        self.value_dim_per_group = self.value_dim // self.num_kv_groups
        
        # Projections
        self.q_proj = nn.Linear(n_embd, self.key_dim, bias=False)
        self.k_proj = nn.Linear(n_embd, self.key_dim_per_group, bias=False)
        self.v_proj = nn.Linear(n_embd, self.value_dim_per_group, bias=False)
        self.o_proj = nn.Linear(self.value_dim, n_embd, bias=False)
        
        # Output gate projection (Qwen3-Next/GDN style)
        self.g_proj = nn.Linear(n_embd, self.value_dim, bias=False)
        
        # Forget gate projection - per-head (simpler, efficient)
        self.gk_proj = nn.Linear(n_embd, n_head, bias=not use_mamba_gate)
        
        # Beta projection for delta rule
        self.b_proj = nn.Linear(n_embd, n_head, bias=True)
        
        # Mamba-style gating parameters (official GDN)
        # v2.4.8 FIX: Reduced A range from (0,16) to (0,8) to prevent State Collapse
        # High A values cause forget_gate ≈ 0, erasing state completely
        if use_mamba_gate:
            A = torch.empty(n_head, dtype=torch.float32).uniform_(0.5, 8)
            self.A_log = nn.Parameter(torch.log(A))
            self.A_log._no_weight_decay = True
            
            dt_min, dt_max = 0.001, 0.1
            dt = torch.exp(torch.rand(n_head) * (math.log(dt_max) - math.log(dt_min)) + math.log(dt_min))
            dt = torch.clamp(dt, min=1e-4)
            self.dt_bias = nn.Parameter(dt + torch.log(-torch.expm1(-dt)))
            self.dt_bias._no_weight_decay = True
        
        # Short convolution on Q, K, V (official GDN)
        self.use_short_conv = use_short_conv
        if use_short_conv:
            conv_act = 'silu' if qk_norm != 'softmax' else None
            self.conv_q = ShortConvolution(self.key_dim, conv_size, activation=conv_act)
            self.conv_k = ShortConvolution(self.key_dim_per_group, conv_size, activation=conv_act)
            self.conv_v = ShortConvolution(self.value_dim_per_group, conv_size, activation='silu')
        
        # QK Normalization - L2 is default (fastest)
        from ..layers.norms import RMSNorm, RotaryPositionalEmbedding
        self.use_l2_norm = (qk_norm == "l2")
        if not self.use_l2_norm:
            self.q_norm = RMSNorm(self.head_qk_dim, eps=norm_eps)
            self.k_norm = RMSNorm(self.head_qk_dim, eps=norm_eps)
        
        # RoPE - partial rotation (FLA best practice)
        self.rope = RotaryPositionalEmbedding(
            dim=self.head_qk_dim,
            max_seq_len=4096,
            partial_rotary_factor=0.5,
        )
        
        self.dropout = nn.Dropout(dropout)
        
        # Output normalization + gate
        if fuse_norm_gate:
            self.g_norm_swish_gate = FusedRMSNormSwishGate(
                self.head_v_dim, elementwise_affine=True, eps=norm_eps
            )
        else:
            self.g_norm = RMSNorm(self.head_v_dim, eps=norm_eps)
        
        self.last_metrics: Optional[GLAMetrics] = None
        self.use_fla = FLA_AVAILABLE
        self._init_weights()
        
    def _init_weights(self):
        """Initialize weights following official Gated DeltaNet best practices."""
        # Beta projection - small init for stable delta rule
        nn.init.zeros_(self.b_proj.weight)
        if self.b_proj.bias is not None:
            nn.init.zeros_(self.b_proj.bias)
        
        # Gate projection - small init
        nn.init.zeros_(self.gk_proj.weight)
        if hasattr(self.gk_proj, 'bias') and self.gk_proj.bias is not None:
            nn.init.zeros_(self.gk_proj.bias)
        
        # Output gate - small init for near-identity at start
        nn.init.zeros_(self.g_proj.weight)
    
    def _repeat_kv(self, x: torch.Tensor, n_rep: int) -> torch.Tensor:
        """Repeat KV heads for GQA."""
        return repeat_kv(x, n_rep)
    
    def forward(
        self,
        x: torch.Tensor,
        past_state: Optional[torch.Tensor] = None,
        return_state: bool = False,
        position_offset: int = 0,
        past_key_value: Optional[dict] = None,
        use_cache: bool = False,
    ):
        """
        Forward with Gated DeltaNet attention (OPTIMIZED v2.0).
        
        v0.8.2: Added segment-level recurrence (Transformer-XL style)
        - Pass past_state from previous segment for extended context
        - State is detached to prevent gradient flow across segments
        - Use return_state=True to get final state for next segment
        
        Args:
            x: [B, T, C] input
            past_state: [B, n_head, head_dim, head_dim] state from previous segment
            return_state: whether to return final state for next segment
            
        Returns:
            output: [B, T, C]
            metrics: GLA metrics
            (optional) final_state: [B, n_head, head_dim, head_dim] if return_state=True
        """
        B, T, C = x.shape
        
        # Compute Q, K, V projections
        q = self.q_proj(x)
        k = self.k_proj(x)
        v = self.v_proj(x)
        q_raw, k_raw, v_raw = q, k, v
        
        # Short convolution on Q, K, V (official GDN)
        if self.use_short_conv:
            if use_cache:
                kq = self.conv_q.kernel_size - 1
                kk = self.conv_k.kernel_size - 1
                kv = self.conv_v.kernel_size - 1

                if past_key_value is not None:
                    conv_cache_q = past_key_value.get("conv_cache_q")
                    conv_cache_k = past_key_value.get("conv_cache_k")
                    conv_cache_v = past_key_value.get("conv_cache_v")
                    if conv_cache_q is not None:
                        self._conv_cache_q = conv_cache_q
                    if conv_cache_k is not None:
                        self._conv_cache_k = conv_cache_k
                    if conv_cache_v is not None:
                        self._conv_cache_v = conv_cache_v

                if T == 1 and getattr(self, "_conv_cache_q", None) is not None:
                    q_cat = torch.cat([self._conv_cache_q, q], dim=1)
                    q = self.conv_q(q_cat)[:, -1:, :]
                    self._conv_cache_q = q_cat[:, -kq:, :]
                else:
                    q = self.conv_q(q)
                    if kq > 0:
                        if T >= kq:
                            self._conv_cache_q = q_raw[:, -kq:, :].detach()
                        else:
                            pad = torch.zeros(B, kq - T, q_raw.shape[-1], device=q_raw.device, dtype=q_raw.dtype)
                            self._conv_cache_q = torch.cat([pad, q_raw.detach()], dim=1)

                if T == 1 and getattr(self, "_conv_cache_k", None) is not None:
                    k_cat = torch.cat([self._conv_cache_k, k], dim=1)
                    k = self.conv_k(k_cat)[:, -1:, :]
                    self._conv_cache_k = k_cat[:, -kk:, :]
                else:
                    k = self.conv_k(k)
                    if kk > 0:
                        if T >= kk:
                            self._conv_cache_k = k_raw[:, -kk:, :].detach()
                        else:
                            pad = torch.zeros(B, kk - T, k_raw.shape[-1], device=k_raw.device, dtype=k_raw.dtype)
                            self._conv_cache_k = torch.cat([pad, k_raw.detach()], dim=1)

                if T == 1 and getattr(self, "_conv_cache_v", None) is not None:
                    v_cat = torch.cat([self._conv_cache_v, v], dim=1)
                    v = self.conv_v(v_cat)[:, -1:, :]
                    self._conv_cache_v = v_cat[:, -kv:, :]
                else:
                    v = self.conv_v(v)
                    if kv > 0:
                        if T >= kv:
                            self._conv_cache_v = v_raw[:, -kv:, :].detach()
                        else:
                            pad = torch.zeros(B, kv - T, v_raw.shape[-1], device=v_raw.device, dtype=v_raw.dtype)
                            self._conv_cache_v = torch.cat([pad, v_raw.detach()], dim=1)
            else:
                q = self.conv_q(q)
                k = self.conv_k(k)
                v = self.conv_v(v)
        
        # Compute forget gate (gk) - per-head, Mamba-style
        gk = self.gk_proj(x).float()  # [B, T, n_head]
        if self.use_mamba_gate:
            gk = -self.A_log.float().exp() * F.softplus(gk + self.dt_bias)
        else:
            gk = F.logsigmoid(gk) / self.gate_logit_normalizer
        gk = gk.transpose(1, 2).unsqueeze(-1)  # [B, n_head, T, 1]
        
        # Compute beta (per-token learning rate for delta rule)
        beta = self.b_proj(x).float().sigmoid()  # [B, T, n_head]
        beta = beta.transpose(1, 2)  # [B, n_head, T]
        
        # Reshape for multi-head attention
        q = q.view(B, T, self.n_head, self.head_qk_dim).transpose(1, 2)
        
        # Handle GQA: repeat K, V if needed
        if self.num_kv_groups > 1:
            k = k.view(B, T, self.n_kv_head, self.head_qk_dim)
            v = v.view(B, T, self.n_kv_head, self.head_v_dim)
            k = k.unsqueeze(2).expand(B, T, self.num_kv_groups, self.n_kv_head, self.head_qk_dim)
            k = k.reshape(B, T, self.n_head, self.head_qk_dim).transpose(1, 2)
            v = v.unsqueeze(2).expand(B, T, self.num_kv_groups, self.n_kv_head, self.head_v_dim)
            v = v.reshape(B, T, self.n_head, self.head_v_dim).transpose(1, 2)
        else:
            k = k.view(B, T, self.n_head, self.head_qk_dim).transpose(1, 2)
            v = v.view(B, T, self.n_head, self.head_v_dim).transpose(1, 2)
        
        # QK Normalization (L2 is official GDN default)
        if self.use_l2_norm:
            q = l2_norm(q)
            k = l2_norm(k)
        else:
            q = self.q_norm(q)
            k = self.k_norm(k)
        
        # Apply RoPE (partial rotation)
        q, k = self.rope(q, k, position_offset=position_offset)
        
        # Gated linear attention with delta rule
        # v2.2.6: Use fla Triton kernels - force fp32 for dtype consistency
        # fla-org keeps internal state in fp32 for numerical stability,
        # so ALL inputs must be fp32 to avoid Triton dtype mismatch errors
        if self.use_fla and q.is_cuda:
            original_dtype = q.dtype
            
            # fla uses seq-first format: [B, T, H, D] - all in fp32
            q_fla = q.transpose(1, 2).float()  # [B, H, T, D] -> [B, T, H, D]
            k_fla = k.transpose(1, 2).float()
            v_fla = v.transpose(1, 2).float()
            
            # fla expects g to have same shape as q, k: [B, T, H, D]
            # gk is already fp32 from .float() call earlier
            gk_fla = gk.squeeze(-1).transpose(1, 2)  # [B, H, T] -> [B, T, H]
            gk_fla = gk_fla.unsqueeze(-1).expand_as(k_fla)  # [B, T, H, D], already fp32
            
            # Use fused_recurrent for short sequences, chunk for longer
            if T <= 64:
                output, final_state = fused_recurrent_gla(
                    q=q_fla, k=k_fla, v=v_fla, gk=gk_fla,
                    initial_state=past_state,
                    output_final_state=return_state,
                )
            else:
                output, final_state = chunk_gla(
                    q=q_fla, k=k_fla, v=v_fla, g=gk_fla,
                    initial_state=past_state,
                    output_final_state=return_state,
                )
            # Convert output back to original dtype for downstream ops
            output = output.to(original_dtype)
        else:
            # Fallback to pure PyTorch implementation
            use_delta_rule = self.use_delta_rule and (not use_cache)
            if use_delta_rule and (not q.is_cuda) and (not self.training):
                if os.environ.get("GENESIS_ENABLE_DELTA_RULE_ON_CPU", "0") != "1":
                    use_delta_rule = False
            attn_result = chunk_linear_attention(
                q, k, v, 
                gk,
                chunk_size=self.chunk_size,
                use_delta_rule=use_delta_rule,
                input_gate=beta.unsqueeze(-1),
                initial_state=past_state,
                return_state=return_state,
            )
            
            if return_state:
                output, final_state = attn_result
            else:
                output = attn_result
                final_state = None
            
            # Reshape for output processing: [B, H, T, D] -> [B, T, H, D]
            output = output.transpose(1, 2)
        
        # Output gate with FusedRMSNormSwishGate (official GDN style)
        g = self.g_proj(x)
        g = g.view(B, T, self.n_head, self.head_v_dim)
        
        if self.fuse_norm_gate:
            output = self.g_norm_swish_gate(output, g)
        else:
            output = self.g_norm(output) * F.silu(g)
        
        # Reshape and project to output
        output = output.reshape(B, T, self.value_dim)
        output = self.o_proj(output)
        output = self.dropout(output)
        
        # Collect metrics
        self.last_metrics = GLAMetrics(
            gate_openness=beta.mean().item(),
            state_norm=k.norm().item() / (B * T),
            forget_rate=gk.exp().mean().item(),
        )
        
        if return_state:
            if use_cache:
                present_key_value = {
                    "position_offset": int(position_offset) + int(T),
                    "conv_cache_q": getattr(self, "_conv_cache_q", None).detach() if getattr(self, "_conv_cache_q", None) is not None else None,
                    "conv_cache_k": getattr(self, "_conv_cache_k", None).detach() if getattr(self, "_conv_cache_k", None) is not None else None,
                    "conv_cache_v": getattr(self, "_conv_cache_v", None).detach() if getattr(self, "_conv_cache_v", None) is not None else None,
                }
                return output, self.last_metrics, final_state, present_key_value
            return output, self.last_metrics, final_state

        if use_cache:
            present_key_value = {
                "position_offset": int(position_offset) + int(T),
                "conv_cache_q": getattr(self, "_conv_cache_q", None).detach() if getattr(self, "_conv_cache_q", None) is not None else None,
                "conv_cache_k": getattr(self, "_conv_cache_k", None).detach() if getattr(self, "_conv_cache_k", None) is not None else None,
                "conv_cache_v": getattr(self, "_conv_cache_v", None).detach() if getattr(self, "_conv_cache_v", None) is not None else None,
            }
            return output, self.last_metrics, present_key_value

        return output, self.last_metrics
    
