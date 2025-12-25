import numpy as np
from typing import Any, Tuple
from .base import DataBackend

class NumpyBackend(DataBackend):
    def get_shape(self, data: np.ndarray) -> Tuple[int, ...]:
        return data.shape

    def get_dtype(self, data: np.ndarray) -> Any:
        return data.dtype

    def to_cpu_flat(self, data: np.ndarray) -> np.ndarray:
        return data.reshape(data.shape[0], -1)

    def compute_distance(self, x: np.ndarray, y: np.ndarray) -> float:
        # Standard numpy euclidean distance
        dist = np.linalg.norm(x[:, None, :] - y[None, :, :], axis=-1)**2
        return float(np.mean(dist))

    def harmonize(self, data: np.ndarray, target_spec: dict) -> Tuple[np.ndarray, float]:
        # Basic numpy harmonization
        return data, 1.0
