import torch
import torch.nn as nn
import torch.nn.functional as F
from ...component import Component
from ..pos.rotary import apply_rotary_pos_emb

class SelfAttention(Component):
    def __init__(self, bias: bool = False, dropout: float = 0.0, is_causal: bool = True):
        super().__init__(name="SelfAttention")
        # ... existing init ...
        self.bias = bias
        self.dropout_p = dropout
        self.is_causal = is_causal
        self.norm = None
        self.qkv = None
        self.proj = None
        self.attn_drop = None
        self.proj_drop = None

    def build(self, cfg):
        super().build(cfg)
        if cfg.dim % cfg.num_heads != 0:
            raise ValueError("cfg.dim must be divisible by cfg.num_heads")

        self.head_dim = cfg.dim // cfg.num_heads
        self.scale = self.head_dim ** -0.5

        self.norm = nn.LayerNorm(cfg.dim)
        self.qkv = nn.Linear(cfg.dim, cfg.dim * 3, bias=self.bias)
        self.proj = nn.Linear(cfg.dim, cfg.dim, bias=self.bias)
        self.attn_drop = nn.Dropout(self.dropout_p)
        self.proj_drop = nn.Dropout(self.dropout_p)

    def forward(self, x, mask: torch.Tensor = None, past_key_value = None, rotary_pos_emb = None, attention_bias = None, **kwargs):
        if not hasattr(self, "cfg"):
            raise ValueError(f"cfg not set for {self.name}")

        B, T, C = x.shape
        if C != self.cfg.dim:
            raise ValueError(f"Input dimension mismatch: {C} != {self.cfg.dim}")

        qkv = self.qkv(x)
        q, k, v = qkv.chunk(3, dim=-1)

        q = q.view(B, T, self.cfg.num_heads, self.head_dim).transpose(1, 2)
        k = k.view(B, T, self.cfg.num_heads, self.head_dim).transpose(1, 2)
        v = v.view(B, T, self.cfg.num_heads, self.head_dim).transpose(1, 2)

        # Apply Rotational Position Embeddings (RoPE)
        if rotary_pos_emb is not None:
             cos, sin = rotary_pos_emb
             # q, k shape: (B, H, T, D)
             # cos, sin shape: (1, 1, T, D) or broadcastable
             q = apply_rotary_pos_emb(q, cos, sin)
             k = apply_rotary_pos_emb(k, cos, sin)

        if past_key_value is not None:
            past_k, past_v = past_key_value
            k = torch.cat([past_k, k], dim=2)
            v = torch.cat([past_v, v], dim=2)
        
        current_key_value = (k, v)

        attn = (q @ k.transpose(-2, -1)) * self.scale
        
        # Apply ALiBi or other attention bias
        if attention_bias is not None:
             attn = attn + attention_bias

        if mask is not None:
            attn = attn.masked_fill(mask == 0, float('-inf'))
        elif self.is_causal and T > 1:
            # Apply causal mask: mask positions where q_i attends to k_j with j > i
            # q shape (B, H, T, D). k shape (B, H, T_k, D).
            # attn shape (B, H, T, T_k).
            # We want diag to include self.
            # j > i + (T_k - T)?
            # Case Naive: T_k = T. j > i. 
            T_k = k.size(2)
            causal_mask = torch.triu(torch.ones(T, T_k, device=x.device), diagonal=1 + T_k - T).bool()
            attn = attn.masked_fill(causal_mask, float('-inf'))

        attn = F.softmax(attn, dim=-1)
        attn = self.attn_drop(attn)

        out = attn @ v  
        out = out.transpose(1, 2).contiguous().view(B, T, C)
        out = self.proj(out)
        out = self.proj_drop(out)

        return x + out, current_key_value

