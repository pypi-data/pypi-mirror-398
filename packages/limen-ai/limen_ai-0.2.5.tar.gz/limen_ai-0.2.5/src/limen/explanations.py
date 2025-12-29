"""Interpretability utilities for LIMEN-AI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence

from .core import KnowledgeBase, WeightedFormula
from .semantics import evaluate_formula


@dataclass(frozen=True)
class RuleExplanation:
    name: str
    weight: float
    activation: float
    contribution: float


def summarize_rule_contributions(kb: KnowledgeBase, assignment) -> List[RuleExplanation]:
    """Returns sorted rule contributions for a given assignment."""

    explanations: List[RuleExplanation] = []
    for wf in kb.formulas:
        activation = evaluate_formula(wf.formula, assignment)
        contribution = wf.weight * activation
        name = wf.name or "formula"
        explanations.append(
            RuleExplanation(
                name=name,
                weight=wf.weight,
                activation=activation,
                contribution=contribution,
            )
        )
    return sorted(explanations, key=lambda item: abs(item.contribution), reverse=True)


def format_explanations(explanations: Sequence[RuleExplanation], limit: int = 5) -> str:
    rows = ["Rule                        Weight  Activation  Contribution"]
    for explanation in explanations[:limit]:
        rows.append(
            f"{explanation.name:<26} {explanation.weight:>6.2f}     {explanation.activation:>6.3f}        {explanation.contribution:>6.3f}"
        )
    return "\n".join(rows)

