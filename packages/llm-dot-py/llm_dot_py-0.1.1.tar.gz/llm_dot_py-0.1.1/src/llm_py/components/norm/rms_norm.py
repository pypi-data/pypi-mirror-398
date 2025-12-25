"""
RMSNorm (Root Mean Square Layer Normalization) component.
No centering, only scaling.
"""

import torch
import torch.nn as nn
from ...component import Component


class RMSNorm(Component):
	"""RMSNorm: Root Mean Square Layer Normalization.
	
	Normalizes by RMS instead of mean and variance.
	No centering, only scaling.
	
	Args:
		eps: Epsilon for numerical stability
	"""
	def __init__(self, eps: float = 1e-6):
		super().__init__(name="RMSNorm")
		self.eps = eps
		self.weight = None

	def build(self, cfg):
		super().build(cfg)
		self.weight = nn.Parameter(torch.ones(cfg.dim))

	def forward(self, x):
		"""Apply RMS normalization.
		
		Args:
			x: Input tensor of shape (batch, seq_len, dim)
		
		Returns:
			Normalized tensor
		"""
		rms = torch.sqrt(torch.mean(x ** 2, dim=-1, keepdim=True) + self.eps)
		return x / rms * self.weight

