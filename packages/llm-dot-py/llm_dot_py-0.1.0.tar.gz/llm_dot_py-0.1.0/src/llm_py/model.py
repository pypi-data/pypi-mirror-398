import torch.nn as nn
from .component import Component

class Model(nn.Module):
    def __init__(self, cfg, name: str = None):
        super().__init__()
        self.cfg = cfg
        self.components = nn.ModuleList()
        self._embedding_component = None
        self.name = name if name is not None else self.__class__.__name__

    def add(self, component: Component):
        component.build(self.cfg)
        self.components.append(component)
        
        if isinstance(component, type) and component.__name__ == 'Embedding':
            self._embedding_component = component
        elif hasattr(component, '__class__') and 'Embedding' in component.__class__.__name__:
            self._embedding_component = component
        
        if hasattr(component, 'set_embedding') and self._embedding_component is not None:
            if hasattr(component, 'tie_weights') and component.tie_weights:
                component.set_embedding(self._embedding_component)
        
        return self  

    def repeat(self, component_cls, times: int, **kwargs):
        if times <= 0:
            return self
        for _ in range(times):
            comp = component_cls(**kwargs)
            self.add(comp)
        return self

    def validate(self):
        if not hasattr(self.cfg, 'vocab_size') or self.cfg.vocab_size <= 0:
            raise ValueError("cfg.vocab_size must be a positive integer")
        if not hasattr(self.cfg, 'dim') or self.cfg.dim <= 0:
            raise ValueError("cfg.dim must be a positive integer")

        num_heads = getattr(self.cfg, 'num_heads', None)
        if num_heads is not None:
            if num_heads <= 0:
                raise ValueError("cfg.num_heads must be positive")
            if self.cfg.dim % num_heads != 0:
                raise ValueError("cfg.dim must be divisible by cfg.num_heads")

        names = [c.__class__.__name__ for c in self.components]
        if any(name.lower().endswith('head') for name in names[:-1]):
            raise ValueError("LM head must be the final component")
        if names:
            first = names[0].lower()
            if 'embedding' not in first:
                raise ValueError("First component should be an embedding")

    @property
    def num_parameters(self):
        return sum(p.numel() for p in self.parameters())
    
    @property
    def num_trainable_parameters(self):
        return sum(p.numel() for p in self.parameters() if p.requires_grad)
    
    @property
    def num_components(self):
        return len(self.components)
    
    @property
    def component_names(self):
        return [comp.__class__.__name__ for comp in self.components]
    
    @property
    def model_size_mb(self):
        param_size = sum(p.numel() * p.element_size() for p in self.parameters())
        buffer_size = sum(b.numel() * b.element_size() for b in self.buffers())
        return (param_size + buffer_size) / (1024 * 1024)
    
    @property
    def vocab_size(self):
        return getattr(self.cfg, 'vocab_size', 0)
    
    @property
    def dim(self):
        return getattr(self.cfg, 'dim', 0)
    
    @property
    def num_heads(self):
        return getattr(self.cfg, 'num_heads', None)
    
    @property
    def max_seq_len(self):
        return getattr(self.cfg, 'max_seq_len', None)
    
    @property
    def hidden_dim(self):
        return getattr(self.cfg, 'hidden', self.dim * 4 if self.dim > 0 else 0)
    
    def __repr__(self):
        lines = [f"{self.name}("]
        lines.append(f"  vocab_size={self.vocab_size}")
        lines.append(f"  dim={self.dim}")
        if self.num_heads:
            lines.append(f"  num_heads={self.num_heads}")
        if self.max_seq_len:
            lines.append(f"  max_seq_len={self.max_seq_len}")
        lines.append(f"  num_components={self.num_components}")
        lines.append(f"  num_parameters={self.num_parameters:,}")
        lines.append(f"  model_size={self.model_size_mb:.2f} MB")
        lines.append(")")
        return "\n".join(lines)
    
    def summary(self):
        print(f"Model: {self.name}")
        print(f"  Vocabulary size: {self.vocab_size:,}")
        print(f"  Model dimension: {self.dim}")
        if self.num_heads:
            print(f"  Attention heads: {self.num_heads}")
        if self.max_seq_len:
            print(f"  Max sequence length: {self.max_seq_len}")
        print(f"  Hidden dimension: {self.hidden_dim}")
        print(f"  Number of components: {self.num_components}")
        print(f"  Total parameters: {self.num_parameters:,}")
        print(f"  Trainable parameters: {self.num_trainable_parameters:,}")
        print(f"  Model size: {self.model_size_mb:.2f} MB")
        print("\nComponent architecture:")
        for i, comp in enumerate(self.components):
            comp_params = sum(p.numel() for p in comp.parameters())
            print(f"  [{i}] {comp.__class__.__name__} ({comp_params:,} params)")

    def forward(self, x):
        for comp in self.components:
            x = comp(x)
        return x
