"""
Mixture of Experts (MoE) Head implementation.
Top-k expert routing with load balancing.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from ...component import Component


class MoEHead(Component):
	"""Mixture of Experts output head.
	
	Routes input to top-k experts and combines their outputs.
	
	Args:
		num_experts: Number of expert networks
		top_k: Number of experts to route to (default: 2)
		expert_capacity_factor: Capacity factor for expert load balancing
		use_load_balancing: Whether to compute load balancing loss
	"""
	def __init__(
		self,
		num_experts: int = 8,
		top_k: int = 2,
		expert_capacity_factor: float = 1.25,
		use_load_balancing: bool = True,
	):
		super().__init__(name="MoEHead")
		self.num_experts = num_experts
		self.top_k = top_k
		self.expert_capacity_factor = expert_capacity_factor
		self.use_load_balancing = use_load_balancing
		
		self.router = None
		self.experts = None
		self._load_balancing_loss = None

	def build(self, cfg):
		super().build(cfg)
		self.router = nn.Linear(cfg.dim, self.num_experts)
		
		self.experts = nn.ModuleList([
			nn.Linear(cfg.dim, cfg.vocab_size, bias=False)
			for _ in range(self.num_experts)
		])

	def _compute_load_balancing_loss(self, router_logits: torch.Tensor, expert_mask: torch.Tensor):
		"""Compute load balancing loss for training.
		
		Encourages uniform expert usage.
		
		Args:
			router_logits: Router logits of shape (batch * seq_len, num_experts)
			expert_mask: Expert selection mask of shape (batch * seq_len, num_experts)
		
		Returns:
			Load balancing loss scalar
		"""
		expert_usage = expert_mask.float().mean(dim=0)  # (num_experts,)
		
		router_probs = F.softmax(router_logits, dim=-1)  # (batch * seq_len, num_experts)
		router_usage = router_probs.mean(dim=0)  
		

		load_balancing_loss = self.num_experts * torch.sum(expert_usage * router_usage)
		
		return load_balancing_loss

	def forward(self, x):
		"""Forward pass through MoE head.
		
		Args:
			x: Input tensor of shape (batch, seq_len, dim)
		
		Returns:
			Output logits of shape (batch, seq_len, vocab_size)
		"""
		batch_size, seq_len, dim = x.shape
		
		x_flat = x.view(-1, dim)  # (batch * seq_len, dim)
		
		router_logits = self.router(x_flat)  # (batch * seq_len, num_experts)
		router_probs = F.softmax(router_logits, dim=-1)
		
		top_k_probs, top_k_indices = torch.topk(router_probs, self.top_k, dim=-1)
		top_k_probs = top_k_probs / (top_k_probs.sum(dim=-1, keepdim=True) + 1e-8)
		
		expert_mask = torch.zeros(
			batch_size * seq_len,
			self.num_experts,
			device=x.device,
			dtype=torch.bool
		)
		expert_mask.scatter_(1, top_k_indices, True)
		
		expert_capacity = int((batch_size * seq_len * self.expert_capacity_factor) / self.num_experts)
		expert_capacity = max(expert_capacity, self.top_k)
		
		outputs = torch.zeros(
			batch_size * seq_len,
			self.cfg.vocab_size,
			device=x.device,
			dtype=x.dtype
		)
		
		for expert_idx in range(self.num_experts):
			expert_tokens = expert_mask[:, expert_idx]  # (batch * seq_len,)
			
			if expert_tokens.any():
				expert_inputs = x_flat[expert_tokens]  # (num_tokens, dim)
				
				if expert_inputs.size(0) > expert_capacity:
					expert_probs = router_probs[expert_tokens, expert_idx]
					_, top_indices = torch.topk(expert_probs, expert_capacity)
					expert_inputs = expert_inputs[top_indices]
					expert_tokens = torch.where(expert_tokens)[0][top_indices]
				else:
					expert_tokens = torch.where(expert_tokens)[0]
				
				expert_output = self.experts[expert_idx](expert_inputs)  # (num_tokens, vocab_size)
				
				token_weights = top_k_probs[expert_tokens, (top_k_indices[expert_tokens] == expert_idx).nonzero(as_tuple=True)[1]]
				
				outputs[expert_tokens] += expert_output * token_weights.unsqueeze(-1)
		
		outputs = outputs.view(batch_size, seq_len, self.cfg.vocab_size)
		
		if self.training and self.use_load_balancing:
			self._load_balancing_loss = self._compute_load_balancing_loss(router_logits, expert_mask)
		
		return outputs

	def get_load_balancing_loss(self):
		"""Get load balancing loss (if computed).
		
		Returns:
			Load balancing loss scalar or None
		"""
		return self._load_balancing_loss

