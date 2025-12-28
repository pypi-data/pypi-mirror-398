# floyd-net

Floyd Multi-Head Attention (F-MHA) is a drop-in variant of PyTorch's attention stack. It provides:

- Module API: `FloydMultiheadAttention` mirroring `torch.nn.MultiheadAttention`
- Functional API: `floyd_scaled_dot_product_attention` mirroring `torch.nn.functional.scaled_dot_product_attention`

Install and manage with `uv` for a modern Python workflow.

## Quick start

```bash
# Install with uv (recommended)
uv venv --python 3.10
source .venv/bin/activate
uv pip install -e .[dev]
```

```python
import torch
from floyd_net import FloydMultiheadAttention

m = FloydMultiheadAttention(embed_dim=64, num_heads=8, batch_first=True)
x = torch.randn(2, 16, 64)
out, attn = m(x, x, x)
print(out.shape)
```

### Functional API
```python
import torch
import torch.nn.functional as F
from floyd_net import floyd_scaled_dot_product_attention

q = torch.randn(2, 8, 16, 64)  # (B, H, L, D)
k = torch.randn(2, 8, 16, 64)
v = torch.randn(2, 8, 16, 64)
out = floyd_scaled_dot_product_attention(q, k, v)
print(out.shape)
```

## Paper reproductions
See `paper/` for dataset preparation, configs, and experiment templates to reproduce the results in the paper.

## License
MIT
