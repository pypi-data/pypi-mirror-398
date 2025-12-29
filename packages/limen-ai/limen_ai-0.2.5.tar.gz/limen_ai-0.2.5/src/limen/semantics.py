"""Łukasiewicz semantics and formula evaluation utilities."""

from __future__ import annotations

from functools import reduce
from typing import Callable, Iterable, Sequence

import torch

from .core import Atom, FormulaNode, TruthAssignment, Operator


def lukasiewicz_and(a: float, b: float) -> float:
    """Łukasiewicz t-norm (fuzzy conjunction)."""

    return max(0.0, min(1.0, a + b - 1.0))


def lukasiewicz_or(a: float, b: float) -> float:
    """Łukasiewicz s-norm (fuzzy disjunction)."""

    return min(1.0, a + b)


def lukasiewicz_not(a: float) -> float:
    """Łukasiewicz negation."""

    return 1.0 - a


def lukasiewicz_implication(a: float, b: float) -> float:
    """Łukasiewicz implication."""

    return min(1.0, 1.0 - a + b)


def _aggregate(children, assignment: TruthAssignment, op: Callable[[float, float], float]) -> float:
    values = [evaluate_formula(child, assignment) for child in children]
    if not values:
        return 1.0
    return reduce(op, values)


def evaluate_formula(node: FormulaNode, assignment: TruthAssignment) -> float:
    """Recursively evaluate a formula node under a given truth assignment."""

    if node.operator == Operator.ATOM:
        if node.atom is None:
            raise ValueError("Atom node missing atom reference")
        return assignment.get(node.atom)
    if node.operator == Operator.CONST:
        if node.constant is None:
            raise ValueError("Constant node missing value")
        return node.constant
    if node.operator == Operator.AND:
        return _aggregate(node.children, assignment, lukasiewicz_and)
    if node.operator == Operator.OR:
        return _aggregate(node.children, assignment, lukasiewicz_or)
    if node.operator == Operator.NOT:
        if len(node.children) != 1:
            raise ValueError("NOT nodes must have exactly one child")
        return lukasiewicz_not(evaluate_formula(node.children[0], assignment))
    if node.operator == Operator.IMPLIES:
        if len(node.children) != 2:
            raise ValueError("IMPLIES nodes must have exactly two children")
        antecedent = evaluate_formula(node.children[0], assignment)
        consequent = evaluate_formula(node.children[1], assignment)
        return lukasiewicz_implication(antecedent, consequent)

    raise ValueError(f"Unknown operator: {node.operator}")


def evaluate_formula_batch(
    node: FormulaNode,
    assignments: Sequence[TruthAssignment],
) -> Sequence[float]:
    """Evaluates a formula across a batch of assignments."""

    return [evaluate_formula(node, assignment) for assignment in assignments]


def evaluate_formula_torch(
    node: FormulaNode,
    atom_resolver: Callable[[Atom], torch.Tensor],
) -> torch.Tensor:
    """Evaluates a formula using torch tensors for automatic differentiation."""

    if node.operator == Operator.ATOM:
        if node.atom is None:
            raise ValueError("Atom node missing atom reference")
        return atom_resolver(node.atom)
    if node.operator == Operator.CONST:
        if node.constant is None:
            raise ValueError("Constant node missing value")
        return torch.tensor(node.constant, dtype=torch.float32)
    if node.operator == Operator.AND:
        return _evaluate_tensor_children(node.children, atom_resolver, _torch_lukasiewicz_and, 1.0)
    if node.operator == Operator.OR:
        return _evaluate_tensor_children(node.children, atom_resolver, _torch_lukasiewicz_or, 0.0)
    if node.operator == Operator.NOT:
        if len(node.children) != 1:
            raise ValueError("NOT nodes must have exactly one child")
        return _torch_lukasiewicz_not(evaluate_formula_torch(node.children[0], atom_resolver))
    if node.operator == Operator.IMPLIES:
        if len(node.children) != 2:
            raise ValueError("IMPLIES nodes must have exactly two children")
        antecedent = evaluate_formula_torch(node.children[0], atom_resolver)
        consequent = evaluate_formula_torch(node.children[1], atom_resolver)
        return _torch_lukasiewicz_implies(antecedent, consequent)

    raise ValueError(f"Unknown operator: {node.operator}")


def _evaluate_tensor_children(
    children: Iterable[FormulaNode],
    resolver: Callable[[Atom], torch.Tensor],
    reducer: Callable[[torch.Tensor, torch.Tensor], torch.Tensor],
    neutral: float,
) -> torch.Tensor:
    tensors = [evaluate_formula_torch(child, resolver) for child in children]
    if not tensors:
        return torch.tensor(neutral, dtype=torch.float32)
    result = tensors[0]
    for tensor in tensors[1:]:
        result = reducer(result, tensor)
    return result


def _torch_lukasiewicz_and(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    return torch.clamp(a + b - 1.0, min=0.0, max=1.0)


def _torch_lukasiewicz_or(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    return torch.clamp(a + b, min=0.0, max=1.0)


def _torch_lukasiewicz_not(a: torch.Tensor) -> torch.Tensor:
    return torch.clamp(1.0 - a, min=0.0, max=1.0)


def _torch_lukasiewicz_implies(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    return torch.clamp(1.0 - a + b, min=0.0, max=1.0)
