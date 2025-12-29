"""Core data structures for the LIMEN-AI reference implementation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple


class Operator(str, Enum):
    """Enumerates the supported formula operators."""

    ATOM = "atom"
    CONST = "const"
    AND = "and"
    OR = "or"
    NOT = "not"
    IMPLIES = "implies"


@dataclass(frozen=True)
class Constant:
    """Represents an individual constant in the LIMEN-AI language."""

    name: str

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.name


@dataclass(frozen=True)
class Predicate:
    """Represents a predicate symbol with fixed arity."""

    name: str
    arity: int
    description: str = ""

    def __post_init__(self) -> None:
        if self.arity < 0:
            raise ValueError("Predicate arity must be non-negative")

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.name


@dataclass(frozen=True)
class Atom:
    """A grounded predicate application (predicate + arguments)."""

    predicate: Predicate
    arguments: Tuple[Constant, ...]

    def __post_init__(self) -> None:
        if len(self.arguments) != self.predicate.arity:
            raise ValueError(
                f"Atom {self.predicate.name} expects {self.predicate.arity} arguments, "
                f"got {len(self.arguments)}"
            )

    def __str__(self) -> str:  # pragma: no cover - trivial
        args = ", ".join(str(arg) for arg in self.arguments)
        return f"{self.predicate.name}({args})"


@dataclass
class TruthAssignment:
    """Stores fuzzy truth degrees for atoms in the knowledge base."""

    values: Dict[Atom, float] = field(default_factory=dict)

    def get(self, atom: Atom, default: float = 0.0) -> float:
        return self.values.get(atom, default)

    def set(self, atom: Atom, value: float) -> None:
        if not 0.0 <= value <= 1.0:
            raise ValueError("Truth values must lie in [0, 1]")
        self.values[atom] = value

    def copy(self) -> "TruthAssignment":
        return TruthAssignment(values=dict(self.values))

    @classmethod
    def from_iterable(cls, assignments: Iterable[Tuple[Atom, float]]) -> "TruthAssignment":
        inst = cls()
        for atom, value in assignments:
            inst.set(atom, value)
        return inst


TruthFunction = Callable[[Tuple[Constant, ...]], float]


@dataclass(frozen=True)
class FormulaNode:
    """A lightweight representation of a formula as a tree of operators."""

    operator: Operator
    children: Tuple["FormulaNode", ...] = ()
    atom: Optional[Atom] = None
    constant: Optional[float] = None

    @staticmethod
    def atom_node(atom: Atom) -> "FormulaNode":
        return FormulaNode(operator=Operator.ATOM, atom=atom)

    @staticmethod
    def constant_node(value: float) -> "FormulaNode":
        if not 0.0 <= value <= 1.0:
            raise ValueError("Constant nodes must be in [0, 1]")
        return FormulaNode(operator=Operator.CONST, constant=value)

    def with_children(self, *children: "FormulaNode") -> "FormulaNode":
        return FormulaNode(operator=self.operator, children=tuple(children))


@dataclass
class WeightedFormula:
    """Associates a formula node with a real-valued weight."""

    formula: FormulaNode
    weight: float
    name: Optional[str] = None

    def __str__(self) -> str:  # pragma: no cover - trivial
        label = self.name or "formula"
        return f"{label} (w={self.weight})"


class KnowledgeBase:
    """Container for predicates, constants, and weighted formulas."""

    def __init__(self) -> None:
        self.predicates: Dict[str, Predicate] = {}
        self.constants: Dict[str, Constant] = {}
        self.formulas: Sequence[WeightedFormula] = []
        self.truth_functions: Dict[str, TruthFunction] = {}
        self.induced_clauses: List["InducedClause"] = []
        self.label_store: Dict[str, Dict[str, Sequence[Tuple[str, ...]]]] = {}

    def add_predicate(self, predicate: Predicate) -> None:
        if predicate.name in self.predicates:
            raise ValueError(f"Predicate {predicate.name} already registered")
        self.predicates[predicate.name] = predicate

    def get_predicate(self, name: str) -> Predicate:
        if name not in self.predicates:
            raise KeyError(f"Predicate {name} not registered")
        return self.predicates[name]

    def add_constant(self, constant: Constant) -> None:
        if constant.name in self.constants:
            raise ValueError(f"Constant {constant.name} already registered")
        self.constants[constant.name] = constant

    def get_constant(self, name: str) -> Constant:
        if name not in self.constants:
            raise KeyError(f"Constant {name} not registered")
        return self.constants[name]

    def add_formula(self, formula: WeightedFormula) -> None:
        self.formulas = tuple(list(self.formulas) + [formula])

    def register_truth_function(self, predicate_name: str, func: TruthFunction) -> None:
        if predicate_name not in self.predicates:
            raise KeyError(f"Predicate {predicate_name} not registered")
        self.truth_functions[predicate_name] = func

    def evaluate_atom_via_function(self, atom: Atom) -> Optional[float]:
        func = self.truth_functions.get(atom.predicate.name)
        if func is None:
            return None
        return float(func(atom.arguments))

    def build_assignment_from_truth_functions(self) -> TruthAssignment:
        assignment = TruthAssignment()
        for atom in self.iter_atoms():
            value = self.evaluate_atom_via_function(atom)
            if value is not None:
                assignment.set(atom, value)
        return assignment

    def iter_atoms(self, extra_atoms: Optional[Iterable[Atom]] = None) -> Iterable[Atom]:
        seen = set()
        for formula in self.formulas:
            for atom in _collect_atoms(formula.formula):
                if atom not in seen:
                    seen.add(atom)
                    yield atom
        
        if extra_atoms:
            for atom in extra_atoms:
                if atom not in seen:
                    seen.add(atom)
                    yield atom

        for clause in self.induced_clauses:
            # We don't have the full grounding here, but we can't easily iter_atoms for induced clauses without a domain.
            # However, for the purpose of sampling, we usually care about atoms already mentioned.
            pass

    def register_induced_clause(self, clause: "InducedClause") -> None:
        self.induced_clauses.append(clause)

    def replace_induced_clauses(self, head_name: str, clauses: Sequence["InducedClause"]) -> None:
        self.induced_clauses = [c for c in self.induced_clauses if c.head != head_name] + list(clauses)

    def update_labels(
        self,
        label_updates: Dict[str, Dict[str, Sequence[Tuple[str, ...]]]],
        *,
        assignment: Optional["TruthAssignment"] = None,
        auto_induce: bool = False,
        induction_config: Optional[Dict[str, Any]] = None,
    ) -> None:
        for head, payload in label_updates.items():
            pos = payload.get("pos", ())
            neg = payload.get("neg", ())
            self.label_store[head] = {"pos": tuple(pos), "neg": tuple(neg)}
        if auto_induce:
            from .induction import run_induction_and_update_kb

            run_induction_and_update_kb(
                self,
                self.label_store,
                assignment=assignment,
                templates=None,
                config=induction_config,
            )


def _collect_atoms(node: FormulaNode) -> Iterable[Atom]:
    if node.operator == Operator.ATOM and node.atom is not None:
        yield node.atom
    for child in node.children:
        yield from _collect_atoms(child)


@dataclass
class InducedClause:
    head: str
    body: Tuple[str, ...]
    template: str
    weight: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:  # pragma: no cover - human-readable
        body_repr = ", ".join(self.body)
        return f"{self.head} :- {body_repr} (w={self.weight:.3f}, template={self.template})"
