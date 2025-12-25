"""
Learned Positional Encoding.
Learnable positional embeddings (like BERT).
"""

import torch
import torch.nn as nn
from ...component import Component


class LearnedPE(Component):
	"""Learned positional encoding (learnable embeddings).
	
	Args:
		max_seq_len: Maximum sequence length
	"""
	def __init__(self, max_seq_len: int):
		super().__init__(name="LearnedPE")
		self.max_seq_len = max_seq_len
		self.pe = None

	def build(self, cfg):
		super().build(cfg)
		self.pe = nn.Embedding(self.max_seq_len, cfg.dim)

	def forward(self, x):
		"""Add learned positional encoding to input.
		
		Args:
			x: Input tensor of shape (batch, seq_len, dim)
		
		Returns:
			x + positional_encoding
		"""
		seq_len = x.size(1)
		if seq_len > self.max_seq_len:
			raise ValueError(
				f"Sequence length {seq_len} exceeds max_seq_len {self.max_seq_len}. "
				"Increase max_seq_len or truncate input."
			)
		
		positions = torch.arange(seq_len, device=x.device)
		pos_emb = self.pe(positions)  # (seq_len, dim)
		pos_emb = pos_emb.unsqueeze(0)  # (1, seq_len, dim)
		
		return x + pos_emb

