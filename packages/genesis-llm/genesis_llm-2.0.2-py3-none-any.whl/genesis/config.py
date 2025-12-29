"""
Genesis Configuration v3.0.0 "Proxy + Target"
==============================================

Configuration for the Genesis neural architecture.

Available configs:
- genesis_147m(): ~147M params - µP validation model (SmolLM-135M style)
- genesis_sweetspot(): ~398M params - Target production model

Active Features:
1. Hybrid Layout - 75% GLA + 25% FoX (Qwen3-Next style)
2. GLA - Gated DeltaNet with delta rule (ICLR 2025)
3. FoX - Forgetting Attention with NoPE (ICLR 2025)
4. TTT - Test-Time Training for adaptation (MIT 2024)
5. Selective Activation - Top-k FFN sparsity
6. µP - Maximal Update Parametrization for HP transfer
"""

from dataclasses import dataclass


@dataclass
class GenesisConfig:
    """
    Configuration for Genesis model.
    
    Two-model workflow:
    1. Train genesis_proxy() to validate HPs (~147M, ~3x faster)
    2. Transfer HPs to genesis_sweetspot() via µP (~398M)
    """
    
    # ==========================================================================
    # Core Architecture
    # ==========================================================================
    
    vocab_size: int = 50304          # GPT-2 vocab padded to multiple of 64
    n_embd: int = 768                # Embedding dimension
    n_layer: int = 12                # Number of Genesis blocks
    block_size: int = 1024           # Maximum sequence length
    
    # ==========================================================================
    # Gated DeltaNet (GLA v2) - ICLR 2025
    # ==========================================================================
    
    n_head: int = 12                 # Number of attention heads
    n_kv_head: int = 4               # KV heads (GQA-style, 3:1 ratio)
    head_dim: int = 64               # Per-head dimension
    
    use_gla: bool = True
    gla_expand_k: float = 1.0
    gla_expand_v: float = 1.0
    gla_gate_fn: str = "swish"
    gla_use_short_conv: bool = True
    gla_conv_size: int = 4
    gla_chunk_size: int = 64
    gla_use_delta_rule: bool = True
    gla_qk_norm: str = "l2"
    gla_use_mamba_gate: bool = True
    gla_gate_logit_normalizer: int = 16
    gla_fuse_norm_gate: bool = True
    gla_use_dynamic_lr: bool = True
    
    # ==========================================================================
    # Hybrid Attention Layout (Qwen3-Next Style)
    # ==========================================================================
    
    use_hybrid_layout: bool = True
    hybrid_full_attn_ratio: float = 0.25  # 25% full attention (FoX) layers
    
    # ==========================================================================
    # FoX (Forgetting Attention) - ICLR 2025
    # ==========================================================================
    
    use_fox: bool = True
    use_fox_pro: bool = True
    
    # ==========================================================================
    # Test-Time Training (TTT) - MIT 2024
    # ==========================================================================
    
    use_ttt: bool = True
    ttt_inner_lr: float = 0.01
    ttt_rank: int = 8
    ttt_mode: str = "dual"
    ttt_chunk_size: int = 64
    
    # ==========================================================================
    # Training
    # ==========================================================================
    
    dropout: float = 0.0
    norm_eps: float = 1e-6
    init_std: float = 0.02
    use_gradient_checkpointing: bool = False
    tie_word_embeddings: bool = True
    
    # ==========================================================================
    # Normalization
    # ==========================================================================
    
    use_zero_centered_norm: bool = True
    use_fused_norm: bool = True
    
    # ==========================================================================
    # Segment-Level Recurrence
    # ==========================================================================
    
    use_segment_recurrence: bool = False
    segment_state_detach: bool = True
    
    # ==========================================================================
    # Selective Activation
    # ==========================================================================
    
    use_selective_activation: bool = True
    selective_k_ratio: float = 0.5
    selective_use_soft_mask: bool = True
    selective_mask_temperature: float = 0.1
    selective_warmup_steps: int = 1000
    selective_sparsify_steps: int = 10000
    selective_schedule: str = "cubic"
    
    # ==========================================================================
    # µP (Maximal Update Parametrization)
    # ==========================================================================
    
    use_mup: bool = False
    mup_base_width: int = 256
    mup_output_mult: float = 1.0
    mup_embed_mult: float = 1.0
    
    # ==========================================================================
    # Computed Properties
    # ==========================================================================
    
    @property
    def intermediate_size(self) -> int:
        """FFN intermediate size (2.5x for SwiGLU efficiency)."""
        return int(self.n_embd * 2.5)
    
    @property
    def total_head_dim(self) -> int:
        """Total dimension for all heads."""
        return self.n_head * self.head_dim
    
    def __post_init__(self):
        """Validate configuration."""
        assert self.n_embd % self.n_head == 0, "n_embd must be divisible by n_head"
        assert self.n_head % self.n_kv_head == 0, "n_head must be divisible by n_kv_head"
        
        computed_head_dim = self.n_embd // self.n_head
        if self.head_dim != computed_head_dim:
            self.head_dim = computed_head_dim
    
    # ==========================================================================
    # PROXY MODEL (~147M) - For HP validation before scaling
    # ==========================================================================
    
    @classmethod
    def genesis_147m(cls) -> "GenesisConfig":
        """
        Genesis 147M - µP VALIDATION MODEL (SmolLM-135M style)
        
        =====================================================================
        PURPOSE: HP tuning and scaling validation before training target
        =====================================================================
        
        Architecture based on SmolLM-135M (HuggingFace, 2024):
        - Deep-and-thin: 30L × 576D (proven efficient for small models)
        - GQA 3:1 ratio (9 heads : 3 KV heads)
        - Same width as would scale to target for clean µP transfer
        
        Training workflow:
        1. Grid search LR ∈ {0.001, 0.003, 0.005, 0.01} on 500M tokens
        2. Best HP transfers to genesis_sweetspot via µP
        3. Validate loss scaling matches Chinchilla expectations
        
        Expected:
        - ~147M params (37% of target)
        - ~3x faster training than target
        - Full feature parity for accurate validation
        """
        return cls(
            # SmolLM-135M style: Deep-and-Thin (30L × 576D)
            n_embd=576,
            n_layer=30,
            n_head=9,
            n_kv_head=3,
            head_dim=64,
            block_size=2048,         # Full context for curriculum training
            vocab_size=50304,
            
            # Hybrid Layout - 25% FoX
            use_hybrid_layout=True,
            hybrid_full_attn_ratio=0.25,
            
            # GLA - Full features (GatedDeltaNet ICLR 2025)
            use_gla=True,
            gla_expand_k=0.75,       # Asymmetric expansion
            gla_expand_v=1.5,
            gla_gate_fn="swish",
            gla_use_short_conv=True,
            gla_conv_size=4,
            gla_chunk_size=64,
            gla_use_delta_rule=True,
            gla_qk_norm="l2",
            gla_use_mamba_gate=True,
            gla_gate_logit_normalizer=16,
            gla_fuse_norm_gate=True,
            gla_use_dynamic_lr=True,
            
            # FoX - Full features
            use_fox=True,
            use_fox_pro=True,
            
            # TTT - Scaled rank for proxy
            use_ttt=True,
            ttt_inner_lr=0.01,
            ttt_rank=4,              # Smaller rank for proxy
            ttt_mode="dual",
            ttt_chunk_size=64,
            
            # Selective Activation - DISABLED for HP search
            use_selective_activation=False,
            
            # µP - Enabled
            use_mup=True,
            mup_base_width=256,
            mup_output_mult=1.0,
            mup_embed_mult=1.0,
            
            # Normalization
            use_zero_centered_norm=True,
            use_fused_norm=True,
            
            # Training
            dropout=0.0,
            norm_eps=1e-6,
            init_std=0.02,
            use_gradient_checkpointing=False,
            tie_word_embeddings=True,
        )
    
    # ==========================================================================
    # TARGET MODEL (~398M) - Production model
    # ==========================================================================
    
    @classmethod
    def genesis_sweetspot(cls) -> "GenesisConfig":
        """
        Genesis Sweetspot (~398M) - PRODUCTION TARGET MODEL
        
        =====================================================================
        RESEARCH BASIS (Dec 2025):
        =====================================================================
        
        1. HYBRID RATIO (arXiv 2507.06457):
           "GatedDeltaNet with linear-to-full ratio between 3:1 and 6:1"
           → 5:1 ratio (83% GLA + 17% FoX) = optimal efficiency/recall
        
        2. SCALE FOR COMPLEX ARCHITECTURES:
           - GLA + Delta Rule: efficient at any scale
           - FoX layers: benefit starts at >100M
           - TTT: significant benefit at >300M (state scaling)
           - Total overhead ~25% → amortized at ~350M
        
        3. DEEP-AND-THIN (MobileLLM/SmolLM2):
           - 32 layers × 960 hidden = proven efficient ratio
           - GQA 3:1 (15 heads : 5 KV heads)
        
        4. µP TRANSFER:
           - Uses HPs validated on genesis_proxy
           - Width multiplier: 960/576 = 1.67x
        
        =====================================================================
        
        Expected:
        - ~398M total parameters
        - ~80% parameter efficiency
        - 2K context capability
        - All innovations fully leveraged
        """
        return cls(
            # Deep-and-Thin: 32L × 960D
            n_embd=960,
            n_layer=32,
            n_head=15,
            n_kv_head=5,
            head_dim=64,
            block_size=2048,
            vocab_size=50304,
            
            # Hybrid Layout - 5:1 ratio (83% GLA + 17% FoX)
            use_hybrid_layout=True,
            hybrid_full_attn_ratio=0.1875,  # 6/32 = 18.75%
            
            # GLA - GatedDeltaNet (NVIDIA ICLR 2025)
            use_gla=True,
            gla_expand_k=0.75,
            gla_expand_v=1.5,
            gla_gate_fn="swish",
            gla_use_short_conv=True,
            gla_conv_size=4,
            gla_chunk_size=64,
            gla_use_delta_rule=True,
            gla_qk_norm="l2",
            gla_use_mamba_gate=True,
            gla_gate_logit_normalizer=16,
            gla_fuse_norm_gate=True,
            gla_use_dynamic_lr=True,
            
            # FoX - Forgetting Attention
            use_fox=True,
            use_fox_pro=True,
            
            # TTT - Optimal rank for 350M+
            use_ttt=True,
            ttt_inner_lr=0.01,
            ttt_rank=12,
            ttt_mode="dual",
            ttt_chunk_size=64,
            
            # Selective Activation - DISABLED for pre-training
            # Enable for fine-tuning (k_ratio=0.85)
            use_selective_activation=False,
            
            # µP - Transfer from proxy
            use_mup=True,
            mup_base_width=256,
            mup_output_mult=1.0,
            mup_embed_mult=1.0,
            
            # Normalization
            use_zero_centered_norm=True,
            use_fused_norm=True,
            
            # Training
            dropout=0.0,
            norm_eps=1e-6,
            init_std=0.02,
            use_gradient_checkpointing=False,  # Not needed on 80GB
            tie_word_embeddings=True,
        )
    
    # ==========================================================================
    # CONFIG SUMMARY
    # ==========================================================================
    #
    # | Config           | Params  | Layers | Width | Heads | Context | Purpose     |
    # |------------------|---------|--------|-------|-------|---------|-------------|
    # | genesis_147m     | ~147M   | 30     | 576   | 9/3   | 1024    | HP tuning   |
    # | genesis_sweetspot| ~398M   | 32     | 960   | 15/5  | 2048    | Production  |
    #
    # WORKFLOW:
    # 1. Train genesis_147m on 1B tokens to find optimal LR
    # 2. Transfer HPs to genesis_sweetspot via µP
    # 3. Train genesis_sweetspot on 15B+ tokens
    #
    # µP validated: LR=0.001 optimal (see mup_mutransfer.png)
    # ==========================================================================
