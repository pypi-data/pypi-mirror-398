"""
Flamehaven Tensor Canon Prime - The Sovereign Integrator
------------------------------------------------------
"DICM was interpretation, Tensor-Canon is Specification."

This module integrates:
1. Covenant (Structure)
2. Resonance (Distribution)
3. Epsilon Verification (Precision)
"""

from typing import Any, Dict, Optional

from .backends.base import DataBackend
from .covenant import CovenantValidator
from .resonance import ResonanceSeismograph


class TensorCanonPrime:
    """
    Combines structural covenant validation and resonance drift detection.
    """

    def __init__(self, epsilon: float = 1e-6, drift_threshold: float = 0.05):
        self.epsilon = epsilon
        self.drift_threshold = drift_threshold
        self.seismograph = ResonanceSeismograph()
        self._golden_states: Dict[str, Dict[str, Any]] = {}

    def register_golden(self, key: str, data: Any, backend: Optional[DataBackend] = None, max_samples: int = 1000):
        if backend is None:
            module = type(data).__module__
            if "torch" in module:
                from .backends.torch_backend import TorchBackend

                backend = TorchBackend()
            elif "numpy" in module:
                try:
                    from .backends.numpy_backend import NumpyBackend
                except ImportError as e:  # pragma: no cover
                    raise TypeError("NumPy backend is unavailable. Install numpy to enable NumPy support.") from e

                backend = NumpyBackend()
            else:
                raise TypeError(f"No backend found for {type(data)}. Supported: Torch, NumPy.")

        flat = backend.to_cpu_flat(data)
        self._golden_states[key] = {"samples": flat[: min(max_samples, len(flat))]}

    def verify_structure(self, data: Any, spec: CovenantValidator, backend: DataBackend, name: str = "data") -> bool:
        spec.check(data, backend, name)
        return True

    def check_resonance(self, key: str, current: Any, backend: DataBackend) -> float:
        if key not in self._golden_states:
            return 0.0

        golden_samples = self._golden_states[key]["samples"]
        current_flat = backend.to_cpu_flat(current)

        if len(current_flat) > len(golden_samples) * 2:
            current_flat = current_flat[: len(golden_samples)]

        return self.seismograph.compute_resonance_gap(golden_samples, current_flat)
