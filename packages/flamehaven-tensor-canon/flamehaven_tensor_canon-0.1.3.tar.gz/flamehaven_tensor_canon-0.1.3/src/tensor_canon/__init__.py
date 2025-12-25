"""
Flamehaven Tensor Canon
-----------------------
A framework-agnostic validation and drift detection engine for PyTorch.
NumPy support is optional (install with flamehaven-tensor-canon[numpy]).
"Data is not just numbers; it is a structural covenant."
"""

from .covenant import Data, Float, Int, verify
from .resonance import ResonanceSeismograph
from .canon_prime import TensorCanonPrime
from .validator import validate

__all__ = ["Data", "Float", "Int", "verify", "ResonanceSeismograph", "TensorCanonPrime", "validate"]
