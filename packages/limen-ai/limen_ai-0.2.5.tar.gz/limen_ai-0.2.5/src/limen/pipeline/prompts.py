"""Prompt templates for LIMEN-AI + LLM orchestration."""

from __future__ import annotations

import re
from textwrap import dedent
from typing import Optional, Sequence

from .schema import PredicateSchema, SchemaRegistry


def extract_candidate_tokens(text: str, limit: int = 12) -> list[str]:
    """Return literal entity strings that appear inside a text chunk."""

    tokens: list[str] = []
    seen: set[str] = set()

    for match in re.findall(r"`([^`]+)`", text):
        candidate = match.strip()
        if candidate and candidate not in seen:
            tokens.append(candidate)
            seen.add(candidate)
        if len(tokens) >= limit:
            return tokens

    for match in re.findall(r"\b[A-Z][A-Za-z0-9_.-]*\b", text):
        candidate = match.strip()
        if candidate and candidate not in seen:
            tokens.append(candidate)
            seen.add(candidate)
        if len(tokens) >= limit:
            break

    return tokens


def _select_example_schema(registry: SchemaRegistry) -> Optional[PredicateSchema]:
    """Choose a predicate schema to showcase in the extraction example."""

    # Prefer scenario predicates (introduced via heading fallback)
    for schema in registry.predicates.values():
        if "scenario" in schema.name.lower():
            return schema

    # Otherwise prefer the highest-arity predicate; fall back to first entry.
    sorted_schemas = sorted(
        registry.predicates.values(), key=lambda schema: schema.arity, reverse=True
    )
    if sorted_schemas:
        return sorted_schemas[0]
    return None


def build_extraction_prompt(
    chunk: str,
    registry: SchemaRegistry,
    *,
    candidate_tokens: Sequence[str] | None = None,
) -> str:
    """Prompt instructing the LLM to extract structured facts."""

    instruction = registry.as_instruction()
    tokens_block = ""
    scenario_note = ""
    example_block = ""
    example_schema = _select_example_schema(registry)
    if candidate_tokens:
        formatted = "\n".join(f"- {token}" for token in candidate_tokens[:12])
        tokens_block = (
            "\nConcrete entity tokens detected in the text (use these exact spellings in args):\n"
            f"{formatted}\n"
        )
        if example_schema:
            example_predicate = example_schema.name
            example_arity = max(1, example_schema.arity)
        else:
            example_predicate = "examplePredicate"
            example_arity = 2
        usable_args = list(candidate_tokens[: example_arity])
        if len(usable_args) == example_arity:
            args_literal = ", ".join(f'"{arg}"' for arg in usable_args)
            example_block = f"""
Example (each argument must be copied verbatim from the tokens listed above):
[
  {{
    "predicate": "{example_predicate}",
    "args": [{args_literal}],
    "confidence": 0.92
  }}
]
"""

    if any("scenario" in schema.name.lower() for schema in registry.predicates.values()):
        scenario_note = (
            "\nFor predicates whose names contain 'scenario', emit exactly one JSON object per scenario heading. "
            "Map **Initial actor** to argument #1, **Target asset** to argument #2, and the entire **Control evidence** line to argument #3."
        )

    prompt = f"""
You are a high-precision legal information extraction engine. 
Your goal is to extract structured facts and rules from the provided text into a VALID JSON object.

**CRITICAL**: You MUST use ONLY the predicate names listed in the PREDICATE SCHEMA below. 
Do NOT invent new predicate names. If the schema has "isPartyRole", use "isPartyRole", NOT "clientEntity".

### PREDICATE SCHEMA:
{instruction}

### SOURCE TEXT:
\"\"\"
{chunk}
\"\"\"

### EXTRACTION RULES:
1. **STRICT PREDICATE NAMES**: Use ONLY predicates from the schema above. Copy the exact names.
2. **ENTITY GROUNDING**: Identify real entities (e.g., "CharlieCompany", "DaveService") and map them to the predicates in the schema.
3. **ARITY MATCH**: Every fact MUST have the exact number of arguments specified in the schema.
4. **OUTPUT**: Return ONLY the JSON object.

### ONE-SHOT EXAMPLE:
Text: "The Agreement is between SampleCorp (Client) and GlobalSolutions (Provider)."
Schema: legalParty(entity, role)
JSON:
{{
  "facts": [
    {{"predicate": "legalParty", "args": ["SampleCorp", "Client"], "confidence": 0.99}},
    {{"predicate": "legalParty", "args": ["GlobalSolutions", "Provider"], "confidence": 0.99}}
  ],
  "rules": []
}}

JSON:"""
    return dedent(prompt).strip()


def build_schema_induction_prompt(
    text: str,
    max_predicates: int = 6,
    existing_predicates: list[str] | None = None,
    candidate_tokens: Sequence[str] | None = None,
) -> str:
    """Prompt that asks the LLM to propose predicate schemas from free-form text."""

    if existing_predicates:
        sorted_names = ", ".join(sorted(existing_predicates))
        existing_note = (
            "\n- The current schema already contains the following predicates: "
            f"{sorted_names}. Only propose additional predicate definitions that capture NEW concepts present in the narrative."
        )
    else:
        existing_note = ""

    token_block = ""
    if candidate_tokens:
        formatted = "\n".join(f"- {token}" for token in candidate_tokens[:12])
        token_block = (
            "\nConcrete entities mentioned in the narrative (align argument slots to these tokens when possible):\n"
            f"{formatted}\n"
        )

    prompt = f"""
You are designing predicate schemas for the LIMEN-AI probabilistic logic engine.
Read the narrative below and derive up to {max_predicates} predicate definitions that
would help represent its facts in first-order logic form.

Respond strictly in JSON:
{{
  "predicates": [
    {{
      "name": "camelCasePredicateName",
      "arity": 2,
      "arg_names": ["argOne", "argTwo"],
      "description": "Concise natural-language description"
    }}
  ]
}}

Guidelines:
- Use camelCase predicate names without spaces or punctuation.
- Set the arity equal to the length of arg_names.
- Each arg_names entry must be a descriptive camelCase identifier.
- Only include predicates that are clearly supported by the text.
- Avoid duplicate or overlapping predicates; prefer concise coverage.
- Under no circumstance repeat template placeholders such as "camelCasePredicateName",
  "argOne", "argTwo", or "Concise natural-language description".
- Every predicate must be tied to a concrete concept present in the narrative (e.g., riskCategory,
  mitigationControl, kpiMeasurement).{existing_note}
{token_block}

Bad example (do NOT output):
{{
  "predicates": [
    {{
      "name": "camelCasePredicateName",
      "arity": 2,
      "arg_names": ["argOne", "argTwo"],
      "description": "Concise natural-language description"
    }}
  ]
}}

Good example (structure only, invent actual concepts from the text instead of copying this):
{{
  "predicates": [
    {{
      "name": "legalParty",
      "arity": 2,
      "arg_names": ["entity", "role"],
      "description": "Links an entity to its legal role in the agreement"
    }},
    {{
      "name": "governingRule",
      "arity": 1,
      "arg_names": ["ruleName"],
      "description": "Identifies a rule that governs the context"
    }}
  ]
}}

Narrative:
\"\"\"
{text}
\"\"\"

JSON:
"""
    return dedent(prompt).strip()


def build_query_prompt(
    question: str, registry: SchemaRegistry, known_constants: list[str] | None = None
) -> str:
    """Prompt that translates a user question into predicate calls."""

    instruction = registry.as_instruction()
    constants_block = ""
    constants_instructions = ""
    example_block = ""
    if known_constants:
        formatted = "\n".join(f"- {name}" for name in sorted(known_constants))
        constants_block = f"\nKNOWN CONSTANTS (Only use these EXACT strings as arguments):\n{formatted}\n"
        constants_instructions = (
            "STRICT RULE: Arguments in the 'args' list MUST match one of the KNOWN CONSTANTS listed above. "
            "Do not use descriptive labels or nested objects. Return ONLY raw strings."
        )

    prompt = f"""
Translate the USER QUESTION into a logical query using the provided PREDICATE SCHEMA.

### PREDICATE SCHEMA:
{instruction}
{constants_block}

### RULES:
1. **JSON ONLY**: Output ONLY a JSON object. No prose. No markdown fences.
2. **ARITY MATTERS**: Match the schema exactly.
3. **USE CONSTANTS**: Use the exact names from the list above.
4. **FALLBACK**: If the question asks about "parties", "who", or "entities", use BOTH "clientEntity" and "providerEntity" predicates, each with 1 argument from the constant list.

### EXAMPLE MAPPING:
Question: "Who is involved?"
JSON: {{"queries": [{{"predicate": "clientEntity", "args": ["CharlieCompany"]}}, {{"predicate": "providerEntity", "args": ["DaveService"]}}]}}

USER QUESTION: "{question}"

JSON:"""
    return dedent(prompt).strip()


def build_response_prompt(structured_answer: str, user_question: str) -> str:
    """Prompt instructing the LLM to turn structured data into natural language."""

    prompt = f"""
Summarize the logical result into 1 sentence. 
STRICT RULE: Do not say "Summary of Logical Result". 
STRICT RULE: Do not explain why information is missing.
STRICT RULE: Do not mention HR, Managers, or Departments.
If a degree is 0.0, say "The fact is not supported."

### RESULT:
{structured_answer}

### QUESTION:
"{user_question}"

RESPONSE:"""
    return dedent(prompt).strip()

