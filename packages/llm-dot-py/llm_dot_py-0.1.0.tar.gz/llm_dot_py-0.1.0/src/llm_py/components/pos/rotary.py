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
	def __init__(self, base: float = 10000.0, max_seq_len: int = None):
		super().__init__(name="RotaryPE")
		self.base = base
		self.max_seq_len = max_seq_len

	def build(self, cfg):
		super().build(cfg)
		if 'inv_freq' not in self._buffers:
			if 'inv_freq' in self.__dict__:
				delattr(self, 'inv_freq')
			head_dim = cfg.dim
			inv_freq = 1.0 / (self.base ** (torch.arange(0, head_dim, 2).float() / head_dim))
			self.register_buffer('inv_freq', inv_freq, persistent=False)

	def _rotate_half(self, x):
		"""Rotate half the hidden dims of the input."""
		x1, x2 = x.chunk(2, dim=-1)
		return torch.cat([-x2, x1], dim=-1)

	def _apply_rotary_pos_emb(self, x, cos, sin):
		"""Apply rotary positional embedding."""
		return (x * cos) + (self._rotate_half(x) * sin)

	def forward(self, x):
		"""Apply rotary positional encoding.
		
		Args:
			x: Input tensor of shape (batch, seq_len, dim)
		
		Returns:
			x with rotary positional encoding applied
		"""
		seq_len = x.size(1)
		device = x.device
		dtype = x.dtype
		dim = x.size(-1)
		
		t = torch.arange(seq_len, device=device, dtype=dtype)
		
		freqs = torch.outer(t, self.inv_freq)
		
		cos = freqs.cos()  # (seq_len, num_freqs)
		sin = freqs.sin()  # (seq_len, num_freqs)
		
		cos = cos.unsqueeze(0).expand(x.size(0), -1, -1)  # (batch, seq_len, num_freqs)
		sin = sin.unsqueeze(0).expand(x.size(0), -1, -1)
		

		cos_full = cos.repeat_interleave(2, dim=-1)  # (batch, seq_len, num_freqs*2)
		sin_full = sin.repeat_interleave(2, dim=-1)
		
		if cos_full.size(-1) > dim:
			cos_full = cos_full[..., :dim]
			sin_full = sin_full[..., :dim]
		elif cos_full.size(-1) < dim:
			pad_size = dim - cos_full.size(-1)
			cos_full = F.pad(cos_full, (0, pad_size), value=1.0)
			sin_full = F.pad(sin_full, (0, pad_size), value=0.0)
		
		x1 = x[..., 0::2]  # (batch, seq_len, dim//2)
		x2 = x[..., 1::2]  # (batch, seq_len, dim//2)
		
		cos_pairs = cos_full[..., 0::2]  # (batch, seq_len, dim//2)
		sin_pairs = sin_full[..., 0::2]
		
		x1_rot = x1 * cos_pairs - x2 * sin_pairs
		x2_rot = x1 * sin_pairs + x2 * cos_pairs
		
		x_rot = torch.zeros_like(x)
		x_rot[..., 0::2] = x1_rot
		x_rot[..., 1::2] = x2_rot
		
		if dim % 2 == 1:
			x_rot[..., -1] = x[..., -1]
		
		return x_rot
