"""Core package for the LIMEN-AI reference implementation."""

__version__ = "0.2.5"

from .core import Constant, Predicate, Atom, FormulaNode, WeightedFormula, KnowledgeBase, TruthAssignment, Operator, InducedClause
from .semantics import (
    lukasiewicz_and,
    lukasiewicz_or,
    lukasiewicz_not,
    lukasiewicz_implication,
    evaluate_formula,
)
from .storage import load_knowledge_base, save_knowledge_base
from .truth_functions import ConstantTruthFunction, LinearFeatureTruthFunction, differentiable_truth_function
from .config import (
    load_kb_from_config,
    validate_config,
    ValidationIssue,
    register_truth_function_factory,
    available_truth_function_types,
)
from .grounding import (
    GroundingPlan,
    assignment_from_observations,
    auto_ground,
    generate_ground_atoms,
)
from .explanations import RuleExplanation, summarize_rule_contributions, format_explanations
from .training import TorchFormulaEvaluator, TruthFunctionTrainer
from .inference import ImportanceSampler, PowerSampler, LangevinSampler, TorchEnergyWrapper
from .sampling import (
    make_score_guided_proposal,
    make_tempered_proposal,
    make_uniform_proposal,
    make_mixture_proposal,
    rule_activation_trace,
)
from .deduction import GeneratedAtom, generate_atoms
from .printing import format_kb
from .induction import (
    LabelSet,
    InductionConfig,
    ChainTemplate,
    SimpleImplicationTemplate,
    run_induction_and_update_kb,
)
from .pipeline import (
    PredicateSchema,
    SchemaRegistry,
    LLMClient,
    MockLLMClient,
    DocumentIngestionPipeline,
    IngestionResult,
    QueryTranslator,
    StructuredQuery,
    ResponseGenerator,
    StructuredAnswer,
)
from .orchestrator import (
    DEFAULT_ISO_TEXT,
    LimenPipeline,
    LimenClient,
    KnowledgeProposal,
    PipelineCallbacks,
    load_llm,
)

__all__ = [
    "Constant",
    "Predicate",
    "Atom",
    "FormulaNode",
    "WeightedFormula",
    "KnowledgeBase",
    "TruthAssignment",
    "Operator",
    "InducedClause",
    "lukasiewicz_and",
    "lukasiewicz_or",
    "lukasiewicz_not",
    "lukasiewicz_implication",
    "evaluate_formula",
    "save_knowledge_base",
    "load_knowledge_base",
    "load_kb_from_config",
    "validate_config",
    "ValidationIssue",
    "register_truth_function_factory",
    "available_truth_function_types",
    "GroundingPlan",
    "generate_ground_atoms",
    "auto_ground",
    "assignment_from_observations",
    "RuleExplanation",
    "summarize_rule_contributions",
    "format_explanations",
    "ConstantTruthFunction",
    "LinearFeatureTruthFunction",
    "differentiable_truth_function",
    "TorchFormulaEvaluator",
    "TruthFunctionTrainer",
    "ImportanceSampler",
    "PowerSampler",
    "LangevinSampler",
    "TorchEnergyWrapper",
    "GeneratedAtom",
    "generate_atoms",
    "format_kb",
    "LabelSet",
    "InductionConfig",
    "ChainTemplate",
    "SimpleImplicationTemplate",
    "run_induction_and_update_kb",
    "PredicateSchema",
    "SchemaRegistry",
    "LLMClient",
    "MockLLMClient",
    "DocumentIngestionPipeline",
    "IngestionResult",
    "QueryTranslator",
    "StructuredQuery",
    "ResponseGenerator",
    "StructuredAnswer",
    "make_uniform_proposal",
    "make_tempered_proposal",
    "make_score_guided_proposal",
    "make_mixture_proposal",
    "rule_activation_trace",
    "DEFAULT_ISO_TEXT",
    "LimenPipeline",
    "LimenClient",
    "KnowledgeProposal",
    "PipelineCallbacks",
    "load_llm",
]
