# llm-py

**Build LLMs block by block.**

`llm-py` is a modular, educational, and practical library for building Large Language Models (LLMs) from scratch. It provides implementations of modern components like Rotary Positional Embeddings (RoPE), SwiGLU, RMSNorm, and various attention mechanisms.

## Features

- **Modular Design**: Plug-and-play components (`Component` based architecture).
- **Modern Components**:
  - **Positional Embeddings**: Rotary (RoPE), Alibi, Sinusoidal, Learned.
  - **Attention**: Multi-Head, Multi-Query (MQA), Grouped-Query (GQA).
  - **Activations & Norms**: SwiGLU, RMSNorm, LayerNorm.
- **Configurable**: Easy-to-use configuration system for different model sizes.

## Installation

```bash
pip install llm-py
```

*Note: You may need to install PyTorch separately depending on your CUDA version.*

## Usage

Here is a simple example of how to build a model:

```python
from llm_py import (
    Model, small_config,
    Embedding, RotaryPE, SelfAttention, FeedForward, LMHead
)

# Initialize configuration
cfg = small_config(vocab_size=10000)

# Build the model block by block
model = (
    Model(cfg)
        .add(Embedding())
        .add(RotaryPE())
        .repeat(SelfAttention, 4, dropout=0.1)
        .add(FeedForward())
        .add(LMHead(tie_weights=True))
)

# Validate and print summary
model.validate()
model.summary()

# Run a forward pass
import torch
x = torch.randint(0, cfg.vocab_size, (2, 32)) 
output = model(x)
print(f"Output shape: {output.shape}")
```

## Architecture

The library revolves around the `Model` class, which acts as a container for sequential `Component`s. 

- **`Component`**: Base class for all layers. Implementation of specific logic (e.g., `RotaryPE`) resides here.
- **`Config`**: Dataclass holding hyperparameters (dimension, heads, layers, etc.).

## License

MIT
