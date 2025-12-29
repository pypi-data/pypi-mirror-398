"""Helpers for parameterised truth functions."""

from __future__ import annotations

from typing import Callable, Dict, Optional, Sequence, Tuple

import torch

from .core import Constant, TruthFunction


class ConstantTruthFunction:
    """Returns a fixed truth value regardless of the arguments."""

    def __init__(self, value: float) -> None:
        if not 0.0 <= value <= 1.0:
            raise ValueError("Truth value must lie in [0, 1]")
        self.value = float(value)

    def __call__(self, arguments: Tuple[Constant, ...]) -> float:  # pragma: no cover - no logic
        return self.value


class LinearFeatureTruthFunction(torch.nn.Module):
    """Differentiable truth function with learnable linear/sigmoid parameters."""

    def __init__(
        self,
        feature_map: Callable[[Tuple[Constant, ...]], Sequence[float]],
        feature_dim: Optional[int] = None,
        weights: Optional[torch.Tensor] = None,
        bias: Optional[torch.Tensor] = None,
    ) -> None:
        super().__init__()
        self.feature_map = feature_map

        if weights is not None:
            if weights.ndim != 1:
                raise ValueError("weights must be a 1-D tensor")
            self.weights = torch.nn.Parameter(weights.clone().detach().requires_grad_(True))
            feature_dim = weights.shape[0]
        else:
            if feature_dim is None:
                raise ValueError("feature_dim is required when weights are not provided")
            self.weights = torch.nn.Parameter(torch.zeros(feature_dim))

        if bias is not None:
            if bias.shape not in {(1,), ()}:
                raise ValueError("bias must be scalar or shape (1,)")
            self.bias = torch.nn.Parameter(bias.clone().detach().reshape(1).requires_grad_(True))
        else:
            self.bias = torch.nn.Parameter(torch.zeros(1))

    def forward(self, arguments: Tuple[Constant, ...]) -> torch.Tensor:
        features = torch.tensor(self.feature_map(arguments), dtype=self.weights.dtype, device=self.weights.device)
        if features.shape[0] != self.weights.shape[0]:
            raise ValueError("Feature dimension mismatch")
        score = torch.dot(self.weights, features) + self.bias
        return torch.sigmoid(score).clamp(0.0, 1.0)


def differentiable_truth_function(module: LinearFeatureTruthFunction) -> TruthFunction:
    """Adapter returning a callable that keeps autograd graph when needed."""

    def _fn(arguments: Tuple[Constant, ...]) -> float:
        with torch.no_grad():
            value = module(arguments)
        return float(value.detach())

    return _fn


class TableTruthFunction:
    """Truth function defined by explicit argument/value rows."""

    def __init__(self, table: Dict[Tuple[str, ...], float], default: float = 0.0) -> None:
        self.table = {}
        for key, value in table.items():
            if not 0.0 <= value <= 1.0:
                raise ValueError("Table truth function values must lie in [0, 1]")
            self.table[tuple(key)] = float(value)
        if not 0.0 <= default <= 1.0:
            raise ValueError("Default truth value must lie in [0, 1]")
        self.default = float(default)

    def __call__(self, arguments: Tuple[Constant, ...]) -> float:
        key = tuple(const.name for const in arguments)
        return self.table.get(key, self.default)
