"""SQLite-backed persistence helpers for LIMEN-AI knowledge bases."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable, Tuple

from .core import Constant, KnowledgeBase, Predicate, WeightedFormula
from .storage_utils import dict_to_formula, formula_to_dict


_SCHEMA = """
CREATE TABLE IF NOT EXISTS predicates (
    name TEXT PRIMARY KEY,
    arity INTEGER NOT NULL,
    description TEXT
);
CREATE TABLE IF NOT EXISTS constants (
    name TEXT PRIMARY KEY
);
CREATE TABLE IF NOT EXISTS formulas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    weight REAL NOT NULL,
    serialized TEXT NOT NULL
);
"""


def save_knowledge_base(kb: KnowledgeBase, db_path: str | Path) -> None:
    """Persist the given knowledge base into an SQLite database file."""

    path = Path(db_path)
    with sqlite3.connect(path) as conn:
        conn.executescript(_SCHEMA)
        conn.execute("DELETE FROM predicates")
        conn.execute("DELETE FROM constants")
        conn.execute("DELETE FROM formulas")

        conn.executemany(
            "INSERT INTO predicates(name, arity, description) VALUES (?, ?, ?)",
            ((pred.name, pred.arity, pred.description) for pred in kb.predicates.values()),
        )
        conn.executemany(
            "INSERT INTO constants(name) VALUES (?)",
            ((const.name,) for const in kb.constants.values()),
        )

        formula_rows: Iterable[Tuple[str | None, float, str]] = (
            (
                wf.name,
                wf.weight,
                json.dumps(formula_to_dict(wf.formula)),
            )
            for wf in kb.formulas
        )
        conn.executemany(
            "INSERT INTO formulas(name, weight, serialized) VALUES (?, ?, ?)",
            formula_rows,
        )
        conn.commit()


def load_knowledge_base(db_path: str | Path) -> KnowledgeBase:
    """Load a knowledge base from the given SQLite database file."""

    path = Path(db_path)
    kb = KnowledgeBase()
    with sqlite3.connect(path) as conn:
        for name, arity, description in conn.execute("SELECT name, arity, description FROM predicates"):
            kb.add_predicate(Predicate(name=name, arity=arity, description=description or ""))
        for (name,) in conn.execute("SELECT name FROM constants"):
            kb.add_constant(Constant(name=name))
        for name, weight, serialized in conn.execute(
            "SELECT name, weight, serialized FROM formulas ORDER BY id"
        ):
            data = json.loads(serialized)
            formula = dict_to_formula(data, kb)
            kb.add_formula(WeightedFormula(formula=formula, weight=weight, name=name))
    return kb
