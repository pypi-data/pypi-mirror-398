"""
Genesis Dynamics v2.0.0
========================

Dynamic computation mechanisms.

v2.0.0 CLEANUP:
- EventRouter removed (overhead > benefit at <1B scale)
- LiquidLayer removed (overhead > benefit at <1B scale)

Components:
- ttt.py: Test-Time Training for adaptation (MIT 2024)
"""

from .ttt import TTTLayer, GenesisMetacognition

__all__ = [
    "TTTLayer",
    "GenesisMetacognition",
]
