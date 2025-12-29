"""Document ingestion pipeline that feeds facts into LIMEN-AI via an LLM."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple

from ..core import Atom, Constant, KnowledgeBase, TruthAssignment
from .llm_client import LLMClient
from .prompts import build_extraction_prompt, extract_candidate_tokens
from .schema import SchemaRegistry


@dataclass
class ParsedFact:
    predicate: str
    args: Tuple[str, ...]
    confidence: float = 1.0
    provenance: Optional[str] = None


@dataclass
class IngestionResult:
    facts_added: List[ParsedFact] = field(default_factory=list)
    rejected_chunks: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


def _extract_json_payload(text: str) -> str:
    """Return the first valid JSON object/array substring within text."""

    text = text.strip()
    start_idx: Optional[int] = None
    stack: List[str] = []
    in_string = False
    escape = False

    for idx, ch in enumerate(text):
        if start_idx is None:
            if ch in "[{":
                start_idx = idx
                stack.append(ch)
            continue

        if escape:
            escape = False
            continue

        if ch == "\\":
            escape = True
            continue

        if ch == '"':
            in_string = not in_string
            continue

        if in_string:
            continue

        if ch in "[{":
            stack.append(ch)
            continue

        if ch in "]}":
            if not stack:
                break
            opener = stack.pop()
            if (opener == "[" and ch != "]") or (opener == "{" and ch != "}"):
                break
            if not stack:
                return text[start_idx : idx + 1]

    if start_idx is not None:
        return text[start_idx:]
    return text

def _chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
    tokens = text.split()
    chunks: List[str] = []
    i = 0
    while i < len(tokens):
        chunk = tokens[i : i + chunk_size]
        chunks.append(" ".join(chunk))
        i += max(chunk_size - overlap, 1)
    return chunks


class DocumentIngestionPipeline:
    """Coordinates chunking, prompting, parsing, and KB insertion."""

    def __init__(
        self,
        registry: SchemaRegistry,
        llm_client: LLMClient,
        chunk_size: int = 800,
        overlap: int = 80,
        min_confidence: float = 0.4,
    ) -> None:
        self.registry = registry
        self.llm = llm_client
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.min_confidence = min_confidence

    def ingest(
        self,
        text: str,
        kb: KnowledgeBase,
        *,
        assignment: Optional[TruthAssignment] = None,
    ) -> IngestionResult:
        result = IngestionResult()
        for chunk in _chunk_text(text, self.chunk_size, self.overlap):
            tokens = extract_candidate_tokens(chunk)
            prompt = build_extraction_prompt(
                chunk, self.registry, candidate_tokens=tokens
            )
            self._ingest_from_prompt(prompt, chunk, chunk, kb, assignment, result)
        return result

    def ingest_prompts(
        self,
        prompts: Sequence[str],
        kb: KnowledgeBase,
        *,
        assignment: Optional[TruthAssignment] = None,
    ) -> IngestionResult:
        """Executes user-supplied prompts (already formatted) and inserts resulting facts."""

        result = IngestionResult()
        for prompt in prompts:
            self._ingest_from_prompt(
                prompt,
                chunk_text=None,
                source_label=prompt.strip() or None,
                kb=kb,
                assignment=assignment,
                result=result,
            )
        return result

    def _ensure_constant(self, kb: KnowledgeBase, name: str) -> Constant:
        if name in kb.constants:
            return kb.constants[name]
        constant = Constant(name)
        kb.add_constant(constant)
        return constant

    def _ingest_from_prompt(
        self,
        prompt: str,
        chunk_text: Optional[str],
        source_label: Optional[str],
        kb: KnowledgeBase,
        assignment: Optional[TruthAssignment],
        result: IngestionResult,
    ) -> None:
        completion = self.llm.complete(prompt)
        parsed = self._parse_completion(completion, chunk_text)
        if not parsed:
            if source_label:
                result.rejected_chunks.append(source_label)
            return
        seen = set()
        for fact in parsed:
            key = (fact.predicate, fact.args)
            if key in seen:
                continue
            ok, message = self.registry.validate_fact(fact.predicate, fact.args)
            if not ok:
                result.errors.append(message)
                continue
            schema = self.registry.get(fact.predicate)
            if schema and all(
                arg.strip().lower() == placeholder.strip().lower()
                for arg, placeholder in zip(fact.args, schema.arg_names)
            ):
                result.errors.append(
                    f"Predicate {fact.predicate} ignored because the LLM returned placeholder args: {fact.args}"
                )
                continue
            if fact.confidence < self.min_confidence:
                continue
            predicate = self.registry.ensure_in_kb(fact.predicate, kb)
            constants = tuple(self._ensure_constant(kb, name) for name in fact.args)
            atom = Atom(predicate, constants)
            if assignment is not None:
                assignment.set(atom, fact.confidence)
            result.facts_added.append(fact)
            seen.add(key)

    def _parse_completion(self, completion: str, chunk_text: str | None = None) -> List[ParsedFact]:
        completion = completion.strip()
        if not completion:
            return []
        payload = _extract_json_payload(completion)
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return []
        facts: List[ParsedFact] = []
        if isinstance(data, dict) and "facts" in data:
            data = data["facts"]
        if not isinstance(data, list):
            return []
        chunk_lower = chunk_text.lower() if chunk_text else None
        for item in data:
            raw_predicate = item.get("predicate")
            if raw_predicate is None:
                continue
            predicate = re.split(r"[\s(]", str(raw_predicate).strip(), 1)[0]
            args: Sequence[str] = item.get("args", [])
            confidence = float(item.get("confidence", 1.0))
            provenance = item.get("provenance")
            if predicate and isinstance(args, list):
                normalized_args = tuple(str(arg) for arg in args)
                if chunk_lower and not all(str(arg).strip().lower() in chunk_lower for arg in normalized_args):
                    continue
                facts.append(
                    ParsedFact(
                        predicate=predicate,
                        args=normalized_args,
                        confidence=confidence,
                        provenance=provenance,
                    )
                )
        return facts
