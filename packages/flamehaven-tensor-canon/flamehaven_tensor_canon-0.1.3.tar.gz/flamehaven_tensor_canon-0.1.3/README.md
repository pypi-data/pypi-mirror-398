# Flamehaven Tensor Canon

> "Data is not just numbers; it is a structural covenant."

Flamehaven Tensor Canon is a small library for:

- Structural validation (shapes and optional dtypes)
- Distribution drift detection (MMD-based)

PyTorch is required. NumPy support is optional.

## Installation

```bash
pip install flamehaven-tensor-canon
```

Enable NumPy support:

```bash
pip install flamehaven-tensor-canon[numpy]
```

## Quick start (validation)

```python
import torch
from tensor_canon import validate

spec = "batch channels 224 224"
data = torch.randn(32, 3, 224, 224)

validate(data, spec, key="input_layer")
```

## Drift detection

```python
import torch
from tensor_canon.validator import engine

torch.manual_seed(42)
golden = torch.randn(100, 5)
engine.check_drift("embeddings", golden, register_golden=True)

current = golden + torch.randn_like(golden) * 0.01
drift = engine.check_drift("embeddings", current)
print("drift:", drift)
```

## Development

```bash
pip install -e .[dev,numpy]
ruff check .
pytest -q
```

## Docker

```bash
docker build -t tensor-canon .
docker run --rm tensor-canon
```

## Release notes and security

- See `CHANGELOG.md` for release notes.
- See `SECURITY.md` for vulnerability reporting.

## License

MIT. See `LICENSE`.
