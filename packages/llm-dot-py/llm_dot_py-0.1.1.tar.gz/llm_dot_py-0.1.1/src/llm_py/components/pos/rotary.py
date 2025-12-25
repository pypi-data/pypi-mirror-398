import torch
import torch.nn.functional as F
from ...component import Component


class RotaryPE(Component):
	"""Rotary Positional Encoding (RoPE).
	
	Applies rotary embeddings to input. This is typically applied within
	attention mechanisms, but can also be added directly to embeddings.
	
	Args:
		base: Base frequency for rotary encoding (default: 10000)
		max_seq_len: Maximum sequence length (for pre-computation, optional)
	"""
def rotate_half(x):
	"""Rotate half the hidden dims of the input."""
	x = x.view(x.shape[:-1] + (-1, 2))
	x1, x2 = x.unbind(dim=-1)
	return torch.stack((-x2, x1), dim=-1).flatten(-2)

def apply_rotary_pos_emb(x, cos, sin):
	"""Apply rotary positional embedding.
	x: (batch, heads, seq_len, head_dim)
	cos, sin: (batch, 1, seq_len, head_dim) or broadcastable
	"""
	# Ensure cos/sin are broadcastable to x
	# x is usually (B, H, T, D). cos/sin are (1, 1, T, D) or (B, 1, T, D).
	return (x * cos) + (rotate_half(x) * sin)

class RotaryPE(Component):
	"""Rotary Positional Encoding (RoPE).
	
	Calculates rotary embeddings and passes them for use in attention.
	Note: Does NOT apply embeddings to input 'x' directly.
	
	Args:
		base: Base frequency for rotary encoding (default: 10000)
		max_seq_len: Maximum sequence length (for pre-computation, optional)
	"""
	def __init__(self, base: float = 10000.0, max_seq_len: int = None):
		super().__init__(name="RotaryPE")
		self.base = base
		self.max_seq_len = max_seq_len

	def build(self, cfg):
		super().build(cfg)
		if 'inv_freq' not in self._buffers:
			if 'inv_freq' in self.__dict__:
				delattr(self, 'inv_freq')
			head_dim = cfg.dim // cfg.num_heads
			inv_freq = 1.0 / (self.base ** (torch.arange(0, head_dim, 2).float() / head_dim))
			self.register_buffer('inv_freq', inv_freq, persistent=False)

	def forward(self, x, offset: int = 0, **kwargs):
		"""Calculate rotary positional encoding frequencies.
		
		Args:
			x: Input tensor (batched). Used only for shape inference (seq_len, device).
			offset: Starting position for the sequence (default: 0)
		
		Returns:
			Tuple (x, (cos, sin)) where x is unchanged.
		"""
		seq_len = x.size(1)
		device = x.device
		dtype = x.dtype
		
		t = torch.arange(seq_len, device=device, dtype=dtype) + offset
		
		freqs = torch.outer(t, self.inv_freq)
		
		cos = freqs.cos()  # (seq_len, head_dim/2)
		sin = freqs.sin()  # (seq_len, head_dim/2)
		
		# Reshape for Attention: (batch, heads, seq_len, head_dim)
		# But here we just compute (seq_len, head_dim).
		# Attention will broadcast. 
		# We'll return (1, 1, seq_len, head_dim) to make it easy?
		# Standard is usually (seq_len, head_dim).
		# Let's match typical Attention broadcasting: (B, H, T, D)
		
		cos = cos.unsqueeze(0).unsqueeze(0) # (1, 1, seq_len, head_dim/2)
		sin = sin.unsqueeze(0).unsqueeze(0)
		
		cos = cos.repeat_interleave(2, dim=-1) # (1, 1, seq_len, head_dim)
		sin = sin.repeat_interleave(2, dim=-1)

		return x, (cos, sin)
