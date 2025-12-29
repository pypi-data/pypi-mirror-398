"""Schema registry for predicates and arguments used by LIMEN-AI + LLM pipelines."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Sequence, Tuple

from ..core import Predicate


@dataclass
class PredicateSchema:
    """Describes a predicate available in the knowledge base."""

    name: str
    arity: int
    arg_names: Sequence[str]
    description: str = ""

    def __post_init__(self) -> None:
        if len(self.arg_names) != self.arity:
            raise ValueError(
                f"Predicate {self.name} expects {self.arity} argument names, got {len(self.arg_names)}"
            )


@dataclass
class SchemaRegistry:
    """Central registry of predicate schemas used by the ingestion/query layers."""

    predicates: Dict[str, PredicateSchema] = field(default_factory=dict)

    def register(self, schema: PredicateSchema) -> None:
        self.predicates[schema.name] = schema

    def get(self, name: str) -> PredicateSchema | None:
        return self.predicates.get(name)

    def ensure_in_kb(self, name: str, kb) -> Predicate:
        schema = self.get(name)
        if schema is None:
            raise KeyError(f"Predicate {name} is not registered in the schema registry")
        if name in kb.predicates:
            return kb.predicates[name]
        predicate = Predicate(name, schema.arity, description=schema.description)
        kb.add_predicate(predicate)
        return predicate

    def validate_fact(self, predicate_name: str, args: Sequence[str]) -> Tuple[bool, str]:
        schema = self.get(predicate_name)
        if schema is None:
            return False, f"Predicate {predicate_name} is not known"
        if len(args) != schema.arity:
            return (
                False,
                f"Predicate {predicate_name} expects {schema.arity} args, got {len(args)}",
            )
        return True, ""

    def as_instruction(self) -> str:
        """Return a textual summary for prompt construction."""
        lines = ["Available predicates:"]
        for schema in self.predicates.values():
            arg_list = ", ".join(schema.arg_names)
            desc = f" - {schema.description}" if schema.description else ""
            lines.append(f"- {schema.name}({arg_list}){desc}")
        return "\n".join(lines)

    def extend(self, schemas: Iterable[PredicateSchema]) -> None:
        for schema in schemas:
            self.register(schema)

