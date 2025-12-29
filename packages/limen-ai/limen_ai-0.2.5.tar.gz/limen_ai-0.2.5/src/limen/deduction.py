"""Rule-based atom generation for LIMEN-AI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from .core import Atom, FormulaNode, KnowledgeBase, Operator, TruthAssignment, WeightedFormula
from .semantics import evaluate_formula


@dataclass(frozen=True)
class GeneratedAtom:
    atom: Atom
    value: float
    previous_value: float
    rule_name: str


def _split_implication(formula: FormulaNode) -> Optional[Tuple[FormulaNode, Atom]]:
    if formula.operator != Operator.IMPLIES or len(formula.children) != 2:
        return None
    antecedent, consequent = formula.children
    if consequent.operator != Operator.ATOM or consequent.atom is None:
        return None
    return antecedent, consequent.atom


def generate_atoms(
    kb: KnowledgeBase,
    assignment: Optional[TruthAssignment] = None,
    *,
    threshold: float = 0.75,
    max_iterations: int = 5,
) -> Tuple[TruthAssignment, List[GeneratedAtom]]:
    """Applies implication rules to derive new atom truth values."""

    working = assignment.copy() if assignment is not None else TruthAssignment()
    generated: List[GeneratedAtom] = []

    for _ in range(max_iterations):
        updated = False
        for wf in kb.formulas:
            split = _split_implication(wf.formula)
            if split is None:
                continue
            antecedent, consequent_atom = split
            antecedent_value = evaluate_formula(antecedent, working)
            current = working.get(consequent_atom, 0.0)
            if antecedent_value >= threshold and antecedent_value > current:
                working.set(consequent_atom, antecedent_value)
                generated.append(
                    GeneratedAtom(
                        atom=consequent_atom,
                        value=antecedent_value,
                        previous_value=current,
                        rule_name=wf.name or "formula",
                    )
                )
                updated = True
        if not updated:
            break

    return working, generated

