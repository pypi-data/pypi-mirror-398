import pytest
import torch

from tensor_canon import validate
from tensor_canon.validator import engine


def test_validate_torch_shape_ok():
    x = torch.randn(32, 10)
    out = validate(x, "batch 10", key="x")
    assert tuple(out.shape) == (32, 10)


def test_validate_torch_rank_mismatch_raises():
    x = torch.randn(32, 10)
    with pytest.raises(ValueError, match="Rank"):
        validate(x, "batch channels 10", key="x")


def test_drift_detection_torch():
    torch.manual_seed(42)
    golden = torch.randn(200, 8)
    drift0 = engine.check_drift("feat", golden, register_golden=True)
    assert drift0 == 0.0

    current = golden + torch.randn_like(golden) * 0.01
    drift_small = engine.check_drift("feat", current, register_golden=False)
    assert drift_small < 0.2

    drifting = golden * 5.0 + 2.0
    drift_big = engine.check_drift("feat", drifting, register_golden=False)
    assert drift_big > 0.3


def test_numpy_optional_import_path():
    try:
        import numpy as np  # noqa: F401
    except ImportError:
        # NumPy is optional; base import should still work.
        return

    assert "numpy" in engine.backends
