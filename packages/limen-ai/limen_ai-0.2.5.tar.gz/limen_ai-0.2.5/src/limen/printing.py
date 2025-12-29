"""Utilities to format LIMEN-AI knowledge bases for inspection."""

from __future__ import annotations

from typing import List

from .core import KnowledgeBase


def format_kb(kb: KnowledgeBase) -> str:
    """Returns a human-readable description of predicates, constants, and formulas."""

    lines: List[str] = []
    lines.append("Predicates:")
    for predicate in kb.predicates.values():
        lines.append(f"  - {predicate.name}/{predicate.arity} : {predicate.description}")

    lines.append("Constants:")
    for constant in kb.constants.values():
        lines.append(f"  - {constant.name}")

    lines.append("Formulas:")
    for wf in kb.formulas:
        name = wf.name or "formula"
        lines.append(f"  - {name} (weight={wf.weight})")

    if kb.truth_functions:
        lines.append("Truth Functions:")
        for predicate_name in kb.truth_functions.keys():
            lines.append(f"  - {predicate_name}")

    return "\n".join(lines)

