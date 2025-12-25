import math
import torch
from ...component import Component


class SinusoidalPE(Component):
	"""Sinusoidal positional encoding (fixed, non-learnable).
	
	Args:
		max_seq_len: Maximum sequence length to support
		base: Base frequency for positional encoding (default: 10000)
	"""
	def __init__(self, max_seq_len: int, base: float = 10000.0):
		super().__init__(name="SinusoidalPE")
		self.max_seq_len = max_seq_len
		self.base = base

	def build(self, cfg):
		super().build(cfg)
		if 'pe' not in self._buffers:
			if 'pe' in self.__dict__:
				delattr(self, 'pe')
			pe = torch.zeros(self.max_seq_len, cfg.dim)
			position = torch.arange(0, self.max_seq_len, dtype=torch.float).unsqueeze(1)
			div_term = torch.exp(torch.arange(0, cfg.dim, 2).float() * (-math.log(self.base) / cfg.dim))
			pe[:, 0::2] = torch.sin(position * div_term)
			pe[:, 1::2] = torch.cos(position * div_term)
			self.register_buffer('pe', pe.unsqueeze(0), persistent=False)

	def forward(self, x):
		"""Add positional encoding to input.
		
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
		return x + self.pe[:, :seq_len, :]
