import torch.nn as nn
from ...component import Component


class Embedding(Component):
	def __init__(self, padding_idx: int = None):
		super().__init__(name="Embedding")
		self.padding_idx = padding_idx
		self.embed = None

	def build(self, cfg):
		super().build(cfg)
		self.embed = nn.Embedding(cfg.vocab_size, cfg.dim, padding_idx=self.padding_idx)

	def forward(self, x, **kwargs):
		return self.embed(x)
