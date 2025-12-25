"""
Flamehaven Resonance Seismograph - Drift Detection Engine
-------------------------------------------------------
Implements the "Resonance over Variance" philosophy.
Detects distributional drift using Maximum Mean Discrepancy (MMD) kernels.

Philosophy:
    Drift is the loss of resonance between the expected (Golden) and the actual (Current).
    We measure this vibration using the Gaussian Kernel.
"""

from typing import Any, Optional

import torch

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None


class ResonanceSeismograph:
    """
    Detects data drift using MMD (Maximum Mean Discrepancy).
    Acts as a vibration sensor for tensor distributions.
    """

    def __init__(self, kernel_scales: Optional[list] = None):
        self.kernel_scales = kernel_scales if kernel_scales else [0.1, 0.5, 1.0, 2.0, 5.0, 10.0]

    def _gaussian_kernel(self, x: torch.Tensor, y: torch.Tensor, max_samples: int = 1000) -> torch.Tensor:
        if x.size(0) > max_samples:
            x = x[torch.randperm(x.size(0))[:max_samples]]
        if y.size(0) > max_samples:
            y = y[torch.randperm(y.size(0))[:max_samples]]

        xx = torch.cdist(x, x, p=2).pow(2)
        yy = torch.cdist(y, y, p=2).pow(2)
        xy = torch.cdist(x, y, p=2).pow(2)

        total_k_xx = torch.zeros_like(xx)
        total_k_yy = torch.zeros_like(yy)
        total_k_xy = torch.zeros_like(xy)

        for scale in self.kernel_scales:
            gamma = 1.0 / (2 * scale**2)
            total_k_xx += torch.exp(-gamma * xx)
            total_k_yy += torch.exp(-gamma * yy)
            total_k_xy += torch.exp(-gamma * xy)

        return total_k_xx, total_k_yy, total_k_xy

    def _to_torch_2d(self, data: Any) -> torch.Tensor:
        if isinstance(data, torch.Tensor):
            t = data
        elif np is not None and isinstance(data, np.ndarray):
            t = torch.from_numpy(data)
        else:
            raise TypeError(f"Unsupported data type for resonance: {type(data)}")

        if not torch.is_floating_point(t):
            t = t.float()

        if t.dim() == 1:
            t = t.unsqueeze(0)

        if t.dim() > 2:
            t = t.view(t.size(0), -1)

        return t

    def compute_resonance_gap(self, x: Any, y: Any) -> float:
        x = self._to_torch_2d(x)
        y = self._to_torch_2d(y)

        k_xx, k_yy, k_xy = self._gaussian_kernel(x, y)

        m = k_xx.size(0)
        n = k_yy.size(0)

        if m > 1:
            e_xx = (k_xx.sum() - torch.diagonal(k_xx, 0).sum()) / (m * (m - 1))
        else:
            e_xx = torch.tensor(0.0, device=k_xx.device)

        if n > 1:
            e_yy = (k_yy.sum() - torch.diagonal(k_yy, 0).sum()) / (n * (n - 1))
        else:
            e_yy = torch.tensor(0.0, device=k_yy.device)

        e_xy = k_xy.mean()

        mmd_sq = e_xx + e_yy - (2 * e_xy)
        return max(0.0, float(mmd_sq.item()))

    def is_stable(self, x: Any, y: Any, threshold: float = 0.05) -> bool:
        return self.compute_resonance_gap(x, y) < threshold
