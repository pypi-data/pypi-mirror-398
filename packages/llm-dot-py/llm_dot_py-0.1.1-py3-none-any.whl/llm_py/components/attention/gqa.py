"""
Grouped Query Attention (GQA) implementation.
Configurable number of KV heads between MHA and MQA.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from ...component import Component
from ..pos.rotary import apply_rotary_pos_emb

class GroupedQueryAttention(Component):
	# ... (init unchanged) ...
	"""Grouped Query Attention: configurable number of KV heads.
	
	Args:
		num_kv_heads: Number of key/value heads (must divide num_heads)
		bias: Whether to use bias in linear layers
		dropout: Attention dropout probability
	"""
	def __init__(self, num_kv_heads: int = None, bias: bool = False, dropout: float = 0.0):
		super().__init__(name="GroupedQueryAttention")
		self.num_kv_heads = num_kv_heads
		self.bias = bias
		self.dropout_p = dropout
		self.q_proj = None
		self.k_proj = None
		self.v_proj = None
		self.proj = None
		self.attn_drop = None
		self.proj_drop = None

	def build(self, cfg):
		super().build(cfg)
		if cfg.dim % cfg.num_heads != 0:
			raise ValueError("cfg.dim must be divisible by cfg.num_heads")

		if self.num_kv_heads is None:
			self.num_kv_heads = cfg.num_heads

		if cfg.num_heads % self.num_kv_heads != 0:
			raise ValueError(f"num_heads ({cfg.num_heads}) must be divisible by num_kv_heads ({self.num_kv_heads})")

		self.head_dim = cfg.dim // cfg.num_heads
		self.scale = self.head_dim ** -0.5
		self.num_groups = cfg.num_heads // self.num_kv_heads

		self.q_proj = nn.Linear(cfg.dim, cfg.dim, bias=self.bias)
		kv_dim = self.num_kv_heads * self.head_dim
		self.k_proj = nn.Linear(cfg.dim, kv_dim, bias=self.bias)
		self.v_proj = nn.Linear(cfg.dim, kv_dim, bias=self.bias)
		self.proj = nn.Linear(cfg.dim, cfg.dim, bias=self.bias)
		self.attn_drop = nn.Dropout(self.dropout_p)
		self.proj_drop = nn.Dropout(self.dropout_p)

	def forward(self, x, mask: torch.Tensor = None, rotary_pos_emb = None, attention_bias = None, **kwargs):
		"""Forward pass.
		
		Args:
			x: Input tensor of shape (batch, seq_len, dim)
			mask: Optional attention mask
		
		Returns:
			Output tensor with residual connection
		"""
		B, T, C = x.shape
		if C != self.cfg.dim:
			raise ValueError(f"Input dimension mismatch: {C} != {self.cfg.dim}")

		q = self.q_proj(x)  # (batch, seq_len, dim)
		k = self.k_proj(x)  # (batch, seq_len, num_kv_heads * head_dim)
		v = self.v_proj(x)  # (batch, seq_len, num_kv_heads * head_dim)

		q = q.view(B, T, self.cfg.num_heads, self.head_dim).transpose(1, 2)  # (batch, heads, seq_len, head_dim)
		k = k.view(B, T, self.num_kv_heads, self.head_dim).transpose(1, 2)  # (batch, kv_heads, seq_len, head_dim)
		v = v.view(B, T, self.num_kv_heads, self.head_dim).transpose(1, 2)

		# Apply RoPE
		if rotary_pos_emb is not None:
			cos, sin = rotary_pos_emb
			q = apply_rotary_pos_emb(q, cos, sin)
			k = apply_rotary_pos_emb(k, cos, sin)

		k = k.repeat_interleave(self.num_groups, dim=1)  # (batch, heads, seq_len, head_dim)
		v = v.repeat_interleave(self.num_groups, dim=1)

		attn = (q @ k.transpose(-2, -1)) * self.scale  # (batch, heads, seq_len, seq_len)
		
		if attention_bias is not None:
			attn = attn + attention_bias

		causal_mask = torch.triu(torch.ones(T, T, device=x.device, dtype=torch.bool), diagonal=1)
		attn = attn.masked_fill(causal_mask.unsqueeze(0).unsqueeze(0), float('-inf'))

		if mask is not None:
			if mask.dim() == 2:
				mask = mask.unsqueeze(1).unsqueeze(1)
			attn = attn.masked_fill(mask == 0, float('-inf'))

		attn = F.softmax(attn, dim=-1)
		attn = self.attn_drop(attn)

		out = attn @ v  # (batch, heads, seq_len, head_dim)
		
		out = out.transpose(1, 2).contiguous().view(B, T, C)
		out = self.proj(out)
		out = self.proj_drop(out)

		return x + out

