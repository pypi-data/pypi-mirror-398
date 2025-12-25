"""
Cross-Attention implementation.
Takes query from one sequence, key/value from another.
For encoder-decoder architectures.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from ...component import Component


class CrossAttention(Component):
	"""Cross-Attention: query from x, key/value from context.
	
	Args:
		bias: Whether to use bias in linear layers
		dropout: Attention dropout probability
	"""
	def __init__(self, bias: bool = False, dropout: float = 0.0):
		super().__init__(name="CrossAttention")
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
		self.k_proj = nn.Linear(cfg.dim, cfg.dim, bias=self.bias)
		self.v_proj = nn.Linear(cfg.dim, cfg.dim, bias=self.bias)
		self.proj = nn.Linear(cfg.dim, cfg.dim, bias=self.bias)
		self.attn_drop = nn.Dropout(self.dropout_p)
		self.proj_drop = nn.Dropout(self.dropout_p)

	def forward(self, x, context: torch.Tensor = None, mask: torch.Tensor = None):
		"""Forward pass.
		
		Args:
			x: Query tensor of shape (batch, seq_len_q, dim)
			context: Key/value tensor of shape (batch, seq_len_kv, dim)
				If None, uses x (becomes self-attention)
			mask: Optional attention mask of shape (batch, seq_len_q, seq_len_kv)
		
		Returns:
			Output tensor with residual connection
		"""
		if context is None:
			context = x

		B, T_q, C = x.shape
		_, T_kv, _ = context.shape
		
		if C != self.cfg.dim:
			raise ValueError(f"Input dimension mismatch: {C} != {self.cfg.dim}")

		q = self.q_proj(x)  # (batch, seq_len_q, dim)
		k = self.k_proj(context)  # (batch, seq_len_kv, dim)
		v = self.v_proj(context)  # (batch, seq_len_kv, dim)

		q = q.view(B, T_q, self.cfg.num_heads, self.head_dim).transpose(1, 2)  # (batch, heads, seq_len_q, head_dim)
		k = k.view(B, T_kv, self.cfg.num_heads, self.head_dim).transpose(1, 2)  # (batch, heads, seq_len_kv, head_dim)
		v = v.view(B, T_kv, self.cfg.num_heads, self.head_dim).transpose(1, 2)

		attn = (q @ k.transpose(-2, -1)) * self.scale  # (batch, heads, seq_len_q, seq_len_kv)

		# Apply mask if provided
		if mask is not None:
			if mask.dim() == 2:
				mask = mask.unsqueeze(1).unsqueeze(1)  # (batch, 1, 1, seq_len_kv)
			elif mask.dim() == 3:
				mask = mask.unsqueeze(1)  # (batch, 1, seq_len_q, seq_len_kv)
			attn = attn.masked_fill(mask == 0, float('-inf'))

		attn = F.softmax(attn, dim=-1)
		attn = self.attn_drop(attn)

		out = attn @ v  # (batch, heads, seq_len_q, head_dim)
		
		out = out.transpose(1, 2).contiguous().view(B, T_q, C)
		out = self.proj(out)
		out = self.proj_drop(out)

		return x + out

