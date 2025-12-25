from abc import ABC, abstractmethod
from typing import Any, Tuple

class DataBackend(ABC):
    """
    The Sovereign Backend Interface.
    Defines how the engine interacts with different data types (Torch, Numpy, etc.)
    """
    @abstractmethod
    def get_shape(self, data: Any) -> Tuple[int, ...]:
        """Return the shape of the data."""
        pass

    @abstractmethod
    def get_dtype(self, data: Any) -> Any:
        """Return the data type."""
        pass

    @abstractmethod
    def to_cpu_flat(self, data: Any) -> Any: 
        """Converts data to a flattened 2D representation [Batch, Features] for processing."""
        pass

    @abstractmethod
    def compute_distance(self, x: Any, y: Any) -> float:
        """Backend-optimized distance calculation (e.g., Euclidean)."""
        pass

    @abstractmethod
    def harmonize(self, data: Any, target_spec: dict) -> Tuple[Any, float]:
        """Performs domain-specific adaptation (Reshaping, Normalization)."""
        pass