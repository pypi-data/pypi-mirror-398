"""Grounding and observation utilities for LIMEN-AI knowledge bases."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .core import Atom, Constant, KnowledgeBase, Predicate, TruthAssignment


@dataclass(frozen=True)
class GroundingPlan:
    predicate: str
    domains: Optional[Sequence[Sequence[str]]] = None


def _resolve_constants(kb: KnowledgeBase, names: Sequence[str]) -> Tuple[Constant, ...]:
    return tuple(kb.get_constant(name) for name in names)


def generate_ground_atoms(
    kb: KnowledgeBase,
    predicate_name: str,
    domains: Optional[Sequence[Sequence[str]]] = None,
) -> List[Atom]:
    """Returns all grounded atoms for a predicate using the provided constant domains."""

    predicate = kb.get_predicate(predicate_name)
    if predicate.arity == 0:
        return [Atom(predicate, tuple())]

    if domains is None:
        pools = [list(kb.constants.keys()) for _ in range(predicate.arity)]
    else:
        if len(domains) != predicate.arity:
            raise ValueError(
                f"Expected {predicate.arity} domains for predicate {predicate.name}, got {len(domains)}"
            )
        pools = domains

    atoms: List[Atom] = []
    for combo in product(*pools):
        constants = _resolve_constants(kb, combo)
        atoms.append(Atom(predicate, constants))
    return atoms


def auto_ground(kb: KnowledgeBase, plans: Sequence[GroundingPlan]) -> List[Atom]:
    """Grounds multiple predicates according to a sequence of plans."""

    atoms: List[Atom] = []
    for plan in plans:
        atoms.extend(generate_ground_atoms(kb, plan.predicate, plan.domains))
    return atoms


def assignment_from_observations(
    kb: KnowledgeBase,
    observations: Mapping[str, Sequence[Mapping[str, object]]],
    *,
    default_value: float = 1.0,
) -> TruthAssignment:
    """Constructs a truth assignment from structured observations."""

    assignment = TruthAssignment()
    for predicate_name, entries in observations.items():
        predicate = kb.get_predicate(predicate_name)
        for entry in entries:
            arg_names = entry.get("arguments", [])
            if not isinstance(arg_names, Sequence):
                raise ValueError("Observation 'arguments' must be a sequence")
            constants = tuple(kb.get_constant(name) for name in arg_names)
            if len(constants) != predicate.arity:
                raise ValueError(
                    f"Predicate {predicate_name} expects {predicate.arity} arguments, got {len(constants)}"
                )
            atom = Atom(predicate, constants)
            value = float(entry.get("value", default_value))
            assignment.set(atom, value)
    return assignment

