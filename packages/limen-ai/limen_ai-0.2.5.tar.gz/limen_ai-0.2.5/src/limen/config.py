"""Configuration utilities and validation for building LIMEN-AI knowledge bases."""

from __future__ import annotations

from dataclasses import dataclass
from numbers import Number
from typing import Any, Callable, Dict, List, Tuple

from .core import Constant, KnowledgeBase, Predicate, WeightedFormula
from .storage_utils import dict_to_formula
from .truth_functions import ConstantTruthFunction, TableTruthFunction

TruthFunctionFactory = Callable[[Dict[str, Any]], Callable]


@dataclass
class ValidationIssue:
    location: str
    message: str
    severity: str = "error"


def _table_factory(spec: Dict[str, Any]) -> TableTruthFunction:
    rows = spec.get("values", [])
    mapping: Dict[Tuple[str, ...], float] = {}
    for row in rows:
        args = tuple(row.get("arguments", []))
        if not args:
            raise ValueError("Table truth function rows must supply 'arguments'")
        value = row.get("value")
        if value is None:
            raise ValueError("Table truth function rows must supply 'value'")
        mapping[args] = float(value)
    default = float(spec.get("default", 0.0))
    return TableTruthFunction(mapping, default=default)


_TRUTH_FUNCTION_FACTORIES: Dict[str, TruthFunctionFactory] = {
    "constant": lambda spec: ConstantTruthFunction(spec["value"]),
    "table": _table_factory,
}


def register_truth_function_factory(name: str, factory: TruthFunctionFactory) -> None:
    """Registers a new truth-function factory for config loading."""

    if not name:
        raise ValueError("Factory name must be non-empty")
    _TRUTH_FUNCTION_FACTORIES[name] = factory


def available_truth_function_types() -> List[str]:
    return sorted(_TRUTH_FUNCTION_FACTORIES.keys())


def _formula_predicates(serialized: Dict[str, Any]) -> List[str]:
    preds = []
    if serialized.get("operator") == "atom":
        preds.append(serialized.get("predicate"))
    for child in serialized.get("children", []):
        preds.extend(_formula_predicates(child))
    return preds


def _formula_constants(serialized: Dict[str, Any]) -> List[str]:
    constants = []
    if serialized.get("operator") == "atom":
        constants.extend(serialized.get("arguments", []))
    for child in serialized.get("children", []):
        constants.extend(_formula_constants(child))
    return constants


def validate_config(config: Dict[str, Any]) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []

    predicate_names: List[str] = []
    predicate_arities: Dict[str, int] = {}
    for idx, pred_spec in enumerate(config.get("predicates", [])):
        location = f"predicates[{idx}]"
        name = pred_spec.get("name")
        arity = pred_spec.get("arity")
        if not isinstance(name, str) or not name:
            issues.append(ValidationIssue(location, "Predicate name must be a non-empty string"))
            continue
        if name in predicate_names:
            issues.append(ValidationIssue(location, f"Duplicate predicate name '{name}'"))
        predicate_names.append(name)
        if not isinstance(arity, int) or arity < 0:
            issues.append(ValidationIssue(location, "Predicate arity must be a non-negative integer"))
        else:
            predicate_arities[name] = arity

    constants = config.get("constants", [])
    if not isinstance(constants, list):
        issues.append(ValidationIssue("constants", "Constants must be provided as a list"))
    else:
        seen = set()
        for idx, const in enumerate(constants):
            if not isinstance(const, str) or not const:
                issues.append(ValidationIssue(f"constants[{idx}]", "Constants must be non-empty strings"))
            if const in seen:
                issues.append(ValidationIssue(f"constants[{idx}]", f"Duplicate constant '{const}'"))
            seen.add(const)

    formulas = config.get("formulas", [])
    if not isinstance(formulas, list):
        issues.append(ValidationIssue("formulas", "Formulas must be provided as a list"))
    else:
        for idx, form_spec in enumerate(formulas):
            location = f"formulas[{idx}]"
            weight = form_spec.get("weight")
            if not isinstance(weight, Number):
                issues.append(ValidationIssue(location, "Formula weight must be numeric"))
            serialized = form_spec.get("formula")
            if not isinstance(serialized, dict):
                issues.append(ValidationIssue(location, "Formula must include a serialized structure"))
                continue
            for pred in _formula_predicates(serialized):
                if pred not in predicate_names:
                    issues.append(ValidationIssue(location, f"Formula references unknown predicate '{pred}'"))
            for const in _formula_constants(serialized):
                if const not in constants:
                    issues.append(ValidationIssue(location, f"Formula references unknown constant '{const}'"))

    truth_functions = config.get("truth_functions", [])
    if not isinstance(truth_functions, list):
        issues.append(ValidationIssue("truth_functions", "Truth functions must be provided as a list"))
    else:
        for idx, tf_spec in enumerate(truth_functions):
            location = f"truth_functions[{idx}]"
            predicate = tf_spec.get("predicate")
            if predicate not in predicate_names:
                issues.append(ValidationIssue(location, f"Truth function references unknown predicate '{predicate}'"))
            tf_type = tf_spec.get("type", "constant")
            if tf_type not in _TRUTH_FUNCTION_FACTORIES:
                issues.append(ValidationIssue(location, f"Unsupported truth function type '{tf_type}'"))
            if tf_type == "constant":
                value = tf_spec.get("value")
                if not isinstance(value, Number) or not (0.0 <= value <= 1.0):
                    issues.append(ValidationIssue(location, "Constant truth function requires 'value' in [0, 1]"))
            if tf_type == "table":
                arity = predicate_arities.get(predicate, 0)
                rows = tf_spec.get("values", [])
                if not isinstance(rows, list) or not rows:
                    issues.append(ValidationIssue(location, "Table truth function must provide a non-empty 'values' list"))
                else:
                    for row_idx, row in enumerate(rows):
                        args = row.get("arguments")
                        value = row.get("value")
                        if not isinstance(args, list) or len(args) != arity:
                            issues.append(
                                ValidationIssue(
                                    f"{location}.values[{row_idx}]",
                                    f"Expected {arity} arguments for predicate '{predicate}'",
                                )
                            )
                        if not isinstance(value, Number) or not (0.0 <= value <= 1.0):
                            issues.append(
                                ValidationIssue(
                                    f"{location}.values[{row_idx}]",
                                    "Row 'value' must be numeric in [0, 1]",
                                )
                            )
                default = tf_spec.get("default", 0.0)
                if not isinstance(default, Number) or not (0.0 <= default <= 1.0):
                    issues.append(ValidationIssue(location, "Table truth function 'default' must be in [0, 1]"))

    return issues


def load_kb_from_config(config: Dict[str, Any], *, validate: bool = True) -> KnowledgeBase:
    if validate:
        issues = validate_config(config)
        if issues:
            details = "; ".join(f"{issue.location}: {issue.message}" for issue in issues)
            raise ValueError(f"Configuration validation failed: {details}")

    kb = KnowledgeBase()

    for pred_spec in config.get("predicates", []):
        predicate = Predicate(
            name=pred_spec["name"],
            arity=pred_spec["arity"],
            description=pred_spec.get("description", ""),
        )
        kb.add_predicate(predicate)

    for const_name in config.get("constants", []):
        kb.add_constant(Constant(const_name))

    for form_spec in config.get("formulas", []):
        serialized = form_spec["formula"]
        node = dict_to_formula(serialized, kb)
        weight = form_spec["weight"]
        name = form_spec.get("name")
        kb.add_formula(WeightedFormula(formula=node, weight=weight, name=name))

    for tf_spec in config.get("truth_functions", []):
        predicate_name = tf_spec["predicate"]
        tf_type = tf_spec.get("type", "constant")
        factory = _TRUTH_FUNCTION_FACTORIES.get(tf_type)
        if factory is None:
            raise ValueError(f"Unsupported truth function type: {tf_type}")
        tf = factory(tf_spec)
        kb.register_truth_function(predicate_name, tf)

    return kb
