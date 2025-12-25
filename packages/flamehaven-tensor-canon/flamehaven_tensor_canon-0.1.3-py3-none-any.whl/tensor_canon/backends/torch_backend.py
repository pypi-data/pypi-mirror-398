import torch
from typing import Any, Tuple
from .base import DataBackend

class TorchBackend(DataBackend):
    def get_shape(self, data: torch.Tensor) -> Tuple[int, ...]:
        return tuple(data.shape)

    def get_dtype(self, data: torch.Tensor) -> Any:
        return data.dtype

    def to_cpu_flat(self, data: torch.Tensor) -> torch.Tensor:
        return data.detach().view(data.size(0), -1).cpu()

    def compute_distance(self, x: torch.Tensor, y: torch.Tensor) -> float:
        # Optimized pairwise distance using torch
        return torch.cdist(x, y, p=2).pow(2).mean().item()

    def harmonize(self, data: torch.Tensor, target_spec: dict) -> Tuple[torch.Tensor, float]:
        score = 1.0
        harmonized = data
        expected_rank = target_spec.get("rank")
        if expected_rank and data.dim() != expected_rank:
            if data.dim() == expected_rank - 1:
                harmonized = harmonized.unsqueeze(0)
                score = 0.9
        return harmonized, score
