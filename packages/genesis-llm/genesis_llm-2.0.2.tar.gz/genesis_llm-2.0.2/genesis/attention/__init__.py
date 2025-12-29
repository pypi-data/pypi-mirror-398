"""
Genesis Attention v2.0.0
========================

Hybrid Layout (Qwen3-Next style):

75% of layers - GLA (Gated DeltaNet):
- O(n) linear attention with delta rule (NVIDIA, ICLR 2025)

25% of layers - FoX:
- Softmax with forget gate, NoPE (ICLR 2025)

Module structure:
- base.py: GLA (Gated DeltaNet)
- forgetting.py: FoX (Forgetting Attention)
- gated_attention.py: Softmax + gate (fallback)
- utils.py: Utilities
"""

from .base import GatedLinearAttention, GLAMetrics
from .gated_attention import GatedAttention, GatedAttentionMetrics, HybridAttentionBlock
from .forgetting import ForgettingAttention, FoXMetrics, FoXLayer
from .utils import chunk_linear_attention, repeat_kv, ShortConvolution

__all__ = [
    # Core GLA (Gated DeltaNet)
    "GatedLinearAttention",
    "GLAMetrics",
    # Gated Attention (Qwen3-Next style)
    "GatedAttention",
    "GatedAttentionMetrics",
    "HybridAttentionBlock",
    # FoX (Forgetting Attention) - v1.1.0
    "ForgettingAttention",
    "FoXMetrics",
    "FoXLayer",
    # Utilities (for custom implementations)
    "chunk_linear_attention",
    "repeat_kv",
    "ShortConvolution",
]
