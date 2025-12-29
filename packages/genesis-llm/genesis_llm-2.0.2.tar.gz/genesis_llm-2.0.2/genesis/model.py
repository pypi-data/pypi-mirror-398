"""
Genesis Model v2.0.0 - Efficient Neural Genesis
================================================

Clean, efficient architecture for <1B scale LLMs.

v2.0.0 CLEANUP - "Efficiency First":
Removed features with overhead > benefit at <1B scale.

Hybrid Attention (Qwen3-Next style):
- 75% GLA (Gated DeltaNet) - O(n) linear attention
- 25% FoX - Softmax with forget gate

Active Features:
1. GLA - Gated Linear Attention with Delta Rule
2. FoX - Forgetting Attention (ICLR 2025)
3. TTT - Test-Time Training
4. Selective Activation - Top-k FFN sparsity
5. µP - Hyperparameter transfer

"Efficiency First"
"""

from .attention.forgetting import ForgettingAttention
import math
import inspect
from typing import Optional, Tuple, Dict, List, Any
from dataclasses import dataclass, field

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.checkpoint import checkpoint

from .config import GenesisConfig
from .layers import RMSNorm, SwiGLU
from .layers.norms import ZeroCenteredRMSNorm
from .attention import GatedLinearAttention, GatedAttention
from .dynamics import GenesisMetacognition


def get_norm_class(config: GenesisConfig):
    """
    Get the appropriate normalization class based on config.
    
    v0.8.1: ZeroCenteredRMSNorm as default for better weight decay + µP compatibility.
    """
    if getattr(config, 'use_zero_centered_norm', True):
        return ZeroCenteredRMSNorm
    return RMSNorm


@dataclass
class GenesisMetrics:
    """Metrics from Genesis forward pass (v2.0.0 simplified)."""
    # Core
    loss: float = 0.0
    perplexity: float = 0.0
    
    # Attention (GLA + FoX)
    attention_gate_openness: float = 0.0
    attention_forget_rate: float = 0.0
    fox_effective_context: float = 0.0
    
    # Self-evolution (TTT)
    ttt_activated: bool = False
    surprise_level: float = 0.0
    confidence: float = 0.0
    
    # Auxiliary losses
    aux_loss: float = 0.0


class GenesisBlock(nn.Module):
    """
    Genesis Block - The fundamental unit of computation.
    
    Combines:
    - GLA/FoX attention (hybrid linear + softmax)
    - SwiGLU FFN with Selective Activation
    """
    
    def __init__(
        self,
        config: GenesisConfig,
        layer_idx: int = 0,
    ):
        super().__init__()
        self.config = config
        self.layer_idx = layer_idx
        
        # Pre-norm (v0.8.1: ZeroCenteredRMSNorm by default for µP compatibility)
        NormClass = get_norm_class(config)
        self.attn_norm = NormClass(config.n_embd, config.norm_eps)
        self.ffn_norm = NormClass(config.n_embd, config.norm_eps)
        
        # Attention: Hybrid Layout (75% GLA + 25% FoX)
        # v0.9.0: Hybrid Layout (Qwen3-Next style) - 75% GLA + 25% Full Attention
        self.use_full_attention = False  # Track for metrics
        
        if getattr(config, 'use_hybrid_layout', False) and config.use_gla:
            # Hybrid Layout (Qwen3-Next style): alternate between GLA and Full Attention
            # Pattern: every N-th layer uses Full Gated Attention for retrieval
            # v1.1.0: Option to use FoX (Forgetting Attention) for full attention layers
            hybrid_ratio = getattr(config, 'hybrid_full_attn_ratio', 0.25)
            full_attn_interval = int(1 / hybrid_ratio) if hybrid_ratio > 0 else config.n_layer + 1
            use_full_attn_this_layer = ((layer_idx + 1) % full_attn_interval == 0)
            
            if use_full_attn_this_layer:
                # v1.1.0: FoX (Forgetting Attention) or Gated Attention for precise retrieval
                use_fox = getattr(config, 'use_fox', True)
                use_fox_pro = getattr(config, 'use_fox_pro', True)
                
                if use_fox:
                    # FoX: Softmax with forget gate (ICLR 2025)
                    self.attn = ForgettingAttention(
                        n_embd=config.n_embd,
                        n_head=config.n_head,
                        n_kv_head=config.n_kv_head,
                        dropout=config.dropout,
                        use_output_gate=use_fox_pro,
                        use_output_norm=use_fox_pro,
                        use_qk_norm=use_fox_pro,
                        use_k_shift=use_fox_pro,
                        use_v_shift=use_fox_pro,
                        layer_idx=layer_idx,
                        n_layer=config.n_layer,
                    )
                else:
                    # Original Gated Attention
                    self.attn = GatedAttention(
                        n_embd=config.n_embd,
                        n_head=config.n_head,
                        n_kv_head=config.n_kv_head,
                        dropout=config.dropout,
                        max_seq_len=config.block_size,
                    )
                self.use_full_attention = True
            else:
                # Gated DeltaNet for efficiency (75% of layers)
                self.attn = GatedLinearAttention(
                    n_embd=config.n_embd,
                    n_head=config.n_head,
                    n_kv_head=config.n_kv_head,
                    expand_k=getattr(config, 'gla_expand_k', 1.0),
                    expand_v=getattr(config, 'gla_expand_v', 1.0),
                    use_short_conv=config.gla_use_short_conv,
                    conv_size=getattr(config, 'gla_conv_size', 4),
                    dropout=config.dropout,
                    chunk_size=getattr(config, 'gla_chunk_size', 64),
                    use_delta_rule=getattr(config, 'gla_use_delta_rule', True),
                    qk_norm=getattr(config, 'gla_qk_norm', 'l2'),
                    use_mamba_gate=getattr(config, 'gla_use_mamba_gate', True),
                    gate_logit_normalizer=getattr(config, 'gla_gate_logit_normalizer', 16),
                    fuse_norm_gate=getattr(config, 'gla_fuse_norm_gate', True),
                    use_dynamic_lr=getattr(config, 'gla_use_dynamic_lr', True),
                )
        elif config.use_gla:
            # GLA: Gated DeltaNet for linear attention
            self.attn = GatedLinearAttention(
                    n_embd=config.n_embd,
                    n_head=config.n_head,
                    n_kv_head=config.n_kv_head,
                    expand_k=getattr(config, 'gla_expand_k', 1.0),
                    expand_v=getattr(config, 'gla_expand_v', 1.0),
                    use_short_conv=config.gla_use_short_conv,
                    conv_size=getattr(config, 'gla_conv_size', 4),
                    dropout=config.dropout,
                    chunk_size=getattr(config, 'gla_chunk_size', 64),
                    use_delta_rule=getattr(config, 'gla_use_delta_rule', True),
                    qk_norm=getattr(config, 'gla_qk_norm', 'l2'),
                    use_mamba_gate=getattr(config, 'gla_use_mamba_gate', True),
                    gate_logit_normalizer=getattr(config, 'gla_gate_logit_normalizer', 16),
                    fuse_norm_gate=getattr(config, 'gla_fuse_norm_gate', True),
                    use_dynamic_lr=getattr(config, 'gla_use_dynamic_lr', True),
                )
        else:
            # Standard attention fallback
            self.attn = nn.MultiheadAttention(
                config.n_embd, config.n_head,
                dropout=config.dropout,
                batch_first=True,
            )
        
        # FFN: SwiGLU with Selective Activation
        self.ffn = SwiGLU(
            config.n_embd,
            config.intermediate_size,
            dropout=config.dropout,
            use_selective_activation=getattr(config, 'use_selective_activation', False),
            k_ratio=getattr(config, 'selective_k_ratio', 0.5),
            use_soft_mask=getattr(config, 'selective_use_soft_mask', True),
            mask_temperature=getattr(config, 'selective_mask_temperature', 0.1),
            selective_activation_in_eval=getattr(config, 'selective_activation_in_eval', False),
        )
        
        self.dropout = nn.Dropout(config.dropout)
        
        # Metrics storage
        self.last_attn_metrics = None
        
    def forward(
        self, 
        x: torch.Tensor,
        past_state: Optional[torch.Tensor] = None,
        return_state: bool = False,
        past_key_value: Optional[Tuple] = None,
        use_cache: bool = False,
        position_offset: int = 0,
    ) -> Tuple[torch.Tensor, float, Optional[Any], Optional[Tuple]]:
        """
        Forward through Genesis block.
        
        v0.8.2: Added segment-level recurrence support for GLA layers.
        v2.2.0: Added KV cache support for Attention/FoX layers.
        
        Flow:
        1. Attention - capture dependencies (with optional state passing)
        2. FFN - heavy computation
        
        Args:
            x: [B, T, C] input
            past_state: optional state from previous segment (GLA only)
            return_state: whether to return final state for next segment
            past_key_value: optional KV cache (FoX/Attention only)
            use_cache: whether to return new KV cache
        
        Returns:
            output: [B, T, C]
            aux_loss: auxiliary losses
            (optional) final_state: if return_state=True
            (optional) current_key_value: if use_cache=True
        """
        aux_loss = 0.0
        final_state = None
        current_key_value = None
        
        # 1. Attention (with optional segment-level recurrence for GLA)
        h = self.attn_norm(x)
        if hasattr(self.attn, 'forward') and not isinstance(self.attn, nn.MultiheadAttention):
            # Check if this is a GLA layer that supports state passing
            # v2.2.1: Fix - ForgettingAttention also has chunk_size but is NOT GLA
            is_gla = hasattr(self.attn, 'chunk_size') and not getattr(self, 'use_full_attention', False)
            
            if is_gla and (past_state is not None or return_state or use_cache or past_key_value is not None):
                # GLA with segment-level recurrence
                result = self.attn(
                    h,
                    past_state=past_state,
                    return_state=return_state,
                    position_offset=position_offset,
                    past_key_value=past_key_value,
                    use_cache=use_cache,
                )
                if return_state and use_cache:
                    attn_out, attn_metrics, final_state, current_key_value = result
                elif return_state:
                    attn_out, attn_metrics, final_state = result
                elif use_cache:
                    attn_out, attn_metrics, current_key_value = result
                else:
                    attn_out, attn_metrics = result
            elif not is_gla and (past_key_value is not None or use_cache):
                # FoX / Gated Attention with KV Cache
                # We assume updated signatures in forgetting.py / gated_attention.py
                result = self.attn(h, past_key_value=past_key_value, use_cache=use_cache)
                if use_cache:
                    attn_out, attn_metrics, current_key_value = result
                else:
                    attn_out, attn_metrics = result
            else:
                # GLA, FoX, GatedAttention - standard forward
                attn_out, attn_metrics = self.attn(h)
            self.last_attn_metrics = attn_metrics
        else:
            # Standard nn.MultiheadAttention fallback
            B, T, C = h.shape
            causal_mask = torch.triu(
                torch.full((T, T), float('-inf'), device=x.device),
                diagonal=1
            )
            attn_out, _ = self.attn(h, h, h, attn_mask=causal_mask, is_causal=True)
        
        x = x + self.dropout(attn_out)
        
        # 2. FFN (SwiGLU)
        h = self.ffn_norm(x)
        ffn_out = self.ffn(h)
        x = x + ffn_out
        
        if return_state or use_cache:
            # We return a tuple that might contain both
            return x, aux_loss, final_state, current_key_value
        return x, aux_loss


class Genesis(nn.Module):
    """
    Genesis 2.0.0 - Efficient Neural Genesis Architecture.
    
    Clean architecture for <1B scale:
    - GLA: O(n) linear attention with delta rule
    - FoX: Forgetting attention for 25% of layers
    - TTT: Self-evolution
    - Selective Activation: Top-k FFN sparsity
    - µP: Hyperparameter transfer
    
    Usage:
        config = GenesisConfig.medium()
        model = Genesis(config)
        logits, loss, metrics = model(input_ids, targets)
    """
    
    def __init__(self, config: GenesisConfig):
        super().__init__()
        self.config = config
        
        # Embeddings
        self.tok_emb = nn.Embedding(config.vocab_size, config.n_embd)
        self.drop = nn.Dropout(config.dropout)
        
        # No positional embedding needed - RoPE in attention handles positions
        
        # Genesis blocks
        self.blocks = nn.ModuleList([
            GenesisBlock(config, i) for i in range(config.n_layer)
        ])
        
        # Metacognition (top of model)
        if config.use_ttt:
            self.metacognition = GenesisMetacognition(
                config.n_embd,
                rank=getattr(config, "ttt_rank", 8),
                inner_lr=getattr(config, "ttt_inner_lr", 0.01),
                mode=getattr(config, "ttt_mode", "dual"),
                lr_cap=getattr(config, "ttt_inner_lr", 0.01),
                inference_fast_path=getattr(config, "ttt_inference_fast_path", True),
            )
        else:
            self.metacognition = None
        
        # Final norm (v0.8.1: ZeroCenteredRMSNorm by default)
        NormClass = get_norm_class(config)
        self.ln_f = NormClass(config.n_embd, config.norm_eps)
        
        # Output head
        self.lm_head = nn.Linear(config.n_embd, config.vocab_size, bias=False)
        
        # Weight tying
        if config.tie_word_embeddings:
            self.tok_emb.weight = self.lm_head.weight
        
        # Initialize
        self.apply(self._init_weights)
        
        # Print architecture summary
        self._print_summary()
        
    def _init_weights(self, module):
        """Initialize weights with µP scaling (Cerebras/EleutherAI reference).
        
        With weight tying (lm_head.weight = tok_emb.weight), the output layer
        inherits embedding init. The 1/width scaling is applied in the forward
        pass via output_alpha / width_mult.
        """
        # µP width multiplier for hidden layers
        if getattr(self.config, 'use_mup', False):
            base_width = getattr(self.config, 'mup_base_width', 256)
            width_mult = self.config.n_embd / base_width
        else:
            width_mult = 1.0
        
        if isinstance(module, nn.Linear):
            # µP: scale hidden layer init by 1/sqrt(width)
            std = self.config.init_std / math.sqrt(width_mult) if width_mult > 1 else self.config.init_std
            torch.nn.init.normal_(module.weight, mean=0.0, std=std)
            if module.bias is not None:
                torch.nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            torch.nn.init.normal_(module.weight, mean=0.0, std=self.config.init_std)
    
    def _print_summary(self):
        """Print model architecture summary (2.0.0: cleaned up)."""
        n_params = sum(p.numel() for p in self.parameters()) / 1e6
        
        # Count hybrid layout layers
        n_full_attn = sum(1 for b in self.blocks if getattr(b, 'use_full_attention', False))
        n_linear_attn = self.config.n_layer - n_full_attn
        
        print(f"\n{'='*70}")
        print(f"  GENESIS 2.0.0 ({n_params:.2f}M params)")
        print(f"{'='*70}")
        print(f"  Architecture:")
        print(f"    ├─ Layers: {self.config.n_layer}")
        print(f"    ├─ Embedding: {self.config.n_embd}")
        print(f"    ├─ Heads: {self.config.n_head} (KV: {self.config.n_kv_head})")
        print(f"    └─ Context: {self.config.block_size}")
        print(f"")
        print(f"  Attention:")
        if getattr(self.config, 'use_hybrid_layout', False):
            ratio = getattr(self.config, 'hybrid_full_attn_ratio', 0.25)
            print(f"    ├─ Hybrid Layout: {n_linear_attn} GLA + {n_full_attn} FoX")
        print(f"    ├─ GLA (O(n)): {'✓' if self.config.use_gla else '✗'}")
        print(f"    └─ FoX: {'✓' if getattr(self.config, 'use_fox', False) else '✗'}")
        print(f"")
        print(f"  Features:")
        # Only show enabled features
        if self.config.use_ttt:
            print(f"    ├─ TTT: ✓ (rank={getattr(self.config, 'ttt_rank', 8)})")
        if getattr(self.config, 'use_mup', False):
            print(f"    ├─ µP: ✓ (base={getattr(self.config, 'mup_base_width', 256)})")
        if getattr(self.config, 'use_selective_activation', False):
            print(f"    └─ Selective Act: ✓ (k={int(getattr(self.config, 'selective_k_ratio', 0.5)*100)}%)")
        print(f"{'='*70}\n")
    
    def get_num_params(self, non_embedding: bool = True) -> int:
        """Count parameters."""
        n = sum(p.numel() for p in self.parameters())
        if non_embedding:
            n -= self.tok_emb.weight.numel()
        return n
    
    # =========================================================================
    # Segment-Level Recurrence (v0.8.2)
    # =========================================================================
    
    def init_segment_states(self, batch_size: int, device: torch.device = None):
        """
        Initialize segment states for all GLA layers.
        
        Call this at the beginning of a document or when batch size changes.
        
        Args:
            batch_size: batch size for state tensors
            device: device to create tensors on (default: model device)
        """
        if device is None:
            device = next(self.parameters()).device
        
        self._segment_states = {}
        for i, block in enumerate(self.blocks):
            if not hasattr(block, 'attn') or not isinstance(block.attn, GatedLinearAttention):
                continue
            attn = block.attn
            state_key_dim = getattr(attn, "head_qk_dim", getattr(attn, "head_dim", None))
            state_value_dim = getattr(attn, "head_v_dim", getattr(attn, "head_dim", None))
            if state_key_dim is None or state_value_dim is None:
                continue
            self._segment_states[i] = torch.zeros(
                batch_size,
                attn.n_head,
                state_key_dim,
                state_value_dim,
                device=device,
                dtype=next(self.parameters()).dtype,
            )
    
    def reset_segment_states(self):
        """Reset all segment states to zero (call at document boundaries)."""
        if hasattr(self, '_segment_states'):
            for key in self._segment_states:
                self._segment_states[key].zero_()
    
    def get_segment_states(self) -> dict:
        """Get current segment states (for checkpointing)."""
        if hasattr(self, '_segment_states'):
            return {k: v.clone() for k, v in self._segment_states.items()}
        return {}
    
    def set_segment_states(self, states: dict):
        """Set segment states (for resuming from checkpoint)."""
        self._segment_states = {k: v.clone() for k, v in states.items()}
    
    # =========================================================================
    # Selective Activation (v0.8.3)
    # =========================================================================
    
    def init_sparsity_scheduler(self):
        """
        Initialize sparsity scheduler for all FFN layers.
        
        Creates a shared SparsityScheduler based on config and attaches it
        to all SwiGLU layers in the model.
        """
        from .layers.ffn import SparsityScheduler
        
        self._sparsity_scheduler = SparsityScheduler(
            initial_k=1.0,  # Start fully dense
            final_k=getattr(self.config, 'selective_k_ratio', 0.5),
            warmup_steps=getattr(self.config, 'selective_warmup_steps', 1000),
            sparsify_steps=getattr(self.config, 'selective_sparsify_steps', 10000),
            schedule=getattr(self.config, 'selective_schedule', 'cubic'),
        )
        
        # Attach to all FFN layers
        for block in self.blocks:
            if hasattr(block, 'ffn') and hasattr(block.ffn, 'set_k_scheduler'):
                block.ffn.set_k_scheduler(self._sparsity_scheduler)
    
    def sparsity_step(self):
        """Advance sparsity scheduler by one step (call after each training step)."""
        if hasattr(self, '_sparsity_scheduler'):
            self._sparsity_scheduler.step()
    
    def set_sparsity_step(self, step: int):
        """Set sparsity scheduler step directly (for resuming training)."""
        if hasattr(self, '_sparsity_scheduler'):
            self._sparsity_scheduler.set_step(step)
    
    def get_current_sparsity(self) -> float:
        """Get current sparsity level (1 - k_ratio)."""
        if hasattr(self, '_sparsity_scheduler'):
            return 1.0 - self._sparsity_scheduler.get_k()
        return 0.0
    
    def get_ffn_sparsity_stats(self) -> dict:
        """Get sparsity statistics from FFN layers."""
        stats = {'avg_sparsity': 0.0, 'layers': []}
        count = 0
        for i, block in enumerate(self.blocks):
            if hasattr(block, 'ffn') and hasattr(block.ffn, '_last_sparsity'):
                stats['layers'].append({
                    'layer': i,
                    'sparsity': block.ffn._last_sparsity
                })
                stats['avg_sparsity'] += block.ffn._last_sparsity
                count += 1
        if count > 0:
            stats['avg_sparsity'] /= count
        return stats
    
    def freeze_sparsity(self):
        """
        Freeze sparsity at current level (stop annealing).
        
        Call this when LR enters decay phase to:
        - Preserve model capacity in final training
        - Avoid over-pruning during low-LR phase
        
        Reference: N:M Sparse Training (ICML 2022)
        """
        if hasattr(self, '_sparsity_scheduler'):
            self._sparsity_scheduler.freeze()
            return True
        return False
    
    def is_sparsity_frozen(self) -> bool:
        """Check if sparsity schedule is frozen."""
        if hasattr(self, '_sparsity_scheduler'):
            return getattr(self._sparsity_scheduler, '_frozen', False)
        return False
    
    def set_selective_activation(
        self,
        enabled: bool,
        k_ratio: float = 0.90,
        selective_activation_in_eval: Optional[bool] = None,  # DEPRECATED: ignored
    ):
        """
        Enable or disable Selective Activation on all SwiGLU layers.
        
        v2.4.5: Simplified - SA now always active when enabled=True.
        The selective_activation_in_eval parameter is deprecated and ignored.
        
        Args:
            enabled: Whether to enable selective activation
            k_ratio: Fraction of neurons to keep (0.0-1.0)
            selective_activation_in_eval: DEPRECATED - ignored (kept for backward compatibility)
        
        Returns:
            Number of layers updated
        """
        count = 0
        for block in self.blocks:
            if hasattr(block, 'ffn') and hasattr(block.ffn, 'use_selective_activation'):
                block.ffn.use_selective_activation = enabled
                if hasattr(block.ffn, '_k_ratio'):
                    block.ffn._k_ratio = k_ratio
                count += 1
        
        # Also update config for consistency
        if hasattr(self, 'config'):
            self.config.use_selective_activation = enabled
            self.config.selective_k_ratio = k_ratio
        
        return count
    
    def estimate_effective_flops(self, batch_size: int, seq_len: int) -> dict:
        """
        Estimate THEORETICAL FLOPs considering sparsity and hybrid attention.
        
        ⚠️ WARNING: This is a THEORETICAL estimate, NOT actual throughput.
        - Selective Activation masking does NOT reduce GPU compute (dense GEMMs still run)
        - Real speedup requires sparse kernels (N:M sparsity, Spark-style, etc.)
        - Use this for paper comparisons only, not performance claims
        
        v2.1.0: Properly differentiates GLA O(T) vs FoX O(T²) complexity.
        
        Returns dict with:
        - dense_flops: Theoretical FLOPs without any sparsity
        - effective_flops: Theoretical FLOPs with current sparsity applied
        - ffn_reduction: % theoretical reduction in FFN FLOPs
        - gla_flops: FLOPs from GLA layers (O(T) per layer)
        - fox_flops: FLOPs from FoX/full attention layers (O(T²) per layer)
        - n_gla_layers / n_fox_layers: Layer counts
        - is_theoretical: Always True (reminder this isn't real throughput)
        """
        config = self.config
        d = config.n_embd
        T = seq_len
        B = batch_size
        
        # Count layer types
        n_fox_layers = sum(1 for b in self.blocks if getattr(b, 'use_full_attention', False))
        n_gla_layers = config.n_layer - n_fox_layers
        
        # FFN FLOPs per layer (SwiGLU: 3 * d * intermediate * 2)
        # Note: Selective Activation mask does NOT reduce these in practice
        ffn_intermediate = getattr(config, 'intermediate_size', d * 4)
        ffn_flops_per_token = 3 * d * ffn_intermediate * 2  # gate, up, down projections
        
        # =========================================================================
        # Attention FLOPs: GLA vs FoX have DIFFERENT complexity
        # =========================================================================
        
        # GLA (Gated Linear Attention): O(T) per layer
        # - QKV projections: 3 * d * d * 2 (or with GQA: 2*d*d + 2*d*(d/ratio))
        # - Gate projection: d * d * 2
        # - State update: O(d²) per token (constant, not T-dependent)
        # - Output projection: d * d * 2
        # Total: ~8 * d² per token (independent of T)
        gla_attn_flops_per_token = 8 * d * d
        
        # FoX / Full Attention: O(T²) per layer
        # - QKV projections: same as above
        # - Attention scores: T * d (per token, so T² total for sequence)
        # - Attention output: T * d (per token)
        # - Output projection: d * d * 2
        # For per-token: we need to account for the T factor in attention
        fox_attn_flops_per_token = 8 * d * d + 2 * T * d  # O(T) component
        
        # =========================================================================
        # Total FLOPs calculation
        # =========================================================================
        
        # Dense FLOPs (no sparsity)
        gla_total_per_token = n_gla_layers * (ffn_flops_per_token + gla_attn_flops_per_token)
        fox_total_per_token = n_fox_layers * (ffn_flops_per_token + fox_attn_flops_per_token)
        dense_flops_per_token = gla_total_per_token + fox_total_per_token
        
        # Apply THEORETICAL sparsity to FFN (reminder: not real GPU savings)
        current_k = 1.0 - self.get_current_sparsity()  # active ratio
        # Only down_proj could theoretically benefit (gate/up still dense)
        # Realistic reduction: only 1/3 of FFN (down_proj with sparse input)
        theoretical_ffn_reduction = (1.0 - current_k) / 3  # Conservative estimate
        effective_ffn_flops = ffn_flops_per_token * (1 - theoretical_ffn_reduction)
        
        gla_effective_per_token = n_gla_layers * (effective_ffn_flops + gla_attn_flops_per_token)
        fox_effective_per_token = n_fox_layers * (effective_ffn_flops + fox_attn_flops_per_token)
        effective_flops_per_token = gla_effective_per_token + fox_effective_per_token
        
        # Total for batch
        dense_flops = dense_flops_per_token * T * B
        effective_flops = effective_flops_per_token * T * B
        
        # Separate GLA vs FoX totals (for analysis)
        gla_flops_total = gla_total_per_token * T * B
        fox_flops_total = fox_total_per_token * T * B
        
        return {
            # Core metrics
            'dense_flops': dense_flops,
            'effective_flops': effective_flops,
            'flops_per_token': effective_flops_per_token,
            'speedup_ratio': dense_flops / effective_flops if effective_flops > 0 else 1.0,
            
            # FFN sparsity (theoretical only)
            'ffn_reduction_pct': theoretical_ffn_reduction * 100,
            'selective_k_ratio': current_k,
            
            # GLA vs FoX breakdown
            'n_gla_layers': n_gla_layers,
            'n_fox_layers': n_fox_layers,
            'gla_flops': gla_flops_total,
            'fox_flops': fox_flops_total,
            'gla_pct': gla_flops_total / dense_flops * 100 if dense_flops > 0 else 0,
            'fox_pct': fox_flops_total / dense_flops * 100 if dense_flops > 0 else 0,
            
            # Complexity info
            'gla_complexity': 'O(T)',
            'fox_complexity': 'O(T²)',
            
            # Reminder flag
            'is_theoretical': True,
            'warning': 'Selective Activation mask does NOT reduce real GPU compute',
        }
    
    def forward(
        self,
        idx: torch.Tensor,
        targets: Optional[torch.Tensor] = None,
        past_key_values: Optional[List[Any]] = None,
        use_cache: bool = False,
    ) -> Tuple[torch.Tensor, Optional[torch.Tensor], GenesisMetrics]:
        """
        Forward pass.
        
        Args:
            idx: [B, T] input token IDs
            targets: [B, T] target token IDs (optional)
            past_key_values: List of KV caches for each layer
            use_cache: Whether to return new KV caches
            
        Returns:
            logits: [B, T, vocab_size]
            loss: scalar loss (if targets provided)
            metrics: comprehensive metrics
            (optional) past_key_values: if use_cache=True
        """
        B, T = idx.shape
        
        # Embeddings
        x = self.tok_emb(idx)
        x = self.drop(x)
        
        # Process through blocks
        total_aux_loss = 0.0
        
        # v0.8.2: Segment-level recurrence support
        use_recurrence = getattr(self.config, 'use_segment_recurrence', False)
        enable_cache_recurrence = bool(use_cache) and (not self.training)
        if enable_cache_recurrence:
            use_recurrence = True
            needs_init = True
            if hasattr(self, "_segment_states") and isinstance(self._segment_states, dict) and len(self._segment_states) > 0:
                first_state = next(iter(self._segment_states.values()))
                needs_init = (not torch.is_tensor(first_state)) or (first_state.shape[0] != B) or (first_state.device != idx.device)
            if needs_init:
                self.init_segment_states(B, device=idx.device)
            if past_key_values is None:
                self.reset_segment_states()
                for block in self.blocks:
                    attn = getattr(block, "attn", None)
                    if attn is None:
                        continue
                    for key in ("_conv_cache_q", "_conv_cache_k", "_conv_cache_v", "_k_conv_cache", "_v_conv_cache"):
                        if hasattr(attn, key):
                            setattr(attn, key, None)
        elif use_recurrence and (not hasattr(self, "_segment_states") or len(getattr(self, "_segment_states", {})) == 0):
            self.init_segment_states(B, device=idx.device)
        has_states = hasattr(self, '_segment_states') and len(self._segment_states) > 0
        
        cache_position_offset = 0
        if past_key_values is not None:
            for kv in past_key_values:
                if kv is None:
                    continue
                if isinstance(kv, dict) and "position_offset" in kv:
                    cache_position_offset = int(kv["position_offset"])
                    break
                if isinstance(kv, tuple) and len(kv) > 0 and torch.is_tensor(kv[0]) and kv[0].dim() >= 3:
                    cache_position_offset = int(kv[0].shape[2])
                    break

        current_key_values = [] if use_cache else None
        
        for i, block in enumerate(self.blocks):
            use_ckpt = self.config.use_gradient_checkpointing and self.training
            
            # Get past state for this block (if segment recurrence enabled)
            past_state = None
            return_state = False
            
            # Handle KV Cache (FoX/Attention)
            layer_past_kv = None
            if past_key_values is not None and i < len(past_key_values):
                layer_past_kv = past_key_values[i]
            
            if use_recurrence and has_states and i in self._segment_states:
                past_state = self._segment_states[i]
                return_state = True
            
            if use_ckpt:
                # Note: gradient checkpointing doesn't support state passing
                x, aux = checkpoint(block, x, use_reentrant=False)
            elif return_state or use_cache:
                # Block call with state support
                block_out = block(
                    x, 
                    past_state=past_state, 
                    return_state=return_state,
                    past_key_value=layer_past_kv,
                    use_cache=use_cache,
                    position_offset=cache_position_offset,
                )
                
                # Unpack results: x, aux, [final_state], [final_kv]
                # GenesisBlock.forward returns: 
                # if return_state or use_cache: return x, aux_loss, final_state, current_key_value
                
                x, aux, new_state, new_kv = block_out
                
                if new_state is not None and use_recurrence:
                    self._segment_states[i] = new_state
                
                if use_cache:
                    current_key_values.append(new_kv)
            else:
                x, aux = block(x)
            total_aux_loss += aux
        
        ttt_strength = float(getattr(self.config, 'ttt_strength', 0.2))
        
        # v2.4.5: TTT only active during INFERENCE (not training)
        # TTT is designed for test-time adaptation, so it should NOT run during training
        if self.metacognition is not None and ttt_strength > 0.0 and (not use_cache) and not self.training:
            x_input = x
            x, reflection, meta_metrics = self.metacognition(x)
            
            conf = meta_metrics.get('confidence', 0.5)
            conf_val = conf.unsqueeze(-1) if torch.is_tensor(conf) else conf
            
            modulated_conf = conf_val * ttt_strength
            x = modulated_conf * x + (1.0 - modulated_conf) * x_input
            
            self._last_reflection = reflection
        else:
            meta_metrics = {}
            self._last_reflection = None
        
        # Final norm
        x = self.ln_f(x)
        
        # µP: scale output by alpha / width_mult before lm_head
        # v2.1.0: Apply µP scaling consistently for BOTH training AND inference
        # This ensures the model behaves the same way in both modes
        if getattr(self.config, 'use_mup', False):
            base_width = getattr(self.config, 'mup_base_width', 256)
            width_mult = self.config.n_embd / base_width
            output_alpha = getattr(self.config, 'mup_output_mult', 1.0)
            x = x * (output_alpha / width_mult)
        
        # Output logits
        if targets is not None:
            logits = self.lm_head(x)
            loss = F.cross_entropy(
                logits.view(-1, logits.size(-1)),
                targets.view(-1),
                ignore_index=-100,  # PyTorch standard for masked tokens
            )
            
            # Add auxiliary losses
            loss = loss + 0.001 * total_aux_loss
        else:
            # Efficient: only compute last token logits
            logits = self.lm_head(x[:, [-1], :])
            loss = None
        
        # Gather metrics
        metrics = self._gather_metrics(loss, total_aux_loss, meta_metrics)
        
        if use_cache:
            return logits, loss, metrics, current_key_values
            
        return logits, loss, metrics
    
    def _gather_metrics(
        self,
        loss: Optional[torch.Tensor],
        aux_loss: float,
        meta_metrics: Dict,
    ) -> GenesisMetrics:
        """Gather metrics from all components."""
        metrics = GenesisMetrics()
        
        if loss is not None:
            # capture_scalar_outputs=True permite .item()
            metrics.loss = loss.item()
            metrics.perplexity = math.exp(min(loss.item(), 20))
        
        metrics.aux_loss = aux_loss
        
        # From last block
        last_block = self.blocks[-1]
        if last_block.last_attn_metrics:
            m = last_block.last_attn_metrics
            # GLA-style metrics
            metrics.attention_gate_openness = getattr(m, 'gate_openness', 0.0)
            metrics.attention_forget_rate = getattr(m, 'forget_rate', 0.0)
            metrics.fox_effective_context = getattr(m, 'effective_context', 0.0)
        
        # Metacognition
        if meta_metrics:
            metrics.ttt_activated = True
            metrics.surprise_level = meta_metrics.get('surprise', 0.0)
            metrics.confidence = meta_metrics.get('confidence', 0.5)
        
        return metrics
    
    def configure_optimizers(
        self,
        weight_decay: float,
        learning_rate: float,
        betas: Tuple[float, float],
        device_type: str,
    ):
        """
        Configure AdamW optimizer with proper weight decay handling.
        
        v2.1.0 Update: Science-based weight decay rules
        Based on arXiv:2510.19093, LLaMA, GPT-NeoX, and ceramic.ai research:
        
        WEIGHT DECAY RULES:
        1. Linear weights (attention, FFN): YES weight decay
        2. Embeddings: NO weight decay (lookup tables, not matrix multiplies)
        3. ZeroCenteredRMSNorm omega: YES weight decay (decays to identity)
        4. Other 1D params (biases, norm weights): NO weight decay
        5. Mamba-style params (A_log, dt_bias): NO weight decay (marked _no_weight_decay)
        
        Research basis:
        - arXiv:2510.19093: "Weight Decay may matter more than muP for LR transfer"
        - StackExchange: Embeddings are lookup tables, decay doesn't make sense
        - LLaMA/GPT-NeoX: Don't decay embeddings or biases
        """
        # Separate parameters for weight decay
        decay_params = []
        no_decay_params = []
        
        for name, param in self.named_parameters():
            if not param.requires_grad:
                continue
            
            # Check for explicit no_weight_decay flag (Mamba-style params)
            if hasattr(param, '_no_weight_decay') and param._no_weight_decay:
                no_decay_params.append(param)
                continue
            
            # Weight decay rules (v2.1.0: Fixed embedding handling)
            if param.dim() >= 2:
                # 2D+ params: linear weights get decay, embeddings don't
                if 'tok_emb' in name or 'embed' in name.lower():
                    # Embeddings: NO weight decay (lookup tables)
                    no_decay_params.append(param)
                else:
                    # Linear layer weights: YES weight decay
                    decay_params.append(param)
            elif 'omega' in name:
                # ZeroCenteredRMSNorm omega: YES weight decay
                # This decays omega to 0, which means gamma decays to 1 (identity)
                decay_params.append(param)
            else:
                # 1D params (biases, standard norm weights): NO decay
                no_decay_params.append(param)
        
        optim_groups = [
            {'params': decay_params, 'weight_decay': weight_decay},
            {'params': no_decay_params, 'weight_decay': 0.0},
        ]
        
        # Use fused AdamW if available
        fused_available = 'fused' in inspect.signature(torch.optim.AdamW).parameters
        use_fused = fused_available and device_type == 'cuda'
        
        optimizer = torch.optim.AdamW(
            optim_groups,
            lr=learning_rate,
            betas=betas,
            fused=use_fused if use_fused else False,
        )
        
        # Log optimizer groups for verification
        n_decay = sum(p.numel() for p in decay_params)
        n_no_decay = sum(p.numel() for p in no_decay_params)
        print(f"⚙️ Optimizer: {len(decay_params)} decay tensors ({n_decay/1e6:.1f}M params)")
        print(f"             {len(no_decay_params)} no-decay tensors ({n_no_decay/1e6:.1f}M params)")
        
        return optimizer
    
    @torch.no_grad()
    def generate(
        self,
        idx: torch.Tensor,
        max_new_tokens: int,
        temperature: float = 1.0,
        top_k: Optional[int] = None,
        top_p: Optional[float] = None,
        repetition_penalty: float = 1.0,
        stop_tokens: Optional[List[int]] = None,
    ) -> torch.Tensor:
        """
        Generate tokens autoregressively (OPTIMIZED).
        
        Args:
            idx: [B, T] starting tokens
            max_new_tokens: how many tokens to generate
            temperature: sampling temperature
            top_k: top-k sampling
            top_p: nucleus sampling
            repetition_penalty: penalty for repeating tokens (1.0 = no penalty, >1.0 = discourage)
            stop_tokens: list of token IDs to stop generation (e.g., EOS)
            
        Returns:
            idx: [B, T + max_new_tokens] generated sequence
        """
        past_key_values = None
        
        for _ in range(max_new_tokens):
            # If using cache, we only feed the last token
            if past_key_values is not None:
                idx_cond = idx[:, -1:]
            else:
                # First step: feed context window (up to block size)
                idx_cond = idx if idx.size(1) <= self.config.block_size else idx[:, -self.config.block_size:]
            
            # Forward with cache
            # Note: We must handle the variable return size from forward
            forward_out = self.forward(
                idx_cond, 
                past_key_values=past_key_values, 
                use_cache=True
            )
            
            # Unpack (logits, loss, metrics, past_key_values)
            logits = forward_out[0]
            past_key_values = forward_out[3]
            
            logits = logits[:, -1, :]
            
            # Repetition penalty (applied to raw logits for consistency)
            if repetition_penalty != 1.0:
                # Get unique tokens in the sequence
                for b in range(idx.size(0)):
                    prev_tokens = idx[b].unique()
                    # Apply penalty: if logit > 0, divide; if < 0, multiply
                    # This discourages tokens that have already appeared
                    mask = torch.zeros_like(logits[b], dtype=torch.bool)
                    mask[prev_tokens] = True
                    
                    # Vectorized penalty application
                    logits[b] = torch.where(
                        mask,
                        torch.where(logits[b] > 0, logits[b] / repetition_penalty, logits[b] * repetition_penalty),
                        logits[b]
                    )
            
            # Apply temperature scaling after penalty
            logits = logits / temperature
            
            # Top-k filtering
            if top_k is not None:
                v, _ = torch.topk(logits, min(top_k, logits.size(-1)))
                logits[logits < v[:, [-1]]] = float('-inf')
            
            # Top-p (nucleus) filtering
            if top_p is not None:
                sorted_logits, sorted_indices = torch.sort(logits, descending=True)
                cumulative_probs = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)
                
                sorted_indices_to_remove = cumulative_probs > top_p
                sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
                sorted_indices_to_remove[..., 0] = 0
                
                indices_to_remove = sorted_indices_to_remove.scatter(1, sorted_indices, sorted_indices_to_remove)
                logits[indices_to_remove] = float('-inf')
            
            # Sample
            probs = F.softmax(logits, dim=-1)
            idx_next = torch.multinomial(probs, num_samples=1)
            
            # Check for stop tokens
            if stop_tokens is not None:
                if idx_next.item() in stop_tokens:
                    idx = torch.cat([idx, idx_next], dim=1)
                    break
            
            # Append
            idx = torch.cat([idx, idx_next], dim=1)
        
        return idx
    
    def get_architecture_analysis(self) -> Dict:
        """Get detailed architecture analysis (2.0.0: simplified)."""
        analysis = {
            'model': 'Genesis 2.0.0',
            'params_millions': self.get_num_params() / 1e6,
            'config': {
                'n_layer': self.config.n_layer,
                'n_embd': self.config.n_embd,
                'n_head': self.config.n_head,
                'block_size': self.config.block_size,
            },
            'features': {
                'gla': self.config.use_gla,
                'fox': getattr(self.config, 'use_fox', False),
                'ttt': self.config.use_ttt,
                'selective_activation': getattr(self.config, 'use_selective_activation', False),
                'mup': getattr(self.config, 'use_mup', False),
            },
            'efficiency': {
                'attention_complexity': 'O(n)' if self.config.use_gla else 'O(n²)',
                'memory_efficient': self.config.use_gradient_checkpointing,
            },
        }
        return analysis
