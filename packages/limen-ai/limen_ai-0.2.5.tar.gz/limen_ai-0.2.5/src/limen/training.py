"""Training helpers for differentiable truth functions in LIMEN-AI."""

from __future__ import annotations

from typing import Callable, Dict, Mapping, Tuple

import torch

from .core import FormulaNode, KnowledgeBase, Operator, WeightedFormula
from .energy import compute_energy_torch


def _infer_device_dtype(modules: Mapping[str, torch.nn.Module]) -> Tuple[torch.device, torch.dtype]:
    for module in modules.values():
        params = list(module.parameters())
        if params:
            return params[0].device, params[0].dtype
    return torch.device("cpu"), torch.float32


def _torch_and(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    return torch.clamp(a + b - 1.0, min=0.0, max=1.0)


def _torch_or(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    return torch.clamp(a + b, min=0.0, max=1.0)


def _torch_not(a: torch.Tensor) -> torch.Tensor:
    return torch.clamp(1.0 - a, min=0.0, max=1.0)


def _torch_implication(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    return torch.clamp(1.0 - a + b, min=0.0, max=1.0)


class TorchFormulaEvaluator:
    """Evaluates weighted formulas using differentiable truth functions."""

    def __init__(self, module_registry: Mapping[str, torch.nn.Module]) -> None:
        if not module_registry:
            raise ValueError("module_registry must contain at least one entry")
        self.module_registry = module_registry
        self.default_device, self.default_dtype = _infer_device_dtype(module_registry)

    def __call__(self, wf: WeightedFormula) -> torch.Tensor:
        return self._evaluate_node(wf.formula)

    def _evaluate_node(self, node: FormulaNode) -> torch.Tensor:
        if node.operator == Operator.ATOM:
            if node.atom is None:
                raise ValueError("Atom node requires an atom reference")
            module = self.module_registry.get(node.atom.predicate.name)
            if module is None:
                raise KeyError(f"No differentiable truth function registered for {node.atom.predicate.name}")
            return module(node.atom.arguments)

        if node.operator == Operator.CONST:
            if node.constant is None:
                raise ValueError("Constant node missing value")
            return torch.tensor(node.constant, dtype=self.default_dtype, device=self.default_device)

        if node.operator == Operator.AND:
            return self._aggregate(node.children, _torch_and, 1.0)

        if node.operator == Operator.OR:
            return self._aggregate(node.children, _torch_or, 0.0)

        if node.operator == Operator.NOT:
            if len(node.children) != 1:
                raise ValueError("NOT nodes must have exactly one child")
            return _torch_not(self._evaluate_node(node.children[0]))

        if node.operator == Operator.IMPLIES:
            if len(node.children) != 2:
                raise ValueError("IMPLIES nodes must have exactly two children")
            antecedent = self._evaluate_node(node.children[0])
            consequent = self._evaluate_node(node.children[1])
            return _torch_implication(antecedent, consequent)

        raise ValueError(f"Unsupported operator: {node.operator}")

    def _aggregate(
        self,
        children: Tuple[FormulaNode, ...],
        reducer: Callable[[torch.Tensor, torch.Tensor], torch.Tensor],
        neutral: float,
    ) -> torch.Tensor:
        values = [self._evaluate_node(child) for child in children]
        if not values:
            return torch.tensor(neutral, dtype=self.default_dtype, device=self.default_device)
        result = values[0]
        for value in values[1:]:
            result = reducer(result, value)
        return result


class TruthFunctionTrainer:
    """Simple gradient-based trainer for differentiable truth functions."""

    def __init__(
        self,
        kb: KnowledgeBase,
        module_registry: Mapping[str, torch.nn.Module],
        optimizer: torch.optim.Optimizer,
    ) -> None:
        self.kb = kb
        self.module_registry = module_registry
        self.optimizer = optimizer
        self._evaluator = TorchFormulaEvaluator(module_registry)

    def step(self) -> float:
        """Performs one optimisation step and returns the scalar energy."""

        self.optimizer.zero_grad()
        energy = compute_energy_torch(self.kb, self._evaluator)
        energy.backward()
        self.optimizer.step()
        return float(energy.detach().cpu().item())

    def current_energy(self) -> float:
        """Evaluates the current scalar energy without gradient tracking."""

        with torch.no_grad():
            energy = compute_energy_torch(self.kb, self._evaluator)
        return float(energy.cpu().item())

    def train(self, steps: int) -> list[float]:
        """Runs multiple optimisation steps, returning the energy trace."""

        history = []
        for _ in range(steps):
            history.append(self.step())
        return history

