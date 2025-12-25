"""
Flamehaven Universal Covenant - Structural Integrity Enforcement
--------------------------------------------------------------
Philosophy:
    Data is a structural promise, regardless of the framework (Torch, NumPy, etc.)
"""

from typing import Any, List

from .backends.base import DataBackend


class CovenantMeta(type):
    """
    Metaclass for defining Data structural covenants.
    Allows syntax: Data['batch 256 256']
    """

    def __getitem__(cls, args: Any) -> "CovenantValidator":
        if isinstance(args, str):
            dims = args.split()
            dtype = None
        elif isinstance(args, tuple):
            if len(args) == 2:
                dtype = args[0]
                dims = args[1].split() if isinstance(args[1], str) else args[1]
            else:
                raise ValueError("Covenant spec must be 'dims' or (dtype, 'dims')")
        else:
            raise TypeError("Invalid covenant specification.")

        return CovenantValidator(dims, dtype)


class Data(metaclass=CovenantMeta):
    """
    Base class for Universal Data specifications.
    Usage:
        def process(x: Data['b 10']):
    """


class CovenantValidator:
    """The Universal Enforcer."""

    def __init__(self, dims: List[str], dtype: Any = None):
        self.dims = dims
        self.dtype = dtype

    def check(self, data: Any, backend: DataBackend, name: str = "data") -> None:
        real_dtype = backend.get_dtype(data)
        if self.dtype is not None and real_dtype != self.dtype:
            raise TypeError(f"Covenant Dtype Violation [{name}]: Expected {self.dtype}, got {real_dtype}")

        shape = backend.get_shape(data)
        if len(shape) != len(self.dims):
            raise ValueError(
                f"Rank mismatch for '{name}':\n"
                f"  Expected: {len(self.dims)} ({self.dims})\n"
                f"  Got:      {len(shape)} {shape}\n"
                f"  [i] Hint: Did you forget to .unsqueeze(0) for batching or .squeeze() to remove unit dims?"
            )

        for i, (spec_dim, real_dim) in enumerate(zip(self.dims, shape)):
            if spec_dim.isdigit() and int(spec_dim) != real_dim:
                raise ValueError(
                    f"Dimension mismatch for '{name}' at index {i}:\n"
                    f"  Expected size: {spec_dim}\n"
                    f"  Actual size:   {real_dim}\n"
                    f"  Full shape:    {shape}\n"
                    f"  [i] Hint: Verify your data pipeline's output shape."
                )


def verify(obj: Any, covenant: "CovenantValidator", name: str = "obj") -> None:
    """Manual trigger for verification - requires backend."""
    raise NotImplementedError(
        "verify() requires a backend parameter. " "Use: validate(data, spec) for auto-detection."
    )


try:
    import torch

    Float = Data[torch.float32, "..."]
    Int = Data[torch.int64, "..."]
except ImportError:  # pragma: no cover
    Float = None
    Int = None
