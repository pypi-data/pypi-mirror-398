"""
Genesis 2.0.0 - Efficient Neural Genesis
==========================================

Clean, efficient architecture for <1B scale LLMs.

2.0.0 CLEANUP - "Efficiency First":
Removed features with overhead > benefit at <1B scale:
- MoE, Event-Driven, Liquid, MTP
- MoM, Differential Attention
- DeltaProduct, Vector Gating

Active Features:
1. GLA (Gated DeltaNet) - O(n) linear attention (ICLR 2025)
2. FoX (Forgetting Attention) - Softmax + forget gate (ICLR 2025)
3. TTT (Test-Time Training) - Self-evolution (MIT 2024)
4. Selective Activation - Top-k FFN sparsity
5. µP - Hyperparameter transfer (Microsoft 2021)

Hybrid Layout (Qwen3-Next style):
- 75% GLA layers (O(n), efficient)
- 25% FoX layers (precise retrieval)
"""

from .config import GenesisConfig
from .model import Genesis, GenesisMetrics
from .layers import RMSNorm, SwiGLU, configure_mup_optimizer, get_mup_param_groups, mup_init_
from .attention import (
    GatedLinearAttention, 
    GatedAttention,
    ForgettingAttention,
    FoXMetrics,
)
from .dynamics import GenesisMetacognition, TTTLayer
from .tokenizer import (
    get_tokenizer,
    TiktokenWrapper,
    SmallBPETokenizer,
    CharTokenizer,
    format_chat,
)

__version__ = "2.0.0"
__codename__ = "Efficiency First"

__all__ = [
    # Config
    "GenesisConfig",
    # Model
    "Genesis",
    "GenesisMetrics",
    # Layers
    "RMSNorm",
    "SwiGLU",
    # µP
    "configure_mup_optimizer",
    "get_mup_param_groups",
    "mup_init_",
    # Attention
    "GatedLinearAttention",
    "GatedAttention",
    "ForgettingAttention",
    "FoXMetrics",
    # Dynamics
    "GenesisMetacognition",
    "TTTLayer",
    # Tokenizer
    "get_tokenizer",
    "TiktokenWrapper",
    "SmallBPETokenizer",
    "CharTokenizer",
    "format_chat",
]
