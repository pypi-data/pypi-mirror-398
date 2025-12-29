"""Translate natural-language prompts into structured LIMEN-AI queries."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, List, Tuple

from .llm_client import LLMClient
from .prompts import build_query_prompt
from .schema import SchemaRegistry


@dataclass
class StructuredQuery:
    predicate: str
    args: Tuple[str, ...]


class QueryTranslator:
    def __init__(self, registry: SchemaRegistry, llm_client: LLMClient):
        self.registry = registry
        self.llm = llm_client

    def translate(self, prompt: str) -> List[StructuredQuery]:
        completion = self.llm.complete(build_query_prompt(prompt, self.registry))
        
        # LOGGING FOR AUDITABILITY
        print(f"\n[DEBUG] Query Translation Raw Output:\n{completion}\n")
        
        payload = self._safe_json(completion)
        queries: List[StructuredQuery] = []
        for entry in payload.get("queries", []):
            predicate = entry.get("predicate")
            args = entry.get("args", [])
            ok, _ = self.registry.validate_fact(predicate, args)
            if ok:
                queries.append(StructuredQuery(predicate, tuple(args)))

        return queries

    def _safe_json(self, completion: str) -> Dict:
        from ..orchestrator import _extract_json_payload
        import re
        
        payload_str = _extract_json_payload(completion.strip())
        # Basic JSON repair
        payload_str = re.sub(r',\s*([\]}])', r'\1', payload_str)
        
        if not payload_str:
            return {"queries": []}
        try:
            return json.loads(payload_str)
        except json.JSONDecodeError:
            return {"queries": []}

