"""
Genesis Layers v2.0.0
=====================

Core building blocks for the Genesis architecture.

Components:
- norms.py: RMSNorm, ZeroCenteredRMSNorm, FusedRMSNormSwishGate, RoPE
- ffn.py: SwiGLU with Selective Activation
- mup.py: µP Maximal Update Parametrization (Microsoft 2021)
"""

from .norms import (
    RMSNorm, 
    QKNorm, 
    ZeroCenteredRMSNorm, 
    FusedRMSNormSwishGate,
    RotaryPositionalEmbedding,
    LayerScale,
)
from .ffn import SwiGLU
from .mup import (
    get_mup_param_groups,
    mup_init_,
    get_mup_info,
    MuReadout,
    configure_mup_optimizer,
)

__all__ = [
    "RMSNorm",
    "QKNorm",
    "ZeroCenteredRMSNorm",
    "FusedRMSNormSwishGate",
    "RotaryPositionalEmbedding",
    "LayerScale",
    "SwiGLU",
    "get_mup_param_groups",
    "mup_init_",
    "get_mup_info",
    "MuReadout",
    "configure_mup_optimizer",
]
