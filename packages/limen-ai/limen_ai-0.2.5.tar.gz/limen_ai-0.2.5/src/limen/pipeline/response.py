"""Response generation for LIMEN-AI answers using (optional) LLM assistance."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import List, Optional

from ..core import KnowledgeBase
from .llm_client import LLMClient
from .prompts import build_response_prompt


@dataclass
class StructuredAnswer:
    question: str
    target_predicate: str
    value: float
    explanation_rows: List[str]
    provenance: Optional[str] = None


class ResponseGenerator:
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client

    def to_text(self, answer: StructuredAnswer) -> str:
        structured = {
            "predicate": answer.target_predicate,
            "value": answer.value,
            "explanations": answer.explanation_rows,
            "provenance": answer.provenance,
        }
        structured_json = json.dumps(structured, indent=2)
        if self.llm is None:
            explanations = "\n".join(answer.explanation_rows)
            return (
                f"Answer: {answer.value:.3f} likelihood for {answer.target_predicate}.\n"
                f"Rationale:\n{explanations}"
            )
        prompt = build_response_prompt(structured_json, answer.question)
        return self.llm.complete(prompt)

