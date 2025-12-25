"""
Main entry point for the LLM framework.
Provides consolidated imports for all components, models, and configs.
"""

from .model import Model
from .component import Component
from .configs import (
    Config,
    tiny_config,
    small_config,
    medium_config,
    large_config,
    xl_config,
    embedding_config,
    attention_config,
    ffn_config,
    sinusoidal_pe_config,
    rotary_pe_config,
    alibi_config,
    lm_head_config,
    residual_config,
    mqa_config,
    gqa_config,
    cross_attention_config,
    layer_norm_config,
    rms_norm_config,
    swiglu_config,
    learned_pe_config,
    relative_pe_config,
    moe_head_config,
)

from .components.embedding import Embedding

from .components.pos import SinusoidalPE, RotaryPE, Alibi, LearnedPE, RelativePE

from .components.attention import SelfAttention, MultiQueryAttention, GroupedQueryAttention, CrossAttention

from .components.ffn import FeedForward

from .components.heads import LMHead, MoEHead

from .components.norm import LayerNorm, RMSNorm

from .components.activation import SwiGLU

from .components.common.residual import Residual

__all__ = [
    "Model",
    "Component",
    "Config",
    "tiny_config",
    "small_config",
    "medium_config",
    "large_config",
    "xl_config",
    "embedding_config",
    "attention_config",
    "ffn_config",
    "sinusoidal_pe_config",
    "rotary_pe_config",
    "alibi_config",
    "lm_head_config",
    "residual_config",
    "mqa_config",
    "gqa_config",
    "cross_attention_config",
    "layer_norm_config",
    "rms_norm_config",
    "swiglu_config",
    "learned_pe_config",
    "relative_pe_config",
    "moe_head_config",
    "Embedding",
    "SinusoidalPE",
    "RotaryPE",
    "Alibi",
    "LearnedPE",
    "RelativePE",
    "SelfAttention",
    "MultiQueryAttention",
    "GroupedQueryAttention",
    "CrossAttention",
    "FeedForward",
    "LMHead",
    "MoEHead",
    "LayerNorm",
    "RMSNorm",
    "SwiGLU",
    "Residual",
]

