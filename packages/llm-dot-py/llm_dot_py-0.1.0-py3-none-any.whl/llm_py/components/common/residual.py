import torch
from ...component import Component


class Residual(Component):
	def __init__(self, block: Component, drop_path: float = 0.0):
		super().__init__(name=f"Residual({block.__class__.__name__})")
		self.block = block
		self.drop_path = drop_path
		self._built = False

	def build(self, cfg):
		if not self._built:
			self.block.build(cfg)
			self._built = True
		super().build(cfg)

	def _stochastic_depth(self, x, residual):
		if self.drop_path <= 0.0 or not self.training:
			return residual
		keep = 1.0 - self.drop_path
		mask = torch.rand(x.shape[0], 1, 1, device=x.device, dtype=x.dtype) < keep
		return residual * (mask / keep)

	def forward(self, x, **kwargs):
		res = self.block(x, **kwargs)
		res = self._stochastic_depth(x, res)
		return x + res
