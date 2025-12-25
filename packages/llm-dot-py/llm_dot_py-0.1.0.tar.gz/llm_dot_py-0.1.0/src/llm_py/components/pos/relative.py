"""
Relative Positional Encoding (Shaw et al.).
Adds relative position biases to attention.
"""

import torch
import torch.nn as nn
from ...component import Component


class RelativePE(Component):
	"""Relative positional encoding (Shaw et al.).
	
	Adds relative position biases that can be added to attention scores.
	This component stores the bias matrix.
	
	Args:
		max_relative_position: Maximum relative distance to encode
	"""
	def __init__(self, max_relative_position: int = 128):
		super().__init__(name="RelativePE")
		self.max_relative_position = max_relative_position
		self.relative_attention_bias = None

	def build(self, cfg):
		super().build(cfg)

		num_buckets = 2 * self.max_relative_position + 1
		self.relative_attention_bias = nn.Embedding(
			num_buckets,
			cfg.num_heads
		)

	def _get_relative_position_bucket(self, seq_len: int, device: torch.device):
		"""Get relative position buckets for attention.
		
		Args:
			seq_len: Sequence length
			device: Device to create tensors on
		
		Returns:
			Relative position bucket indices of shape (seq_len, seq_len)
		"""
		positions = torch.arange(seq_len, device=device)
		
		relative_positions = positions.unsqueeze(0) - positions.unsqueeze(1)  # (seq_len, seq_len)
		
		relative_positions = torch.clamp(
			relative_positions,
			-self.max_relative_position,
			self.max_relative_position
		)
		
		bucket_indices = relative_positions + self.max_relative_position
		
		return bucket_indices

	def get_bias(self, seq_len: int, device: torch.device = None) -> torch.Tensor:
		"""Get relative position bias matrix for attention.
		
		Args:
			seq_len: Sequence length
			device: Device to create bias on
		
		Returns:
			Bias tensor of shape (num_heads, seq_len, seq_len)
		"""
		if device is None:
			device = next(self.relative_attention_bias.parameters()).device
		
		bucket_indices = self._get_relative_position_bucket(seq_len, device)
		
		biases = self.relative_attention_bias(bucket_indices)
		
		biases = biases.permute(2, 0, 1)
		
		return biases

	def forward(self, x):
		"""Forward pass - RelativePE doesn't modify input.
		
		The bias should be added in the attention mechanism.
		This component is mainly for storing and generating bias matrices.
		
		Args:
			x: Input tensor of shape (batch, seq_len, dim)
		
		Returns:
			x unchanged
		"""
		return x

