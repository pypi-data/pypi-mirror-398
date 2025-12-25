"""
Multi-Query Attention (MQA) implementation.
Uses a single key/value head shared across all query heads.
Reduces memory for KV cache.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from ...component import Component


class MultiQueryAttention(Component):
	"""Multi-Query Attention: single KV head shared across all query heads.
	
	Args:
		bias: Whether to use bias in linear layers
		dropout: Attention dropout probability
	"""
	def __init__(self, bias: bool = False, dropout: float = 0.0):
		super().__init__(name="MultiQueryAttention")
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

		self.head_dim = cfg.dim // cfg.num_heads
		self.scale = self.head_dim ** -0.5

		self.q_proj = nn.Linear(cfg.dim, cfg.dim, bias=self.bias)
		self.k_proj = nn.Linear(cfg.dim, self.head_dim, bias=self.bias)
		self.v_proj = nn.Linear(cfg.dim, self.head_dim, bias=self.bias)
		self.proj = nn.Linear(cfg.dim, cfg.dim, bias=self.bias)
		self.attn_drop = nn.Dropout(self.dropout_p)
		self.proj_drop = nn.Dropout(self.dropout_p)

	def forward(self, x, mask: torch.Tensor = None):
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
		k = self.k_proj(x)  # (batch, seq_len, head_dim)
		v = self.v_proj(x)  # (batch, seq_len, head_dim)

		q = q.view(B, T, self.cfg.num_heads, self.head_dim).transpose(1, 2)  # (batch, heads, seq_len, head_dim)
		k = k.unsqueeze(1)  # (batch, 1, seq_len, head_dim)
		v = v.unsqueeze(1)  # (batch, 1, seq_len, head_dim)

		attn = (q @ k.transpose(-2, -1)) * self.scale  # (batch, heads, seq_len, seq_len)

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

