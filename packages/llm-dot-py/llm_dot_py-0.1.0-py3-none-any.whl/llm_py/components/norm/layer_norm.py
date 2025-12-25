"""
LayerNorm component - standalone normalization layer.
"""

import torch.nn as nn
from ...component import Component


class LayerNorm(Component):
	"""Standalone LayerNorm component.
	
	Args:
		eps: Epsilon for numerical stability
	"""
	def __init__(self, eps: float = 1e-5):
		super().__init__(name="LayerNorm")
		self.eps = eps
		self.norm = None

	def build(self, cfg):
		super().build(cfg)
		self.norm = nn.LayerNorm(cfg.dim, eps=self.eps)

	def forward(self, x):
		"""Apply layer normalization.
		
		Args:
			x: Input tensor of shape (batch, seq_len, dim)
		
		Returns:
			Normalized tensor
		"""
		return self.norm(x)

