"""
Universal Tensor Validator (Standard Edition)
--------------------------------------------
Provides a simple interface for structural and distributional validation.
"""

from typing import Any
from .canon_prime import TensorCanonPrime, CovenantValidator
from .backends.torch_backend import TorchBackend
try:
    from .backends.numpy_backend import NumpyBackend
except ImportError:  # pragma: no cover
    NumpyBackend = None

class Validator:
    def __init__(self, drift_threshold: float = 0.05):
        self.canon = TensorCanonPrime(drift_threshold=drift_threshold)
        self.backends = {"torch": TorchBackend()}
        if NumpyBackend is not None:
            self.backends["numpy"] = NumpyBackend()

    def _get_backend(self, data: Any):
        module = type(data).__module__
        if "torch" in module:
            return self.backends["torch"]
        if "numpy" in module:
            if "numpy" in self.backends:
                return self.backends["numpy"]
            raise TypeError("NumPy backend is unavailable. Install numpy to enable NumPy support.")
        raise TypeError(f"Unsupported data type: {type(data)}")

    def validate(self, data: Any, spec: str, key: str = "data") -> Any:
        """Standard structural validation."""
        backend = self._get_backend(data)
        validator = CovenantValidator(spec.split())
        self.canon.verify_structure(data, validator, backend, name=key)
        return data

    def check_drift(self, key: str, data: Any, register_golden: bool = False) -> float:
        """Standard distributional drift check."""
        backend = self._get_backend(data)
        if register_golden:
            self.canon.register_golden(key, data, backend)
        return self.canon.check_resonance(key, data, backend)

# Global Instance
engine = Validator()

def validate(data: Any, spec: str, key: str = "data") -> Any:
    return engine.validate(data, spec, key)
