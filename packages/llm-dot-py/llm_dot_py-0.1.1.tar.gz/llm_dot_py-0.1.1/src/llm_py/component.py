import torch.nn as nn



class Component(nn.Module):
    def __init__(self, name = None):
        """"Base class for all model components."""
        super().__init__()
        self.name = name if name is not None else self.__class__.__name__
        self.cfg = None
    
    def build(self, cfg):
        """Optional: called once when added to a model"""
        self.cfg = cfg

    def forward(self, x, **kwargs):
        raise NotImplementedError("Subclass must implement forward method")
    
