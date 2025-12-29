"""Energy computation helpers for LIMEN-AI."""

from __future__ import annotations

from typing import Callable, Optional

import torch

from .core import FormulaNode, KnowledgeBase, TruthAssignment, WeightedFormula
from .semantics import evaluate_formula
from .semantics import evaluate_formula


def compute_energy(kb: KnowledgeBase, assignment: TruthAssignment) -> float:
    """Compute the scalar energy for a knowledge base under a truth assignment."""

    total = 0.0
    for wf in kb.formulas:
        value = evaluate_formula(wf.formula, assignment)
        total += wf.weight * value
    return float(total)


def compute_energy_torch(
    kb: KnowledgeBase,
    assignment_func: Callable[[WeightedFormula], torch.Tensor],
    device: Optional[torch.device] = None,
) -> torch.Tensor:
    """Torch-compatible energy that expects a per-formula evaluation callback."""

    device = device or torch.device("cpu")
    total = torch.zeros((), dtype=torch.float32, device=device)
    for wf in kb.formulas:
        value = assignment_func(wf)
        if not isinstance(value, torch.Tensor):
            raise TypeError("assignment_func must return torch.Tensor values")
        total = total + torch.tensor(wf.weight, device=device) * value.to(device)
    return total
