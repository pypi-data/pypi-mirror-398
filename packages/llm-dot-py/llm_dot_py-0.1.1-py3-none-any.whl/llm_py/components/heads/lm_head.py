import torch.nn as nn
from ...component import Component


class LMHead(Component):
	"""Language modeling head with optional weight tying.
	
	Args:
		tie_weights: If True, ties output projection weights to embedding weights
			(requires embedding component to be passed via set_embedding)
		bias: Whether to use bias in output projection
	"""
	def __init__(self, tie_weights: bool = True, bias: bool = False):
		super().__init__(name="LMHead")
		self.tie_weights = tie_weights
		self.bias = bias
		self.proj = None
		self.embedding = None
		self._tied = False

	def set_embedding(self, embedding_component):
		"""Set embedding component for weight tying.
		
		Args:
			embedding_component: Embedding component instance
		"""
		self.embedding = embedding_component

	def build(self, cfg):
		super().build(cfg)
		self.proj = nn.Linear(cfg.dim, cfg.vocab_size, bias=self.bias)
		
		if self.tie_weights and self.embedding is not None:
			if hasattr(self.embedding, 'embed') and hasattr(self.embedding.embed, 'weight'):
				self.proj.weight = self.embedding.embed.weight
				self._tied = True
			else:
				raise ValueError("Embedding component must have 'embed.weight' for weight tying")

	def forward(self, x, **kwargs):
		"""Forward pass.
		
		Args:
			x: Input tensor of shape (batch, seq_len, dim)
		
		Returns:
			Logits of shape (batch, seq_len, vocab_size)
		"""
		return self.proj(x)
