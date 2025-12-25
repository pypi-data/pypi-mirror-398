"""
Preconfigured model configurations and component configs.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class Config:
	"""Base model configuration.
	
	Args:
		vocab_size: Vocabulary size
		dim: Model dimension (embedding size)
		hidden: FFN hidden dimension (defaults to 4 * dim)
		num_heads: Number of attention heads
		max_seq_len: Maximum sequence length
		dropout: Dropout probability
		drop_path: Stochastic depth probability
		tie_weights: Whether to tie LM head weights to embedding
	"""
	vocab_size: int = 0
	dim: int = 0
	hidden: Optional[int] = None
	num_heads: Optional[int] = None
	max_seq_len: Optional[int] = None
	dropout: float = 0.0
	drop_path: float = 0.0
	tie_weights: bool = True
	
	component_configs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
	
	def __post_init__(self):
		"""Derive defaults after initialization."""
		if self.hidden is None and self.dim > 0:
			self.hidden = 4 * self.dim


def tiny_config(vocab_size: int = 1000, max_seq_len: int = 512) -> Config:
	"""Tiny model configuration (~1M parameters)."""
	return Config(
		vocab_size=vocab_size,
		dim=128,
		hidden=512,
		num_heads=4,
		max_seq_len=max_seq_len,
		dropout=0.1,
		drop_path=0.0,
		tie_weights=True,
	)


def small_config(vocab_size: int = 10000, max_seq_len: int = 1024) -> Config:
	"""Small model configuration (~10M parameters)."""
	return Config(
		vocab_size=vocab_size,
		dim=256,
		hidden=1024,
		num_heads=8,
		max_seq_len=max_seq_len,
		dropout=0.1,
		drop_path=0.0,
		tie_weights=True,
	)


def medium_config(vocab_size: int = 50000, max_seq_len: int = 2048) -> Config:
	"""Medium model configuration (~100M parameters)."""
	return Config(
		vocab_size=vocab_size,
		dim=512,
		hidden=2048,
		num_heads=8,
		max_seq_len=max_seq_len,
		dropout=0.1,
		drop_path=0.1,
		tie_weights=True,
	)


def large_config(vocab_size: int = 50000, max_seq_len: int = 2048) -> Config:
	"""Large model configuration (~500M parameters)."""
	return Config(
		vocab_size=vocab_size,
		dim=1024,
		hidden=4096,
		num_heads=16,
		max_seq_len=max_seq_len,
		dropout=0.1,
		drop_path=0.1,
		tie_weights=True,
	)


def xl_config(vocab_size: int = 50000, max_seq_len: int = 4096) -> Config:
	"""XL model configuration (~1B parameters)."""
	return Config(
		vocab_size=vocab_size,
		dim=2048,
		hidden=8192,
		num_heads=32,
		max_seq_len=max_seq_len,
		dropout=0.1,
		drop_path=0.2,
		tie_weights=True,
	)



def embedding_config(padding_idx: Optional[int] = None) -> Dict[str, Any]:
	"""Configuration for Embedding component."""
	return {
		"padding_idx": padding_idx,
	}


def attention_config(bias: bool = False, dropout: float = 0.0) -> Dict[str, Any]:
	"""Configuration for SelfAttention component."""
	return {
		"bias": bias,
		"dropout": dropout,
	}


def ffn_config(dropout: float = 0.0, use_swiglu: bool = False) -> Dict[str, Any]:
	"""Configuration for FeedForward component."""
	return {
		"dropout": dropout,
		"use_swiglu": use_swiglu,
	}


def sinusoidal_pe_config(max_seq_len: int, base: float = 10000.0) -> Dict[str, Any]:
	"""Configuration for SinusoidalPE component."""
	return {
		"max_seq_len": max_seq_len,
		"base": base,
	}


def rotary_pe_config(base: float = 10000.0, max_seq_len: Optional[int] = None) -> Dict[str, Any]:
	"""Configuration for RotaryPE component."""
	return {
		"base": base,
		"max_seq_len": max_seq_len,
	}


def alibi_config(num_heads: Optional[int] = None, slope_base: Optional[float] = None) -> Dict[str, Any]:
	"""Configuration for Alibi component."""
	return {
		"num_heads": num_heads,
		"slope_base": slope_base,
	}


def lm_head_config(tie_weights: bool = True, bias: bool = False) -> Dict[str, Any]:
	"""Configuration for LMHead component."""
	return {
		"tie_weights": tie_weights,
		"bias": bias,
	}


def residual_config(drop_path: float = 0.0) -> Dict[str, Any]:
	"""Configuration for Residual wrapper component."""
	return {
		"drop_path": drop_path,
	}


def mqa_config(bias: bool = False, dropout: float = 0.0) -> Dict[str, Any]:
	"""Configuration for MultiQueryAttention component."""
	return {
		"bias": bias,
		"dropout": dropout,
	}


def gqa_config(num_kv_heads: int = None, bias: bool = False, dropout: float = 0.0) -> Dict[str, Any]:
	"""Configuration for GroupedQueryAttention component."""
	return {
		"num_kv_heads": num_kv_heads,
		"bias": bias,
		"dropout": dropout,
	}


def cross_attention_config(bias: bool = False, dropout: float = 0.0) -> Dict[str, Any]:
	"""Configuration for CrossAttention component."""
	return {
		"bias": bias,
		"dropout": dropout,
	}


def layer_norm_config(eps: float = 1e-5) -> Dict[str, Any]:
	"""Configuration for LayerNorm component."""
	return {
		"eps": eps,
	}


def rms_norm_config(eps: float = 1e-6) -> Dict[str, Any]:
	"""Configuration for RMSNorm component."""
	return {
		"eps": eps,
	}


def swiglu_config(hidden: int = None) -> Dict[str, Any]:
	"""Configuration for SwiGLU component."""
	return {
		"hidden": hidden,
	}


def learned_pe_config(max_seq_len: int) -> Dict[str, Any]:
	"""Configuration for LearnedPE component."""
	return {
		"max_seq_len": max_seq_len,
	}


def relative_pe_config(max_relative_position: int = 128) -> Dict[str, Any]:
	"""Configuration for RelativePE component."""
	return {
		"max_relative_position": max_relative_position,
	}


def moe_head_config(
	num_experts: int = 8,
	top_k: int = 2,
	expert_capacity_factor: float = 1.25,
	use_load_balancing: bool = True,
) -> Dict[str, Any]:
	"""Configuration for MoEHead component."""
	return {
		"num_experts": num_experts,
		"top_k": top_k,
		"expert_capacity_factor": expert_capacity_factor,
		"use_load_balancing": use_load_balancing,
	}


__all__ = [
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
]
