import torch
import torch.nn as nn
import torch.nn.functional as F
from ...component import Component


class FeedForward(Component):
	"""Feedforward network with optional SwiGLU activation.
	
	Args:
		dropout: Dropout probability
		use_swiglu: If True, use SwiGLU activation instead of GELU
	"""
	def __init__(self, dropout: float = 0.0, use_swiglu: bool = False):
		super().__init__(name="FeedForward")
		self.dropout_p = dropout
		self.use_swiglu = use_swiglu
		self.norm = None
		self.fc1 = None
		self.gate_proj = None
		self.up_proj = None
		self.fc2 = None
		self.drop = None

	def build(self, cfg):
		super().build(cfg)
		hidden = getattr(cfg, 'hidden', cfg.dim * 4)
		self.norm = nn.LayerNorm(cfg.dim)
		
		if self.use_swiglu:
			self.gate_proj = nn.Linear(cfg.dim, hidden)
			self.up_proj = nn.Linear(cfg.dim, hidden)
		else:
			self.fc1 = nn.Linear(cfg.dim, hidden)
		
		self.fc2 = nn.Linear(hidden, cfg.dim)
		self.drop = nn.Dropout(self.dropout_p)

	def forward(self, x):
		y = self.norm(x)
		
		if self.use_swiglu:
			gate = self.gate_proj(y)
			up = self.up_proj(y)
			swish = gate * torch.sigmoid(gate)
			y = swish * up
		else:
			y = self.fc1(y)
			y = F.gelu(y)
		
		y = self.drop(y)
		y = self.fc2(y)
		y = self.drop(y)
		return x + y
