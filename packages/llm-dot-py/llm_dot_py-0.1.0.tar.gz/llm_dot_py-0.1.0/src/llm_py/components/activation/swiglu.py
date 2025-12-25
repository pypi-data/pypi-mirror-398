"""
SwiGLU (Swish-Gated Linear Unit) activation component.
"""

import torch
import torch.nn as nn
from ...component import Component


class SwiGLU(Component):
	"""SwiGLU activation: Swish(xW + b) * (xV + c)
	
	Args:
		hidden: Hidden dimension (defaults to cfg.hidden or 4 * cfg.dim)
	"""
	def __init__(self, hidden: int = None):
		super().__init__(name="SwiGLU")
		self.hidden = hidden
		self.gate_proj = None
		self.up_proj = None

	def build(self, cfg):
		super().build(cfg)
		hidden = self.hidden if self.hidden is not None else getattr(cfg, 'hidden', cfg.dim * 4)
		self.gate_proj = nn.Linear(cfg.dim, hidden)
		self.up_proj = nn.Linear(cfg.dim, hidden)

	def forward(self, x):
		"""Apply SwiGLU activation.
		
		Args:
			x: Input tensor of shape (batch, seq_len, dim)
		
		Returns:
			Activated tensor of shape (batch, seq_len, hidden)
		"""
		gate = self.gate_proj(x)
		up = self.up_proj(x)
		swish = gate * torch.sigmoid(gate)
		return swish * up

