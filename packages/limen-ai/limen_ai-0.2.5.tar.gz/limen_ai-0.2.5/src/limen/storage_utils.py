"""Helper serialization utilities for LIMEN-AI storage layer."""

from __future__ import annotations

from typing import Dict

from .core import Atom, Constant, FormulaNode, KnowledgeBase, Predicate, Operator


def formula_to_dict(node: FormulaNode) -> Dict:
    """Recursively convert a FormulaNode into a JSON-serializable dict."""

    if node.operator == Operator.ATOM:
        if node.atom is None:
            raise ValueError("Atom node missing reference")
        return {
            "operator": node.operator.value,
            "predicate": node.atom.predicate.name,
            "arguments": [const.name for const in node.atom.arguments],
        }
    if node.operator == Operator.CONST:
        return {"operator": node.operator.value, "value": node.constant}
    return {
        "operator": node.operator.value,
        "children": [formula_to_dict(child) for child in node.children],
    }


def dict_to_formula(data: Dict, kb: KnowledgeBase) -> FormulaNode:
    op = Operator(data["operator"])
    if op == Operator.ATOM:
        predicate = kb.get_predicate(data["predicate"])
        arguments = tuple(kb.get_constant(name) for name in data["arguments"])
        return FormulaNode.atom_node(Atom(predicate=predicate, arguments=arguments))
    if op == Operator.CONST:
        return FormulaNode.constant_node(data["value"])
    children = tuple(dict_to_formula(child, kb) for child in data.get("children", []))
    return FormulaNode(operator=op, children=children)
