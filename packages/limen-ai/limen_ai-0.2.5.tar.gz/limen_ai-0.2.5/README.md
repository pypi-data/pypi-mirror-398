# LIMEN-AI

LIMEN-AI (Łukasiewicz Interpretable Markov Engine for Neuralized AI) is a Python reference implementation of the LIMEN-AI SRM engine. It provides:

- Łukasiewicz fuzzy semantics and differentiable rule evaluation
- Energy-based inference (importance sampling, explanations, deduction)
- KB-driven inductive rule discovery using configurable templates

## Installation

```bash
cd code
pip install -e .
```

## Documentation

- `docs/api_overview.md` describes the main APIs and workflow.
- `notebooks/limen_ai_walkthrough.ipynb` demonstrates KB creation, inference, and induction.
- `notebooks/limen_llm_orchestration.ipynb` shows how to pair an LLM with the new ingestion/query/response helpers.

## LLM-Oriented Pipelines

The `limen.pipeline` package now provides building blocks for production-grade integrations:

- `SchemaRegistry` / `PredicateSchema` – declare the KB schema so prompts stay aligned with predicate arities.
- `DocumentIngestionPipeline` – chunk/normalize text, call an LLM with the extraction prompt, parse JSON facts, validate arguments, and upsert them into the KB.
- `QueryTranslator` – translate arbitrary user questions into structured predicate calls with schema validation/backoff.
- `ResponseGenerator` – turn LIMEN-AI's structured answers/explanations back into natural language (optionally via an LLM).

These helpers are LLM-agnostic: plug any open-source model by providing a callable completion function or a custom `LLMClient`.

