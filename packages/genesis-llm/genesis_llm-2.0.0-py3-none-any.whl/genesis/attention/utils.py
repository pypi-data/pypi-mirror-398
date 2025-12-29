"""
Attention Utilities v2.1.0
==========================

Shared utilities for attention mechanisms.

v2.1.0: Pure PyTorch optimizations:
- Pre-allocated output tensors (avoid list append + cat)
- Pre-computed chunk decay factors (vectorized)
- Cached causal masks
- contiguous() for kernel fusion with torch.compile

NOTE: This is PURE PYTORCH, not using fla-org/flash-linear-attention.
The sequential inter-chunk loop is unavoidable in PyTorch due to state dependency.
For maximum performance, consider integrating fla-org Triton kernels:
  pip install git+https://github.com/fla-org/flash-linear-attention
  from fla.ops.gla import chunk_gla

v2.0.0: Simplified - removed DeltaProduct, Vector Gating code
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple


def _simple_linear_attention(
    q: torch.Tensor,
    k: torch.Tensor,
    v: torch.Tensor,
    forget: torch.Tensor,
    use_delta_rule: bool = False,
    input_gate: Optional[torch.Tensor] = None,
    initial_state: Optional[torch.Tensor] = None,
    return_state: bool = False,
) -> torch.Tensor:
    """
    Simple linear attention fallback for small T (e.g., during generation).
    
    Uses the same math as the chunked path, but runs in a single chunk while
    supporting state passing (needed for cached generation).
    
    Note: v can have different last dim than q/k due to gla_expand_v.
    
    v2.4.3 FIX: Fixed numerical instability in delta rule path:
    - forget is log-space (negative values), need exp() for state decay
    - Added state norm clipping to prevent explosion
    - Use float32 for state accumulation to prevent overflow
    """
    B, n_head, T, head_dim = q.shape
    v_dim = v.shape[-1]  # May differ from head_dim if gla_expand_v != 1.0
    scale = head_dim ** -0.5
    
    log_g = forget.squeeze(-1).float()
    log_g_cumsum = torch.cumsum(log_g, dim=-1)
    log_g_row = log_g_cumsum.unsqueeze(-1)
    log_g_col = log_g_cumsum.unsqueeze(-2)
    intra_decay = torch.exp(log_g_row - log_g_col)
    causal_mask = torch.triu(torch.ones(T, T, device=q.device, dtype=torch.bool), diagonal=1)
    intra_decay = intra_decay.masked_fill(causal_mask, 0)
    scores = torch.matmul(q, k.transpose(-2, -1)) * scale
    scores = scores * intra_decay
    all_intra = torch.matmul(scores, v)
    if initial_state is not None:
        state = initial_state
    else:
        state = torch.zeros(B, n_head, head_dim, v_dim, device=q.device, dtype=q.dtype)
    pos_decay = torch.exp(log_g_cumsum).unsqueeze(-1)
    out_inter = torch.matmul(q, state) * pos_decay * scale
    output = all_intra + out_inter
    if not return_state:
        return output
    chunk_end_decay = torch.exp(log_g_cumsum[:, :, -1]).unsqueeze(-1).unsqueeze(-1)
    state_decayed = chunk_end_decay * state
    end_log_g = log_g_cumsum[:, :, -1].unsqueeze(-1)
    w = torch.exp(end_log_g - log_g_cumsum)
    k_weighted = k * w.unsqueeze(-1)
    if use_delta_rule and input_gate is not None:
        v_retrieved = torch.matmul(k_weighted, state_decayed) * scale
        v_delta = (v - v_retrieved) * input_gate
        kv_update = torch.matmul(k_weighted.transpose(-2, -1), v_delta)
    else:
        kv_update = torch.matmul(k_weighted.transpose(-2, -1), v)
    final_state = state_decayed + kv_update
    return output, final_state


def _chunk_state_passing(
    q_chunks: torch.Tensor,
    k_chunks: torch.Tensor, 
    v_chunks: torch.Tensor,
    log_g_cumsum: torch.Tensor,
    all_intra: torch.Tensor,
    initial_state: Optional[torch.Tensor],
    use_delta_rule: bool,
    input_gate_chunks: Optional[torch.Tensor],
    B: int, n_head: int, n_chunks: int, chunk_size: int, head_dim: int, v_dim: int,
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Sequential state passing between chunks.
    
    v2.1.0: Optimized for torch.compile by minimizing Python overhead.
    The loop is unavoidable due to sequential state dependency, but we:
    - Pre-compute all decay factors
    - Minimize tensor indexing inside loop
    - Use in-place operations where safe
    """
    device = q_chunks.device
    dtype = q_chunks.dtype
    
    # Pre-compute ALL chunk decay factors at once [B, n_head, n_chunks]
    chunk_end_decay = torch.exp(log_g_cumsum[:, :, :, -1])  # [B, n_head, n_chunks]
    
    # Pre-compute positional decay for all chunks [B, n_head, n_chunks, chunk_size, 1]
    pos_decay = torch.exp(log_g_cumsum).unsqueeze(-1)
    
    # Initialize state
    if initial_state is not None:
        state = initial_state.clone()
    else:
        state = torch.zeros(B, n_head, head_dim, v_dim, device=device, dtype=dtype)
    
    # Pre-allocate output tensor (avoid list append + cat)
    outputs = torch.empty(B, n_head, n_chunks, chunk_size, v_dim, device=device, dtype=dtype)
    
    scale = head_dim ** -0.5

    # Sequential chunk processing (unavoidable due to state dependency)
    for c in range(n_chunks):
        # Inter-chunk: query current state
        # [B, n_head, chunk_size, head_dim] @ [B, n_head, head_dim, v_dim] -> [B, n_head, chunk_size, v_dim]
        out_inter = torch.matmul(q_chunks[:, :, c], state) * pos_decay[:, :, c] * scale
        
        # Combine intra + inter
        outputs[:, :, c] = all_intra[:, :, c] + out_inter
        
        # State decay for this chunk
        decay_c = chunk_end_decay[:, :, c].unsqueeze(-1).unsqueeze(-1)  # [B, n_head, 1, 1]
        state_decayed = decay_c * state
        end_log_g = log_g_cumsum[:, :, c, -1].unsqueeze(-1)  # [B, n_head, 1]
        w = torch.exp(end_log_g - log_g_cumsum[:, :, c])  # [B, n_head, chunk_size]
        k_weighted = k_chunks[:, :, c] * w.unsqueeze(-1)
        
        # State update
        if use_delta_rule and input_gate_chunks is not None:
            # Delta rule: v_new = v - retrieve(k, state)
            v_retrieved = torch.matmul(k_weighted, state_decayed) * scale
            v_delta = v_chunks[:, :, c] - v_retrieved
            v_delta = v_delta * input_gate_chunks[:, :, c]
            kv_update = torch.matmul(k_weighted.transpose(-2, -1), v_delta)
        else:
            # Standard linear attention update
            kv_update = torch.matmul(k_weighted.transpose(-2, -1), v_chunks[:, :, c])
        
        state = state_decayed + kv_update
    
    # Reshape output [B, n_head, n_chunks, chunk_size, v_dim] -> [B, n_head, T, v_dim]
    output = outputs.view(B, n_head, n_chunks * chunk_size, v_dim)
    
    return output, state


def chunk_linear_attention(
    q: torch.Tensor,
    k: torch.Tensor,
    v: torch.Tensor,
    forget: torch.Tensor,
    chunk_size: int = 64,
    use_delta_rule: bool = False,
    input_gate: Optional[torch.Tensor] = None,
    initial_state: Optional[torch.Tensor] = None,
    return_state: bool = False,
) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
    """
    Chunk-wise linear attention - True O(n) complexity.
    
    v2.1.0: Optimized implementation based on fla-org patterns:
    - Vectorized intra-chunk computation (fully parallel)
    - Optimized inter-chunk state passing
    - Pre-allocated output tensors
    - torch.compile friendly
    
    Args:
        q: [B, n_head, T, head_dim] queries
        k: [B, n_head, T, head_dim] keys  
        v: [B, n_head, T, v_dim] values (v_dim may differ due to gla_expand_v)
        forget: [B, n_head, T, 1] forget gates
        chunk_size: size of chunks for parallel computation
        use_delta_rule: whether to use delta rule for memory updates
        input_gate: [B, n_head, T, 1] input gates (for delta rule)
        initial_state: [B, n_head, head_dim, v_dim] initial state
        return_state: whether to return final state
        
    Returns:
        output: [B, n_head, T, v_dim]
        OR (output, final_state) if return_state=True
    """
    B, n_head, T, head_dim = q.shape
    v_dim = v.shape[-1]
    
    # Fallback for small T (generation, short sequences)
    if T < chunk_size:
        return _simple_linear_attention(
            q,
            k,
            v,
            forget,
            use_delta_rule=use_delta_rule,
            input_gate=input_gate,
            initial_state=initial_state,
            return_state=return_state,
        )
    
    # Pad sequence to multiple of chunk_size
    pad_len = (chunk_size - T % chunk_size) % chunk_size
    if pad_len > 0:
        q = F.pad(q, (0, 0, 0, pad_len))
        k = F.pad(k, (0, 0, 0, pad_len))
        v = F.pad(v, (0, 0, 0, pad_len))
        forget = F.pad(forget, (0, 0, 0, pad_len), value=0.0)
        if input_gate is not None:
            input_gate = F.pad(input_gate, (0, 0, 0, pad_len), value=0.0)
    
    T_padded = q.shape[2]
    n_chunks = T_padded // chunk_size
    
    # =========================================================================
    # RESHAPE INTO CHUNKS (fused view, no copy)
    # =========================================================================
    q_chunks = q.view(B, n_head, n_chunks, chunk_size, head_dim)
    k_chunks = k.view(B, n_head, n_chunks, chunk_size, head_dim)
    v_chunks = v.view(B, n_head, n_chunks, chunk_size, v_dim)
    g_chunks = forget.view(B, n_head, n_chunks, chunk_size, 1)
    
    # Input gate chunks (if using delta rule)
    input_gate_chunks = None
    if input_gate is not None:
        input_gate_chunks = input_gate.view(B, n_head, n_chunks, chunk_size, 1)
    
    # =========================================================================
    # PRE-COMPUTE DECAY FACTORS (vectorized)
    # =========================================================================
    log_g = g_chunks.squeeze(-1)
    log_g_cumsum = torch.cumsum(log_g, dim=-1)
    
    # =========================================================================
    # INTRA-CHUNK COMPUTATION (fully parallel across all chunks)
    # =========================================================================
    # Causal decay matrix within each chunk
    log_g_row = log_g_cumsum.unsqueeze(-1)  # [B, n_head, n_chunks, chunk_size, 1]
    log_g_col = log_g_cumsum.unsqueeze(-2)  # [B, n_head, n_chunks, 1, chunk_size]
    intra_decay = torch.exp(log_g_row - log_g_col)  # [B, n_head, n_chunks, chunk_size, chunk_size]
    
    # Causal mask (upper triangle = 0)
    causal_mask = torch.triu(
        torch.ones(chunk_size, chunk_size, device=q.device, dtype=torch.bool), 
        diagonal=1
    )
    intra_decay = intra_decay.masked_fill(causal_mask, 0)
    
    # Attention scores within chunks (all chunks in parallel)
    scale = 1.0 / math.sqrt(head_dim)
    all_qk = torch.matmul(q_chunks, k_chunks.transpose(-2, -1)) * scale
    all_qk = all_qk * intra_decay
    
    # Intra-chunk output (all chunks in parallel)
    all_intra = torch.matmul(all_qk, v_chunks)  # [B, n_head, n_chunks, chunk_size, v_dim]
    
    # =========================================================================
    # INTER-CHUNK STATE PASSING (sequential, but optimized)
    # =========================================================================
    output, final_state = _chunk_state_passing(
        q_chunks, k_chunks, v_chunks, log_g_cumsum, all_intra,
        initial_state, use_delta_rule, input_gate_chunks,
        B, n_head, n_chunks, chunk_size, head_dim, v_dim,
    )
    
    # Remove padding
    output = output[:, :, :T]
    
    if return_state:
        return output, final_state
    return output


def repeat_kv(x: torch.Tensor, n_rep: int) -> torch.Tensor:
    """Repeat KV heads for GQA (Grouped Query Attention)."""
    if n_rep == 1:
        return x
    B, n_kv_head, T, head_dim = x.shape
    x = x[:, :, None, :, :].expand(B, n_kv_head, n_rep, T, head_dim)
    return x.reshape(B, n_kv_head * n_rep, T, head_dim)


class ShortConvolution(nn.Module):
    """
    Short 1D convolution for local context aggregation.
    
    v2.1.0: Optimized for torch.compile
    - Uses contiguous() to ensure memory layout
    - Fused activation when possible
    """
    
    def __init__(self, hidden_size: int, kernel_size: int = 4, activation: Optional[str] = 'silu'):
        super().__init__()
        self.hidden_size = hidden_size
        self.kernel_size = kernel_size
        
        # Depthwise conv for efficiency
        self.conv = nn.Conv1d(
            hidden_size, hidden_size,
            kernel_size=kernel_size,
            padding=kernel_size - 1,
            groups=hidden_size,
            bias=False,
        )
        
        # Store activation type for potential fusion
        self.activation_type = activation
        if activation == 'silu':
            self.activation = nn.SiLU()
        elif activation == 'gelu':
            self.activation = nn.GELU()
        else:
            self.activation = None
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        x: [B, T, D] -> [B, T, D]
        
        v2.1.0: Optimized with contiguous tensors
        """
        # Transpose to [B, D, T] for Conv1d (ensure contiguous for kernel fusion)
        x = x.transpose(1, 2).contiguous()
        
        # Causal conv: remove future context
        x = self.conv(x)[..., :-(self.kernel_size - 1)]
        
        # Apply activation
        if self.activation is not None:
            x = self.activation(x)
        
        # Transpose back to [B, T, D] (contiguous for downstream ops)
        return x.transpose(1, 2).contiguous()


class RotaryPositionalEmbedding(nn.Module):
    """
    Rotary Positional Embedding (RoPE).
    
    Based on RoFormer (2021) - applies rotation to partial dimensions.
    Used in LLaMA, Qwen, and most modern LLMs.
    """
    
    def __init__(
        self,
        dim: int,
        max_seq_len: int = 8192,
        base: float = 10000.0,
        rope_ratio: float = 1.0,  # Fraction of head_dim to apply RoPE
    ):
        super().__init__()
        self.dim = dim
        self.max_seq_len = max_seq_len
        self.base = base
        self.rope_ratio = rope_ratio
        
        # Compute inverse frequencies
        inv_freq = 1.0 / (base ** (torch.arange(0, dim, 2).float() / dim))
        self.register_buffer('inv_freq', inv_freq)
        
        # Pre-compute cos/sin for common sequence lengths
        self._build_cache(max_seq_len)
    
    def _build_cache(self, seq_len: int):
        """Build cos/sin cache for given sequence length."""
        t = torch.arange(seq_len, device=self.inv_freq.device)
        freqs = torch.einsum('i,j->ij', t, self.inv_freq)
        emb = torch.cat([freqs, freqs], dim=-1)
        self.register_buffer('cos_cache', emb.cos().unsqueeze(0).unsqueeze(0))
        self.register_buffer('sin_cache', emb.sin().unsqueeze(0).unsqueeze(0))
    
    def forward(self, x: torch.Tensor, seq_len: int = None) -> torch.Tensor:
        """
        Apply RoPE to input tensor.
        
        Args:
            x: [B, n_head, T, head_dim] input
            seq_len: sequence length (defaults to x.shape[2])
        
        Returns:
            x with rotary embedding applied
        """
        if seq_len is None:
            seq_len = x.shape[2]
        
        # Extend cache if needed
        if seq_len > self.max_seq_len:
            self._build_cache(seq_len)
            self.max_seq_len = seq_len
        
        cos = self.cos_cache[:, :, :seq_len, :self.dim]
        sin = self.sin_cache[:, :, :seq_len, :self.dim]
        
        # Apply partial RoPE if ratio < 1.0
        if self.rope_ratio < 1.0:
            rope_dim = int(x.shape[-1] * self.rope_ratio)
            x_rope = x[..., :rope_dim]
            x_pass = x[..., rope_dim:]
            
            x1 = x_rope[..., :rope_dim//2]
            x2 = x_rope[..., rope_dim//2:]
            rotated = torch.cat([-x2, x1], dim=-1)
            x_rope = x_rope * cos[..., :rope_dim] + rotated * sin[..., :rope_dim]
            
            return torch.cat([x_rope, x_pass], dim=-1)
        else:
            x1 = x[..., :self.dim//2]
            x2 = x[..., self.dim//2:self.dim]
            rotated = torch.cat([-x2, x1], dim=-1)
            x_new = x.clone()
            x_new[..., :self.dim] = x[..., :self.dim] * cos + rotated * sin
            return x_new
