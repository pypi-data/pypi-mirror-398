"""High-level orchestration utilities for LIMEN-AI + LLM workflows."""

from __future__ import annotations

import asyncio
import json
import re
import difflib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, List, Optional, Sequence, Tuple

import torch

from .core import Atom, Constant, KnowledgeBase, TruthAssignment, WeightedFormula, Operator, FormulaNode
from .pipeline.llm_client import LLMClient, MockLLMClient
from .pipeline.schema import PredicateSchema, SchemaRegistry
from .pipeline.ingestion import DocumentIngestionPipeline, ParsedFact, IngestionResult
from .pipeline.query import QueryTranslator
from .pipeline.prompts import (
    build_extraction_prompt,
    build_query_prompt,
    build_response_prompt,
    build_schema_induction_prompt,
    extract_candidate_tokens,
)
from .pipeline.response import ResponseGenerator
from .inference import ImportanceSampler
from .sampling import make_score_guided_proposal
from .induction import run_induction_and_update_kb, ChainTemplate, SimpleImplicationTemplate
from .deduction import generate_atoms

@dataclass
class KnowledgeProposal:
    """Holds proposed schema changes and facts for human verification."""
    new_predicates: List[PredicateSchema] = field(default_factory=list)
    new_facts: List[ParsedFact] = field(default_factory=list)
    new_rules: List[dict] = field(default_factory=list) # [{antecedent: list, consequent: dict, weight: float}]
    source_context: str = ""

    def to_markdown(self) -> str:
        """Step 5: Visual-First Markdown representation for Human Verification."""
        lines = ["# Knowledge Proposal for Expert Review", ""]
        
        if self.new_predicates:
            lines.append("## 1. Schema Extensions (New Predicates)")
            for p in self.new_predicates:
                lines.append(f"- **{p.name}**({', '.join(p.arg_names)}): {p.description}")
            lines.append("")

        if self.new_facts:
            lines.append("## 2. Fact Grounding (Extracted from Context)")
            lines.append("| Predicate | Arguments | Confidence | Source |")
            lines.append("| :--- | :--- | :--- | :--- |")
            for f in self.new_facts:
                lines.append(f"| {f.predicate} | {', '.join(f.args)} | {f.confidence:.2f} | `{f.provenance or 'N/A'}` |")
            lines.append("")

        if self.new_rules:
            lines.append("## 3. Logical Rules (Inferred IF/THEN)")
            for r in self.new_rules:
                ant = " AND ".join([f"{a['predicate']}({', '.join(a['args'])})" for a in r['antecedent']])
                con = f"{r['consequent']['predicate']}({', '.join(r['consequent']['args'])})"
                lines.append(f"- **IF** {ant} **THEN** {con} (Weight: {r.get('weight', 1.0)})")
            lines.append("")

        if not self.new_predicates and not self.new_facts and not self.new_rules:
            lines.append("No new knowledge identified in this context.")

        return "\n".join(lines)

PLACEHOLDER_PREDICATE_NAMES = {"camelcasepredicatename"}
PLACEHOLDER_DESCRIPTIONS = {"concise natural-language description"}
PLACEHOLDER_ARG_NAMES = {
    "argone",
    "argtwo",
    "argthree",
    "argfour",
    "argfive",
    "arg1",
    "arg2",
    "arg3",
    "arg4",
    "arg5",
}

DEFAULT_ISO_TEXT = """
# Risk, Threats, Countermeasures and KPIs under ISO/IEC 27001:2022
A Discursive Overview
In an information security management system (ISMS) developed in accordance with ISO/IEC 27001:2022, the assessment of risks and the identification of threats represent the foundation for selecting appropriate controls and for establishing a measurable framework to monitor their effectiveness over time. The standard does not mandate a particular methodology; rather, it requires that the approach be consistent, repeatable, and based on clearly documented criteria. Within this context, risks emerge whenever the confidentiality, integrity or availability of information might be compromised, either by malicious attacks, operational faults, or human error.
One of the most common risks concerns unauthorized access to information. This may arise from credential theft through phishing campaigns, automated brute-force attacks, or privilege escalation attempts. ISO/IEC 27001 emphasises the need for structured identity and access management, enforcing principles such as least privilege and role segregation, combined with multi-factor authentication and the continuous monitoring of anomalous login patterns. Organisations typically measure the effectiveness of these measures by monitoring the rate of failed logins before account lockout, the percentage of accounts protected by multi-factor authentication, or the average time required to revoke the credentials of departing users. A practical example is the compromise of an employee’s password via a fake login page; if multi-factor authentication is correctly implemented, the stolen password alone becomes insufficient for attackers to access internal systems, effectively reducing the residual risk.
Another critical category of risk relates to the loss or unavailability of data. Hardware failures, ransomware-induced encryption, and accidental deletions can all affect business continuity. ISO/IEC 27001 addresses these concerns through mandatory backup processes, regular recovery testing, and the design of resilient architectures capable of supporting continuity requirements. Organisations typically evaluate the reliability of these countermeasures by measuring the success rate of scheduled backups, the proportion of restore tests that complete without errors, and the extent to which actual recovery times align with the defined Recovery Time Objectives (RTO). A typical situation involves the failure of a production storage device: prompt restoration from the latest consistent backup, combined with efficient detection of the fault, limits service disruption and demonstrates operational resilience.
Integrity risks also play a central role in the ISO framework. Data may be altered by attackers, corrupted through supply-chain compromises, or inadvertently modified during system maintenance. To mitigate these threats, ISO/IEC 27001 prescribes the implementation of integrity controls, such as cryptographic validation, secure configuration management, and the definition of formal requirements for software suppliers. The effectiveness of these measures is often assessed by monitoring the number of unauthorised configuration changes, the extent to which CI/CD pipelines integrate integrity verification mechanisms, and the average detection time for unauthorised alterations. A concrete illustration comes from modern software supply-chain attacks, where tampered third-party libraries may introduce malicious code. The presence of code-signing validation in the development pipeline prevents such components from being deployed into production environments.
Human error constitutes another significant source of security incidents and is explicitly addressed by the ISO standard. Misaddressed emails containing sensitive information, public exposure of cloud storage buckets, and the improper use of unapproved sharing tools are all common examples. Training and awareness programmes, clear acceptable-use policies, and technical measures such as Data Loss Prevention (DLP) tools are essential to reduce this risk. Organisations often track completion rates of mandatory training, the frequency of incidents related to accidental disclosures, and the number of DLP interventions over a given period. An illustrative case is the accidental forwarding of a document containing personal data to an external recipient; a properly configured DLP system would detect the presence of regulated data and prevent the transmission, thereby avoiding a potential data breach.
Finally, the ISO/IEC 27001 framework addresses targeted cyberattacks against networked systems. Vulnerability exploitation attempts, man-in-the-middle attacks on unencrypted connections, and distributed denial-of-service activities all threaten system availability and integrity. ISO controls advocate the use of network segmentation, secure communication protocols, and continuous security monitoring, often supported by SIEM and threat-intelligence capabilities. Organisations measure the effectiveness of these measures through indicators such as the number of overdue critical vulnerabilities, the proportion of encrypted network traffic, or the mean time to respond to detected incidents. An example frequently encountered in practice is a DDoS attack targeting a publicly exposed API: a web application firewall equipped with automatic mitigation capabilities can preserve service availability, while correlated event logs enable a rapid and coordinated incident-response effort.
In summary, compliance with ISO/IEC 27001 is not merely a matter of implementing a checklist of technical controls. It requires a systematic and measurable management process that aligns risk assessment, control selection, and continuous improvement within a coherent governance structure. The definition of meaningful KPIs is essential, as it enables organisations to evaluate the real effectiveness of their security measures, to identify emerging weaknesses, and to support strategic decisions based on empirical evidence rather than assumptions.
""".strip()


@dataclass
class PipelineCallbacks:
    on_schema_prompt: Optional[Callable[[str, str], None]] = None
    on_schema_completion: Optional[Callable[[str, str], None]] = None
    on_extraction_prompt: Optional[Callable[[str, str], None]] = None
    on_extraction_completion: Optional[Callable[[str, str], None]] = None
    on_parsed_facts: Optional[Callable[[str, list], None]] = None
    on_validated_facts: Optional[Callable[[str, List[dict]], None]] = None
    on_question_prompt: Optional[Callable[[str, str], None]] = None
    on_question_completion: Optional[Callable[[str, str], None]] = None
    on_answers: Optional[Callable[[str, list], None]] = None
    on_response: Optional[Callable[[str, str], None]] = None
    on_error: Optional[Callable[[str, Exception], None]] = None


def _camel_case(tokens: Iterable[str], fallback: str) -> str:
    cleaned = [token for token in (token.strip() for token in tokens) if token]
    if not cleaned:
        cleaned = [fallback]
    # Ensure all parts are processed: first part lowercase, others capitalized
    parts = []
    for i, token in enumerate(cleaned):
        if i == 0:
            parts.append(token.lower())
        else:
            parts.append(token.capitalize())
    return "".join(parts)


def _normalize_predicate_name(name: str, fallback_idx: int) -> str:
    # Split by non-alphanumeric OR by camelCase/PascalCase boundaries
    # This splits "ContractType" into ["Contract", "Type"]
    tokens = re.findall(r"[A-Z]?[a-z0-9]+|[A-Z]+(?=[A-Z][a-z0-9]|\b)", name)
    if not tokens:
        tokens = re.findall(r"[A-Za-z0-9]+", name)
    return _camel_case(tokens, f"predicate{fallback_idx}")[:64]


def _normalize_arg_names(arg_names: List[str], arity: int) -> List[str]:
    if not arg_names:
        arg_names = [f"arg{i+1}" for i in range(arity)]
    
    normalized = []
    for i, name in enumerate(arg_names):
        tokens = re.findall(r"[A-Z]?[a-z0-9]+|[A-Z]+(?=[A-Z][a-z0-9]|\b)", name)
        if not tokens:
            tokens = re.findall(r"[A-Za-z0-9]+", name)
        normalized.append(_camel_case(tokens, f"arg{i+1}")[:64])
    return normalized


def _extract_json_payload(text: str) -> str:
    """Extracts the longest balanced JSON block from a string."""
    text = text.strip()
    
    # Find all potential start indices for { or [
    starts = [i for i, ch in enumerate(text) if ch in "{["]
    if not starts:
        return text
        
    best_block = ""
    
    for start_idx in starts:
        stack = []
        in_string = False
        escape = False
        
        for idx in range(start_idx, len(text)):
            ch = text[idx]
            
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
                
            if ch in "{[":
                stack.append(ch)
            elif ch in "}]":
                if not stack:
                    break
                opener = stack.pop()
                if (opener == "{" and ch != "}") or (opener == "[" and ch != "]"):
                    break
                
                if not stack:
                    # Found a balanced block
                    block = text[start_idx : idx + 1]
                    if len(block) > len(best_block):
                        best_block = block
                    break
                    
    return best_block or text


def parse_schema_completion(completion: str, max_predicates: int) -> List[PredicateSchema]:
    payload = _extract_json_payload(completion.strip())
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return []
    if isinstance(data, dict) and "predicates" in data:
        entries = data["predicates"]
    elif isinstance(data, list):
        entries = data
    else:
        return []

    schemas: List[PredicateSchema] = []
    for idx, item in enumerate(entries[:max_predicates]):
        original_name = str(item.get("name", "")).strip()
        original_desc = str(item.get("description", "")).strip()
        arg_names_raw = item.get("arg_names") or []
        placeholder_args = [
            isinstance(arg, str) and arg.strip().lower() in PLACEHOLDER_ARG_NAMES
            for arg in arg_names_raw
        ]
        if (
            original_name.lower() in PLACEHOLDER_PREDICATE_NAMES
            or original_desc.lower() in PLACEHOLDER_DESCRIPTIONS
            or (placeholder_args and all(placeholder_args))
        ):
            continue

        name = _normalize_predicate_name(original_name, idx)
        arity = int(item.get("arity", len(arg_names_raw)))
        arg_names = _normalize_arg_names(list(arg_names_raw), arity)
        description = original_desc or f"Predicate inferred from narrative (entry {idx+1})"
        schema = PredicateSchema(
            name=name,
            arity=len(arg_names),
            arg_names=tuple(arg_names),
            description=description,
        )
        schemas.append(schema)
    return schemas


def parse_query_completion(completion: str) -> List[tuple[str, tuple[str, ...]]]:
    payload = _extract_json_payload(completion.strip())
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return []
    if isinstance(data, dict) and "queries" in data:
        entries = data["queries"]
    elif isinstance(data, list):
        entries = data
    else:
        return []

    queries: List[tuple[str, tuple[str, ...]]] = []
    for item in entries:
        predicate_raw = str(item.get("predicate", "")).strip()
        if not predicate_raw:
            continue
        predicate = re.split(r"[\s(]", predicate_raw, 1)[0]
        if not predicate:
            continue
        normalized_predicate = _normalize_predicate_name(predicate, 0)
        args = item.get("args", []) or []
        queries.append((normalized_predicate, tuple(str(arg).strip() for arg in args)))
    return queries


def _args_in_text(args: tuple[str, ...], text_lower: str) -> bool:
    for arg in args:
        token = arg.strip().lower()
        if not token or token not in text_lower:
            return False
    return True


def _atoms_for_predicate(assignment: TruthAssignment, predicate_name: str) -> List[tuple[tuple[str, ...], float]]:
    tuples: List[tuple[tuple[str, ...], float]] = []
    for atom, value in assignment.values.items():
        if atom.predicate.name != predicate_name:
            continue
        arg_names = tuple(constant.name for constant in atom.arguments)
        tuples.append((arg_names, value))
    return tuples


def _heuristic_queries_from_question(
    question: str,
    schema_registry: SchemaRegistry,
    assignment: TruthAssignment,
) -> List[tuple[str, tuple[str, ...]]]:
    q = (question or "").lower()
    scenario_schemas = [
        schema for schema in schema_registry.predicates.values() if "scenario" in schema.name.lower()
    ]
    selected: List[PredicateSchema] = []
    for schema in scenario_schemas:
        description_tokens = re.split(r"[^a-z0-9]+", schema.description.lower())
        name_tokens = re.split(r"[^a-z0-9]+", schema.name.lower())
        tokens = {tok for tok in description_tokens + name_tokens if tok and tok not in {"scenario"}}
        if any(tok in q for tok in tokens):
            selected.append(schema)
    if not selected and scenario_schemas and any(
        keyword in q for keyword in ("scenario", "critical", "incident", "attack")
    ):
        selected = scenario_schemas

    queries: List[tuple[str, tuple[str, ...]]] = []
    seen_keys: set[tuple[str, tuple[str, ...]]] = set()

    for schema in selected:
        for args, _ in _atoms_for_predicate(assignment, schema.name):
            if len(args) != schema.arity:
                continue
            key = (schema.name, args)
            if key in seen_keys:
                continue
            queries.append(key)
            seen_keys.add(key)
    return queries


def derive_schema_from_headings(
    text: str, schema_registry: SchemaRegistry, *, fallback_description_prefix: str = "Scenario"
) -> List[PredicateSchema]:
    heading_re = re.compile(r"^##\s+(.*)$", re.MULTILINE)
    headings = heading_re.findall(text)
    new_entries: List[PredicateSchema] = []
    for idx, heading in enumerate(headings):
        cleaned_heading = re.sub(r"^\s*\d+[\).:\s-]*", "", heading).strip()
        base_name = _normalize_predicate_name(cleaned_heading or heading, idx + 100)
        if base_name in schema_registry.predicates:
            continue
        schema = PredicateSchema(
            name=base_name,
            arity=3,
            arg_names=("initialActor", "targetAsset", "controlEvidence"),
            description=f"{fallback_description_prefix}: {cleaned_heading or heading.strip()}",
        )
        schema_registry.register(schema)
        new_entries.append(schema)
    return new_entries


def _init_llm_client(
    model_name: str,
    *,
    temperature: float,
    top_p: float,
    max_new_tokens: int,
    repetition_penalty: float,
    force_cpu: bool,
    trust_remote_code: bool = True,
) -> tuple[LLMClient, torch.dtype]:
    try:
        from transformers import pipeline
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "Install transformers, accelerate, and sentencepiece to run the LLM-driven demo."
        ) from exc

    use_gpu = torch.cuda.is_available() and not force_cpu
    dtype = torch.float16 if use_gpu else torch.float32
    pipeline_kwargs = {
        "model": model_name,
        "tokenizer": model_name,
        "dtype": dtype,
        "trust_remote_code": trust_remote_code,
    }
    if use_gpu:
        pipeline_kwargs["device_map"] = "auto"
    else:
        pipeline_kwargs["device"] = -1

    text_generator = pipeline("text-generation", **pipeline_kwargs)
    tokenizer = text_generator.tokenizer
    generation_kwargs = {
        "max_new_tokens": max_new_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "do_sample": temperature > 0.0,
        "repetition_penalty": repetition_penalty,
    }
    llm_client = LLMClient.from_hf_pipeline(
        text_generator=text_generator,
        tokenizer=tokenizer,
        generation_kwargs=generation_kwargs,
    )
    return llm_client, dtype


def load_llm(
    model_name: str,
    *,
    temperature: float = 0.0,
    top_p: float = 0.9,
    max_new_tokens: int = 384,
    repetition_penalty: float = 1.05,
    force_cpu: bool = False,
    trust_remote_code: bool = True,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> LLMClient:
    """Loads an LLM client, supporting local HF models or remote APIs."""
    from .pipeline.llm_client import OpenAIClient, GeminiClient
    
    # 1. Check for API-based models
    if model_name.startswith("openai/"):
        return OpenAIClient(
            model_name=model_name[7:],
            api_key=api_key,
            base_url=base_url or "https://api.openai.com/v1",
            temperature=temperature,
            max_new_tokens=max_new_tokens
        )
    elif model_name.startswith("deepseek/"):
        return OpenAIClient(
            model_name=model_name[9:],
            api_key=api_key or os.getenv("DEEPSEEK_API_KEY"),
            base_url=base_url or "https://api.deepseek.com",
            temperature=temperature,
            max_new_tokens=max_new_tokens
        )
    elif model_name.startswith("gemini/"):
        return GeminiClient(
            model_name=model_name[7:],
            api_key=api_key,
            temperature=temperature,
            max_new_tokens=max_new_tokens
        )
    elif model_name.startswith("ollama/"):
        return OpenAIClient(
            model_name=model_name[7:],
            base_url=base_url or "http://localhost:11434/v1",
            api_key="ollama", # placeholder
            temperature=temperature,
            max_new_tokens=max_new_tokens
        )

    # 2. Fallback to local HuggingFace pipeline
    llm_client, _ = _init_llm_client(
        model_name,
        temperature=temperature,
        top_p=top_p,
        max_new_tokens=max_new_tokens,
        repetition_penalty=repetition_penalty,
        force_cpu=force_cpu,
        trust_remote_code=trust_remote_code,
    )
    return llm_client


@dataclass
class StructuredAnswer:
    question: str
    answers: List[dict]
    natural_language: str
    logical_trace: Optional[List[str]] = None


class LimenPipeline:
    """Reusable orchestration pipeline for LIMEN-AI + LLM integration."""

    def __init__(
        self,
        llm_client: LLMClient,
        *,
        chunk_size: int = 400,
        overlap: int = 60,
        min_confidence: float = 0.5,
        max_predicates: int = 6,
        disallowed_constants: Optional[Iterable[str]] = None,
    ) -> None:
        self.llm_client = llm_client
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.min_confidence = min_confidence
        self.max_predicates = max_predicates
        self.disallowed_constants = {
            value.strip().lower()
            for value in (disallowed_constants or [])
            if isinstance(value, str) and value.strip()
        }
        self.schema_registry = SchemaRegistry()
        self.kb = KnowledgeBase()
        self.assignment = TruthAssignment()
        self.response_generator = ResponseGenerator()
        self.ingestion_pipeline = DocumentIngestionPipeline(
            self.schema_registry, self.llm_client, chunk_size=chunk_size, overlap=overlap, min_confidence=min_confidence
        )
        self.query_translator = QueryTranslator(self.schema_registry, self.llm_client)

    def propose_knowledge(self, text: str) -> KnowledgeProposal:
        """Extracts knowledge from text without committing it to the KB."""
        proposal = KnowledgeProposal(source_context=text)
        
        # 1. Induce schema changes
        existing_names = list(self.schema_registry.predicates.keys())
        candidate_tokens = extract_candidate_tokens(text, limit=50)
        schema_prompt = build_schema_induction_prompt(
            text,
            max_predicates=self.max_predicates,
            existing_predicates=existing_names,
            candidate_tokens=candidate_tokens,
        )
        schema_completion = self.llm_client.complete(schema_prompt)
        
        # LOGGING FOR AUDITABILITY
        print(f"\n[DEBUG] Schema Induction Raw Output:\n{schema_completion}\n")
        
        schema_entries = parse_schema_completion(schema_completion, self.max_predicates)
        
        for entry in schema_entries:
            if entry.name not in self.schema_registry.predicates:
                proposal.new_predicates.append(entry)
        
        # 2. Extract facts and rules
        temp_registry = SchemaRegistry()
        for name, s in self.schema_registry.predicates.items():
            temp_registry.register(s)
        for s in proposal.new_predicates:
            temp_registry.register(s)
            
        extraction_prompt = build_extraction_prompt(
            text, temp_registry, candidate_tokens=candidate_tokens
        )
        raw_completion = self.llm_client.complete(extraction_prompt)
        
        # LOGGING FOR AUDITABILITY
        print(f"\n[DEBUG] Fact Extraction Raw Output:\n{raw_completion}\n")
        
        # Handle new JSON structure with 'facts' and 'rules'
        payload = self._safe_parse_json(raw_completion)
        
        # Parse Facts
        parsed_facts = self._parse_facts_from_list(payload.get("facts", []), text)
        for fact in parsed_facts:
            ok, msg = temp_registry.validate_fact(fact["predicate"], fact["args"])
            if ok:
                proposal.new_facts.append(
                    ParsedFact(
                        predicate=fact["predicate"],
                        args=fact["args"],
                        confidence=fact["confidence"],
                        provenance=fact["provenance"]
                    )
                )
            else:
                print(f"[DEBUG] Rejected fact: {fact['predicate']}({fact['args']}) - Reason: {msg}")
        
        # Parse Rules
        rules_raw = payload.get("rules", [])
        if isinstance(rules_raw, list):
            for rule in rules_raw:
                if not isinstance(rule, dict) or "consequent" not in rule or "antecedent" not in rule:
                    continue
                
                # Semantic grounding for rules too
                grounded_ant = []
                for ant in rule.get("antecedent", []):
                    if not isinstance(ant, dict) or "predicate" not in ant or "args" not in ant:
                        continue
                    grounded_ant.append({
                        "predicate": ant["predicate"],
                        "args": self._ground_args(ant["args"], candidate_tokens)
                    })
                
                cons = rule.get("consequent", {})
                if not isinstance(cons, dict) or "predicate" not in cons or "args" not in cons:
                    continue
                    
                grounded_cons = {
                    "predicate": cons["predicate"],
                    "args": self._ground_args(cons["args"], candidate_tokens)
                }
                
                proposal.new_rules.append({
                    "antecedent": grounded_ant,
                    "consequent": grounded_cons,
                    "weight": float(rule.get("weight", 1.0))
                })

        return proposal

    def _safe_parse_json(self, completion: str) -> dict:
        payload_str = _extract_json_payload(completion.strip())
        # Basic JSON repair: remove common trailing commas before closing braces/brackets
        payload_str = re.sub(r',\s*([\]}])', r'\1', payload_str)
        try:
            data = json.loads(payload_str)
            return data if isinstance(data, dict) else {"facts": data}
        except json.JSONDecodeError:
            # Try to recover if it's just a list
            try:
                data = json.loads(f"[{payload_str}]" if not payload_str.startswith("[") else payload_str)
                return {"facts": data} if isinstance(data, list) else {"facts": []}
            except:
                return {"facts": [], "rules": []}

    def _parse_facts_from_list(self, data: list, chunk_text: str) -> List[dict]:
        if not isinstance(data, list): return []
        chunk_lower = chunk_text.lower()
        candidate_tokens = extract_candidate_tokens(chunk_text, limit=50)
        facts: List[dict] = []
        for item in data:
            raw_predicate = item.get("predicate")
            if raw_predicate is None: continue
            predicate = re.split(r"[\s(]", str(raw_predicate).strip(), 1)[0]
            normalized_predicate = _normalize_predicate_name(predicate, 0)
            args = item.get("args", [])
            if not normalized_predicate or not isinstance(args, list): continue
            
            # Semantic Grounding
            grounded_args = self._ground_args(args, candidate_tokens)
            
            facts.append({
                "predicate": normalized_predicate,
                "args": grounded_args,
                "confidence": float(item.get("confidence", 1.0)),
                "provenance": item.get("provenance"),
            })
        return facts

    def commit_knowledge(self, proposal: KnowledgeProposal, auto_induce: bool = True) -> IngestionResult:
        """Commits verified knowledge to the KB and triggers induction."""
        result = IngestionResult()
        
        # 1. Register predicates
        for schema in proposal.new_predicates:
            if schema.name not in self.schema_registry.predicates:
                self.schema_registry.register(schema)
                self.schema_registry.ensure_in_kb(schema.name, self.kb)
        
        # 2. Store facts
        for fact in proposal.new_facts:
            self.set_fact(fact.predicate, fact.args, fact.confidence)
            result.facts_added.append(fact)
            
        # 3. Store rules
        for rule in proposal.new_rules:
            try:
                formula = self._build_rule_formula(rule)
                self.kb.add_formula(WeightedFormula(formula, rule["weight"], name=f"rule_{len(self.kb.formulas)}"))
            except (KeyError, ValueError):
                continue

        # 4. Induction
        if auto_induce and result.facts_added:
            self._trigger_induction()
            
        return result

    def _build_rule_formula(self, rule_dict: dict) -> FormulaNode:
        """Constructs a FormulaNode from a rule dictionary."""
        ant_nodes = []
        for ant in rule_dict["antecedent"]:
            pred = self.kb.get_predicate(ant["predicate"])
            consts = tuple(self._ensure_constant(name) for name in ant["args"])
            ant_nodes.append(FormulaNode.atom_node(Atom(pred, consts)))
        
        if len(ant_nodes) > 1:
            antecedent = FormulaNode(operator=Operator.AND, children=tuple(ant_nodes))
        else:
            antecedent = ant_nodes[0]
            
        cons_data = rule_dict["consequent"]
        cons_pred = self.kb.get_predicate(cons_data["predicate"])
        cons_consts = tuple(self._ensure_constant(name) for name in cons_data["args"])
        consequent = FormulaNode.atom_node(Atom(cons_pred, cons_consts))
        
        return FormulaNode(operator=Operator.IMPLIES, children=(antecedent, consequent))

    def _trigger_induction(self):
        """Internal helper to trigger induction based on current facts."""
        labels = {}
        # Simple heuristic: treat facts with high confidence as positive labels for their predicates
        for atom, val in self.assignment.values.items():
            if val > 0.8:
                if atom.predicate.name not in labels:
                    labels[atom.predicate.name] = {"pos": [], "neg": []}
                labels[atom.predicate.name]["pos"].append(tuple(c.name for c in atom.arguments))
        
        if labels:
            run_induction_and_update_kb(
                self.kb,
                labels,
                assignment=self.assignment,
                templates=[ChainTemplate(), SimpleImplicationTemplate()],
                config={"train_steps": 30, "learning_rate": 0.1}
            )

    def update_knowledge_with_feedback(self, feedback_labels: Dict[str, Dict[str, Sequence[Tuple[str, ...]]]]) -> None:
        """Updates the KB based on human feedback labels."""
        run_induction_and_update_kb(
            self.kb,
            feedback_labels,
            assignment=self.assignment,
            templates=[ChainTemplate(), SimpleImplicationTemplate()],
            config={"train_steps": 50, "learning_rate": 0.05}
        )

    def set_fact(self, predicate_name: str, args: Sequence[str], truth_degree: float = 1.0) -> None:
        """Manually sets a fact in the knowledge base."""
        norm_name = _normalize_predicate_name(predicate_name, 0)
        if norm_name not in self.schema_registry.predicates:
            schema = PredicateSchema(
                name=norm_name,
                arity=len(args),
                arg_names=tuple(f"arg{i+1}" for i in range(len(args))),
                description=f"Manually set predicate: {predicate_name}"
            )
            self.schema_registry.register(schema)
        
        predicate_obj = self.schema_registry.ensure_in_kb(norm_name, self.kb)
        constants = tuple(self._ensure_constant(name) for name in args)
        atom = Atom(predicate_obj, constants)
        self.assignment.set(atom, truth_degree)
        
        # Add to KB as a formula so samplers/inference see it
        # We use a high weight to make it a 'strong' fact.
        # We first remove any existing manual fact for this specific atom.
        manual_name = f"manual_{atom}"
        self.kb.formulas = tuple(f for f in self.kb.formulas if f.name != manual_name)

        if truth_degree >= 0.5:
            node = FormulaNode.atom_node(atom)
            weight = 10.0 * truth_degree
        else:
            # If truth degree is low, we encourage its negation
            node = FormulaNode(operator=Operator.NOT, children=(FormulaNode.atom_node(atom),))
            weight = 10.0 * (1.0 - truth_degree)
            
        self.kb.add_formula(WeightedFormula(node, weight, name=manual_name))

    def _ensure_constant(self, name: str) -> Constant:
        if name in self.kb.constants:
            return self.kb.constants[name]
        c = Constant(name)
        self.kb.add_constant(c)
        return c

    # --- state management -------------------------------------------------
    def save_state(self, path: str) -> None:
        state = {
            "schema": [
                {
                    "name": schema.name,
                    "arity": schema.arity,
                    "arg_names": list(schema.arg_names),
                    "description": schema.description,
                }
                for schema in self.schema_registry.predicates.values()
            ],
            "facts": [
                {
                    "predicate": atom.predicate.name,
                    "args": [const.name for const in atom.arguments],
                    "confidence": value,
                }
                for atom, value in self.assignment.values.items()
            ],
        }
        Path(path).write_text(json.dumps(state, indent=2), encoding="utf-8")

    def load_state(self, path: str) -> None:
        state_path = Path(path)
        if not state_path.exists():
            return
        data = json.loads(state_path.read_text(encoding="utf-8"))
        for entry in data.get("schema", []):
            try:
                schema = PredicateSchema(
                    name=entry["name"],
                    arity=int(entry["arity"]),
                    arg_names=tuple(entry.get("arg_names", [])),
                    description=entry.get("description", ""),
                )
            except (KeyError, TypeError, ValueError):
                continue
            if schema.name not in self.schema_registry.predicates:
                self.schema_registry.register(schema)

        for fact in data.get("facts", []):
            predicate_name = fact.get("predicate")
            args = fact.get("args", [])
            if not predicate_name or not isinstance(args, list):
                continue
            confidence = float(fact.get("confidence", 1.0))
            try:
                predicate = self.schema_registry.ensure_in_kb(predicate_name, self.kb)
            except KeyError:
                continue
            constants = tuple(self._ensure_constant(name) for name in args)
            atom = Atom(predicate, constants)
            self.assignment.set(atom, confidence)

    # --- ingestion --------------------------------------------------------

    async def ingest_blocks_async(
        self,
        blocks: Sequence[tuple[str, str]],
        *,
        callbacks: Optional[PipelineCallbacks] = None,
    ) -> None:
        for label, text in blocks:
            await asyncio.to_thread(self._ingest_block, label, text, callbacks)

    def ingest_block(self, label: str, text: str, callbacks: Optional[PipelineCallbacks] = None) -> None:
        self._ingest_block(label, text, callbacks)

    def ingest_blocks(self, blocks: Sequence[tuple[str, str]], callbacks: Optional[PipelineCallbacks] = None) -> None:
        for label, text in blocks:
            self._ingest_block(label, text, callbacks)

    def _induce_schema_for_block(
        self,
        *,
        text: str,
        label: str,
        callbacks: Optional[PipelineCallbacks],
    ) -> None:
        existing_names = list(self.schema_registry.predicates.keys())
        candidate_tokens = extract_candidate_tokens(text)
        schema_prompt = build_schema_induction_prompt(
            text,
            max_predicates=self.max_predicates,
            existing_predicates=existing_names,
            candidate_tokens=candidate_tokens,
        )
        if callbacks and callbacks.on_schema_prompt:
            callbacks.on_schema_prompt(label, schema_prompt)
        schema_completion = self.llm_client.complete(schema_prompt)
        if callbacks and callbacks.on_schema_completion:
            callbacks.on_schema_completion(label, schema_completion)

        schema_entries = parse_schema_completion(schema_completion, self.max_predicates)
        if not schema_entries:
            derive_schema_from_headings(text, self.schema_registry)
            return
        new_entries: List[PredicateSchema] = []
        for entry in schema_entries:
            if entry.name in self.schema_registry.predicates:
                continue
            self.schema_registry.register(entry)
            new_entries.append(entry)
        if not new_entries:
            derive_schema_from_headings(text, self.schema_registry)

    def _ingest_block(
        self,
        label: str,
        text: str,
        callbacks: Optional[PipelineCallbacks],
    ) -> None:
        try:
            self._induce_schema_for_block(text=text, label=label, callbacks=callbacks)
            candidate_tokens = extract_candidate_tokens(text)
            extraction_prompt = build_extraction_prompt(
                text, self.schema_registry, candidate_tokens=candidate_tokens
            )
            if callbacks and callbacks.on_extraction_prompt:
                callbacks.on_extraction_prompt(label, extraction_prompt)
            raw_completion = self.llm_client.complete(extraction_prompt)
            if callbacks and callbacks.on_extraction_completion:
                callbacks.on_extraction_completion(label, raw_completion)

            parsed_facts = self._parse_facts(raw_completion, text)
            if callbacks and callbacks.on_parsed_facts:
                callbacks.on_parsed_facts(label, parsed_facts)

            accepted = self._validate_and_store_facts(parsed_facts, text)
            if callbacks and callbacks.on_validated_facts:
                callbacks.on_validated_facts(label, accepted)
        except Exception as exc:  # pragma: no cover - tracing for callers
            if callbacks and callbacks.on_error:
                callbacks.on_error(label, exc)
            else:
                raise

    def _parse_facts(self, completion: str, chunk_text: str) -> List[dict]:
        completion = completion.strip()
        if not completion:
            return []
        payload = _extract_json_payload(completion)
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return []
        if isinstance(data, dict) and "facts" in data:
            data = data["facts"]
        if not isinstance(data, list):
            return []
        chunk_lower = chunk_text.lower()
        facts: List[dict] = []
        for item in data:
            raw_predicate = item.get("predicate")
            if raw_predicate is None:
                continue
            predicate = re.split(r"[\s(]", str(raw_predicate).strip(), 1)[0]
            normalized_predicate = _normalize_predicate_name(predicate, 0)
            args = item.get("args", [])
            if not normalized_predicate or not isinstance(args, list):
                continue
            normalized_args = tuple(str(arg) for arg in args)
            if not all(str(arg).strip().lower() in chunk_lower for arg in normalized_args):
                continue
            facts.append(
                {
                    "predicate": normalized_predicate,
                    "args": normalized_args,
                    "confidence": float(item.get("confidence", 1.0)),
                    "provenance": item.get("provenance"),
                }
            )
        return facts

    def _validate_and_store_facts(self, parsed_facts: List[dict], text: str) -> List[dict]:
        accepted: List[dict] = []
        chunk_lower = text.lower()
        candidate_tokens = extract_candidate_tokens(text, limit=50)
        
        for fact in parsed_facts:
            predicate = fact["predicate"]
            args = fact["args"]
            confidence = fact["confidence"]
            
            # Semantic Grounding: Map hallucinated entities to real tokens
            grounded_args = self._ground_args(args, candidate_tokens)
            fact["args"] = grounded_args # Update fact with grounded args
            args = grounded_args
            
            ok, message = self.schema_registry.validate_fact(predicate, args)
            if not ok:
                continue
            schema = self.schema_registry.get(predicate)
            if schema and all(
                arg.strip().lower() == placeholder.strip().lower()
                for arg, placeholder in zip(args, schema.arg_names)
            ):
                continue
            if not _args_in_text(args, chunk_lower):
                continue
            if confidence < self.min_confidence:
                continue
            if self.disallowed_constants and any(
                arg.strip().lower() in self.disallowed_constants for arg in args
            ):
                continue

            predicate_obj = self.schema_registry.ensure_in_kb(predicate, self.kb)
            constants = tuple(self._ensure_constant(name) for name in args)
            atom = Atom(predicate_obj, constants)
            self.assignment.set(atom, confidence)
            accepted.append(fact)
        return accepted

    def _ground_args(self, args: Sequence[Any], candidates: List[str]) -> Tuple[str, ...]:
        """Maps extracted arguments to the closest candidate tokens in the context."""
        if not candidates:
            return tuple(str(arg) for arg in args)
            
        grounded = []
        for arg in args:
            # Ensure arg is a string for comparison and difflib
            arg_str = str(arg)
            
            # If the arg is already a candidate, use it verbatim
            if arg_str in candidates:
                grounded.append(arg_str)
                continue
            
            # Fuzzy match against candidates
            matches = difflib.get_close_matches(arg_str, candidates, n=1, cutoff=0.6)
            if matches:
                grounded.append(matches[0])
            else:
                grounded.append(arg_str) # Fallback to original if no good match
        return tuple(grounded)

    # --- questioning ------------------------------------------------------

    def ask(self, question: str, callbacks: Optional[PipelineCallbacks] = None) -> StructuredAnswer:
        return self._run_question_pipeline(question, callbacks)

    async def ask_async(self, question: str, callbacks: Optional[PipelineCallbacks] = None) -> StructuredAnswer:
        return await asyncio.to_thread(self._run_question_pipeline, question, callbacks)

    def _run_question_pipeline(
        self,
        question: str,
        callbacks: Optional[PipelineCallbacks],
    ) -> StructuredAnswer:
        # Step 9: Translate NL question to structured queries
        known_constants = list(self.kb.constants.keys())
        query_prompt = build_query_prompt(question, self.schema_registry, known_constants)
        if callbacks and callbacks.on_question_prompt:
            callbacks.on_question_prompt(question, query_prompt)
        
        completion = self.llm_client.complete(query_prompt)
        raw_queries = parse_query_completion(completion)
        
        # Semantic Grounding for Queries
        queries = []
        for pred, args in raw_queries:
            grounded_args = self._ground_args(args, known_constants)
            queries.append((pred, grounded_args))

        if callbacks and callbacks.on_question_completion:
            callbacks.on_question_completion(question, completion)

        # Step 10: Logical Analysis
        analysis_trace = self._analyze_query_state(queries)
        deduced_assignment, generated = generate_atoms(self.kb, self.assignment, threshold=0.6)
        
        results: List[dict] = []
        logical_trace: List[str] = []
        
        for line in analysis_trace:
            logical_trace.append(f"Analysis: {line}")
            
        if generated:
            for fact in generated:
                logical_trace.append(f"Deduction: {fact.atom} -> {fact.value:.3f} via {fact.rule_name}")

        # Step 11: Logical Inference (Reasoning)
        sampler = ImportanceSampler(self.kb, make_score_guided_proposal(self.kb, reference=self.assignment))
        
        for predicate_name, args in queries:
            if predicate_name not in self.kb.predicates:
                logical_trace.append(f"Inference: Predicate '{predicate_name}' not found in KB.")
                continue
            predicate = self.kb.get_predicate(predicate_name)
            try:
                constants = tuple(self.kb.get_constant(arg) for arg in args)
            except KeyError:
                logical_trace.append(f"Inference: One or more constants in {args} not found in KB.")
                continue
            
            if len(constants) != predicate.arity:
                if len(constants) < predicate.arity:
                    logical_trace.append(f"Inference: Attempting to repair '{predicate_name}' (found {len(constants)}/{predicate.arity} args).")
                    logical_trace.append(f"Inference: Skipping '{predicate_name}' due to incomplete grounding.")
                    continue
                else:
                    logical_trace.append(f"Inference: Skipping '{predicate_name}' due to arity mismatch (too many args).")
                    continue
                
            atom = Atom(predicate, constants)
            
            # Estimate degree via sampling
            expectation, traces, ess = sampler.estimate(lambda ta: ta.get(atom), num_samples=100)
            results.append({"predicate": predicate_name, "args": list(args), "value": expectation})
            logical_trace.append(f"Inference: {atom} degree = {expectation:.4f} (ESS={ess:.2f})")

        if not results:
            heuristic_queries = _heuristic_queries_from_question(question, self.schema_registry, self.assignment)
            for name, args in heuristic_queries:
                predicate = self.kb.get_predicate(name)
                constants = tuple(self.kb.get_constant(arg) for arg in args)
                atom = Atom(predicate, constants)
                expectation, _, _ = sampler.estimate(lambda ta: ta.get(atom), num_samples=64)
                results.append({"predicate": name, "args": list(args), "value": expectation})
                logical_trace.append(f"Inference (Heuristic): {atom} degree = {expectation:.4f}")

        # Step 12: Response Generation (Reverse 4)
        # --- Strict Entity Replacement Layer ---
        # Build a lookup table of all grounded facts to help the LLM use real names instead of roles.
        entity_dictionary = {}
        if "legalParty" in self.kb.predicates:
            for atom, val in self.assignment.values.items():
                if atom.predicate.name == "legalParty" and val > 0.8:
                    # e.g., legalParty(Alpha, Client) -> entity_dictionary["Client"] = "Alpha"
                    if len(atom.arguments) == 2:
                        entity_dictionary[atom.arguments[1].name] = atom.arguments[0].name

        structured_answer_payload = {
            "answers": results, 
            "logical_trace": logical_trace,
            "entity_dictionary": entity_dictionary
        }
        structured_json = json.dumps(structured_answer_payload, indent=2)
        response_prompt = build_response_prompt(structured_json, question)
        response = self.llm_client.complete(response_prompt)

        if callbacks and callbacks.on_answers:
            callbacks.on_answers(question, results)
        if callbacks and callbacks.on_response:
            callbacks.on_response(question, response)

        return StructuredAnswer(
            question=question,
            answers=results,
            natural_language=response,
            logical_trace=logical_trace
        )

    def _analyze_query_state(self, queries: List[tuple[str, tuple[str, ...]]]) -> List[str]:
        """Performs Step 10: Logical Analysis of the query state."""
        trace = []
        if not queries:
            trace.append("No queries derived from natural language prompt.")
            return trace
            
        for pred, args in queries:
            if pred not in self.kb.predicates:
                trace.append(f"Query for unknown predicate '{pred}'.")
            else:
                schema = self.schema_registry.get(pred)
                if schema and len(args) != schema.arity:
                    trace.append(f"Arity mismatch for '{pred}': expected {schema.arity}, got {len(args)}.")
                else:
                    trace.append(f"Query for '{pred}' with args {args} is structurally valid.")
                    
            for arg in args:
                if arg not in self.kb.constants:
                    trace.append(f"Constant '{arg}' not found in current Knowledge Base.")
                    
        return trace


class LimenClient:
    """The 'Classic' entry point for LIMEN-AI library usage (13-Step Pipeline)."""
    
    def __init__(self, model_name: str = "TinyLlama/TinyLlama-1.1B-Chat-v1.0", 
                 temperature: float = 0.7, 
                 max_new_tokens: int = 2048,
                 use_real_llm: bool = True,
                 trust_remote_code: bool = True,
                 repetition_penalty: float = 1.1,
                 api_key: Optional[str] = None,
                 base_url: Optional[str] = None):
        """
        Step 2 & 3: Initialize client and configure LLM variables.
        """
        if use_real_llm:
            self.llm = load_llm(
                model_name, 
                temperature=temperature, 
                max_new_tokens=max_new_tokens,
                trust_remote_code=trust_remote_code,
                repetition_penalty=repetition_penalty,
                api_key=api_key,
                base_url=base_url
            )
        else:
            self.llm = MockLLMClient({})
            
        self.pipeline = LimenPipeline(self.llm)
        
    def extract(self, context: str) -> KnowledgeProposal:
        """
        Step 4: Extract knowledge from context (LLM parses INPUT_CONTEXT).
        The LLM generates PredicateSchema and Facts candidates.
        """
        return self.pipeline.propose_knowledge(context)
    
    def add_knowledge(self, proposal: KnowledgeProposal) -> IngestionResult:
        """
        Step 5 & 6: Human verified knowledge addition & Induction.
        Expert reviews the proposal, then it is committed to the KB.
        """
        return self.pipeline.commit_knowledge(proposal)
    
    def ask(self, question: str) -> StructuredAnswer:
        """
        Step 8-12: Natural language chat interface.
        Performs:
          - Step 9: Query Translation (NL to Logic)
          - Step 10: Logical Analysis (Structural check)
          - Step 11: Logical Inference (Sampling/Reasoning)
          - Step 12: Response Generation (Logic to NL Prose)
        """
        return self.pipeline.ask(question)
    
    def feedback(self, labels: Dict[str, Dict[str, Sequence[Tuple[str, ...]]]]) -> None:
        """
        Step 13: Feedback loop for induction.
        Refines rule weights based on historical labels.
        """
        self.pipeline.update_knowledge_with_feedback(labels)

    def set_fact(self, predicate: str, args: Sequence[str], truth_degree: float = 1.0) -> None:
        """Step 7 & 13: Manually set/update facts in the KB."""
        self.pipeline.set_fact(predicate, args, truth_degree)
        
    def veto(self, predicate: str, args: Sequence[str]) -> None:
        """
        Step 13: Manual Override (The Veto Power).
        Explicitly sets a truth degree to 0.0 (Article 14(4) compliance).
        """
        self.set_fact(predicate, args, 0.0)

    def save_state(self, path: str) -> None:
        """Step 7: Save KB state to a JSON file."""
        self.pipeline.save_state(path)

    def load_state(self, path: str) -> None:
        """Step 7: Load KB state from a JSON file."""
        self.pipeline.load_state(path)

__all__ = [
    "DEFAULT_ISO_TEXT",
    "LimenPipeline",
    "LimenClient",
    "KnowledgeProposal",
    "PipelineCallbacks",
    "StructuredAnswer",
    "parse_schema_completion",
    "parse_query_completion",
    "derive_schema_from_headings",
    "load_llm",
]


