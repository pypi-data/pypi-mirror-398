"""Sampling utilities for LIMEN-AI inference."""

from __future__ import annotations

import random
from typing import Dict, Iterable, List, Optional, Tuple

from .core import Atom, KnowledgeBase, Operator, TruthAssignment
from .semantics import evaluate_formula


def _collect_atoms(kb: KnowledgeBase) -> Tuple[Atom, ...]:
    return tuple(kb.iter_atoms())


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def make_uniform_proposal(kb: KnowledgeBase, rng: Optional[random.Random] = None):
    """Returns a proposal callable that samples each atom uniformly in [0, 1]."""

    atoms = _collect_atoms(kb)
    rng = rng or random.Random()

    def _proposal() -> TruthAssignment:
        assignment = TruthAssignment()
        for atom in atoms:
            assignment.set(atom, rng.random())
        return assignment

    return _proposal


def make_tempered_proposal(
    kb: KnowledgeBase,
    reference: Optional[TruthAssignment] = None,
    temperature: float = 0.1,
    rng: Optional[random.Random] = None,
):
    """Returns a proposal that perturbs a reference assignment with Gaussian noise."""

    atoms = _collect_atoms(kb)
    rng = rng or random.Random()
    reference = reference or kb.build_assignment_from_truth_functions()

    def _proposal() -> TruthAssignment:
        assignment = TruthAssignment()
        for atom in atoms:
            base = reference.get(atom, 0.5)
            value = base + rng.gauss(0.0, temperature)
            assignment.set(atom, _clamp(value))
        return assignment

    return _proposal


def make_score_guided_proposal(
    kb: KnowledgeBase,
    temperature: float = 0.05,
    reference: Optional[TruthAssignment] = None,
    rng: Optional[random.Random] = None,
):
    """Proposal that biases sampling according to rule weights or truth functions."""

    rng = rng or random.Random()
    atoms = _collect_atoms(kb)
    if reference is None:
        reference = kb.build_assignment_from_truth_functions()
    priors = _atom_weight_priors(kb)

    def _proposal() -> TruthAssignment:
        assignment = TruthAssignment()
        for atom in atoms:
            base = reference.get(atom, priors.get(atom, 0.5))
            value = base + rng.gauss(0.0, temperature)
            assignment.set(atom, _clamp(value))
        return assignment

    return _proposal


def _formula_atoms(node) -> Iterable[Atom]:
    """Helper to collect atoms from a single formula tree."""
    from .core import Operator
    if node.operator == Operator.ATOM and node.atom is not None:
        yield node.atom
    for child in node.children:
        yield from _formula_atoms(child)


def _atom_weight_priors(kb: KnowledgeBase) -> Dict[Atom, float]:
    totals: Dict[Atom, float] = {}
    max_total = 0.0
    for wf in kb.formulas:
        for atom in _formula_atoms(wf.formula):
            totals[atom] = totals.get(atom, 0.0) + abs(wf.weight)
            max_total = max(max_total, totals[atom])

    if max_total == 0.0:
        return {}

    return {atom: value / max_total for atom, value in totals.items()}


def make_mixture_proposal(
    kb: KnowledgeBase,
    centers: List[TruthAssignment],
    uniform_weight: float = 0.2,
    temperature: float = 0.05,
    rng: Optional[random.Random] = None,
):
    """Returns a mixture proposal (Uniform + several Gaussian centers)."""
    
    rng = rng or random.Random()
    atoms = _collect_atoms(kb)
    
    def _proposal() -> TruthAssignment:
        assignment = TruthAssignment()
        
        # Select which component to sample from
        if rng.random() < uniform_weight or not centers:
            # Uniform component
            for atom in atoms:
                assignment.set(atom, rng.random())
        else:
            # Gaussian component centered at one of the previous samples
            center = rng.choice(centers)
            for atom in atoms:
                base = center.get(atom, 0.5)
                value = base + rng.gauss(0.0, temperature)
                assignment.set(atom, _clamp(value))
        return assignment

    return _proposal


def rule_activation_trace(kb: KnowledgeBase, assignment: TruthAssignment) -> Dict[str, float]:
    """Returns a dict mapping rule names to satisfaction degrees under an assignment."""

    trace: Dict[str, float] = {}
    for wf in kb.formulas:
        name = wf.name or "formula"
        trace[name] = evaluate_formula(wf.formula, assignment)
    return trace
