import torch
import torch.nn as nn
import torch.nn.functional as F
from ...component import Component


class SelfAttention(Component):
    def __init__(self, bias: bool = False, dropout: float = 0.0):
        super().__init__(name="SelfAttention")
        self.bias = bias
        self.dropout_p = dropout
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

    def forward(self, x, mask: torch.Tensor = None):
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

        attn = (q @ k.transpose(-2, -1)) * self.scale

        if mask is not None:
            attn = attn.masked_fill(mask == 0, float('-inf'))

        attn = F.softmax(attn, dim=-1)
        attn = self.attn_drop(attn)

        out = attn @ v  
        out = out.transpose(1, 2).contiguous().view(B, T, C)
        out = self.proj(out)
        out = self.proj_drop(out)

        return x + out
