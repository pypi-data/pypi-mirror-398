"""KB-driven inductive rule discovery for LIMEN-AI."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import torch
import torch.nn.functional as F

from .core import Atom, Constant, InducedClause, KnowledgeBase, Predicate


@dataclass
class LabelSet:
    positives: Sequence[Tuple[str, ...]] = field(default_factory=list)
    negatives: Sequence[Tuple[str, ...]] = field(default_factory=list)


@dataclass
class InductionConfig:
    train_steps: int = 150
    learning_rate: float = 0.05
    min_strength: float = 0.55
    min_positive_margin: float = 0.2
    positive_threshold: float = 0.6
    max_clauses_per_head: int = 5
    l1_lambda: float = 1e-3
    device: str = "cpu"


class InductionTemplate:
    name: str = "base_template"

    def instantiate(self, kb: KnowledgeBase, head: Predicate) -> List["TemplateInstance"]:
        raise NotImplementedError


@dataclass
class TemplateInstance:
    template: InductionTemplate
    head: Predicate

    def body_values(self, assignment, example: Tuple[str, ...]) -> float:
        raise NotImplementedError

    @property
    def body_signature(self) -> Tuple[str, ...]:
        raise NotImplementedError


class ChainTemplate(InductionTemplate):
    """Chain rule template: head(A,B) :- rel1(A,C), rel2(C,B)."""

    name = "chain_2"

    def instantiate(self, kb: KnowledgeBase, head: Predicate) -> List["TemplateInstance"]:
        if head.arity != 2:
            return []
        binary_preds = [p for p in kb.predicates.values() if p.arity == 2]
        instances: List[TemplateInstance] = []
        for rel1 in binary_preds:
            for rel2 in binary_preds:
                instances.append(ChainInstance(self, head, rel1, rel2, kb))
        return instances


class SimpleImplicationTemplate(InductionTemplate):
    """Simple implication template: head(A,B) :- body(A,B)."""

    name = "implication_1"

    def instantiate(self, kb: KnowledgeBase, head: Predicate) -> List["TemplateInstance"]:
        if head.arity != 2:
            return []
        binary_preds = [p for p in kb.predicates.values() if p.arity == 2 and p.name != head.name]
        instances: List[TemplateInstance] = []
        for body in binary_preds:
            instances.append(SimpleImplicationInstance(self, head, body, kb))
        return instances


class SimpleImplicationInstance(TemplateInstance):
    def __init__(self, template, head, body, kb: KnowledgeBase) -> None:
        super().__init__(template=template, head=head)
        self.body_pred = body
        self.kb = kb

    def body_values(self, assignment, example: Tuple[str, str]) -> float:
        consts = tuple(self.kb.get_constant(name) for name in example)
        atom = Atom(self.body_pred, consts)
        return assignment.get(atom, 0.0)

    @property
    def body_signature(self) -> Tuple[str, ...]:
        return (self.body_pred.name,)


class ChainInstance(TemplateInstance):
    def __init__(self, template, head, rel1, rel2, kb: KnowledgeBase) -> None:
        super().__init__(template=template, head=head)
        self.rel1 = rel1
        self.rel2 = rel2
        self.kb = kb
        self._constant_names = list(kb.constants.keys())

    def _truth(self, predicate: Predicate, args: Tuple[str, str], assignment) -> float:
        consts = tuple(self.kb.get_constant(name) for name in args)
        atom = Atom(predicate, consts)
        return assignment.get(atom, 0.0)

    def body_values(self, assignment, example: Tuple[str, str]) -> float:
        a, b = example
        best = 0.0
        for mid in self._constant_names:
            val1 = self._truth(self.rel1, (a, mid), assignment)
            val2 = self._truth(self.rel2, (mid, b), assignment)
            combined = max(0.0, val1 + val2 - 1.0)
            if combined > best:
                best = combined
        return best

    @property
    def body_signature(self) -> Tuple[str, ...]:
        return (self.rel1.name, self.rel2.name)


class ClauseLearner(torch.nn.Module):
    def __init__(
        self,
        instance: TemplateInstance,
        assignment,
        labels: LabelSet,
        device: str,
    ) -> None:
        super().__init__()
        self.instance = instance
        self.weight = torch.nn.Parameter(torch.zeros(1, dtype=torch.float32, device=device))
        self.device = device
        self.pos_tensor = self._build_tensor(assignment, labels.positives)
        self.neg_tensor = self._build_tensor(assignment, labels.negatives)

    def _build_tensor(self, assignment, examples: Sequence[Tuple[str, ...]]) -> torch.Tensor:
        if not examples:
            return torch.zeros(0, dtype=torch.float32, device=self.device)
        values = [self.instance.body_values(assignment, example) for example in examples]
        return torch.tensor(values, dtype=torch.float32, device=self.device)

    def forward(self) -> Dict[str, torch.Tensor]:
        strength = torch.sigmoid(self.weight)
        pos_preds = strength * self.pos_tensor if self.pos_tensor.numel() else torch.tensor(0.0, device=self.device)
        neg_preds = strength * self.neg_tensor if self.neg_tensor.numel() else torch.tensor(0.0, device=self.device)

        loss = torch.tensor(0.0, dtype=torch.float32, device=self.device)
        if self.pos_tensor.numel():
            loss = loss + F.mse_loss(pos_preds, torch.ones_like(pos_preds))
        if self.neg_tensor.numel():
            loss = loss + F.mse_loss(neg_preds, torch.zeros_like(neg_preds))
        return {
            "loss": loss,
            "strength": strength,
            "pos_preds": pos_preds,
            "neg_preds": neg_preds,
        }


class InductionEngine:
    def __init__(
        self,
        kb: KnowledgeBase,
        labels: Dict[str, LabelSet],
        assignment,
        templates: Sequence[InductionTemplate],
        config: InductionConfig,
    ) -> None:
        self.kb = kb
        self.labels = labels
        self.assignment = assignment
        self.templates = templates
        self.config = config

    def run(self) -> List[InducedClause]:
        accepted: List[InducedClause] = []
        for head_name, label_set in self.labels.items():
            if not label_set.positives:
                continue
            try:
                head_predicate = self.kb.get_predicate(head_name)
            except KeyError:
                continue
            head_clauses = self._run_for_head(head_predicate, label_set)
            if head_clauses:
                self.kb.replace_induced_clauses(head_name, head_clauses)
                accepted.extend(head_clauses)
        return accepted

    def _run_for_head(self, head: Predicate, label_set: LabelSet) -> List[InducedClause]:
        instances: List[TemplateInstance] = []
        for template in self.templates:
            instances.extend(template.instantiate(self.kb, head))
        ranked: List[Tuple[float, InducedClause]] = []
        for instance in instances:
            learner = ClauseLearner(instance, self.assignment, label_set, self.config.device)
            optimizer = torch.optim.Adam(learner.parameters(), lr=self.config.learning_rate)
            metrics = None
            for _ in range(self.config.train_steps):
                optimizer.zero_grad()  # type: ignore[attr-defined]
                outputs = learner()
                loss = outputs["loss"] + self.config.l1_lambda * torch.abs(torch.sigmoid(learner.weight))
                loss.backward()
                optimizer.step()
                metrics = outputs
            if metrics is None:
                continue
            strength = float(metrics["strength"].detach().cpu())
            pos_score = float(metrics["pos_preds"].mean().detach().cpu()) if learner.pos_tensor.numel() else 0.0
            neg_score = float(metrics["neg_preds"].mean().detach().cpu()) if learner.neg_tensor.numel() else 0.0
            if self._should_accept(strength, pos_score, neg_score):
                clause = InducedClause(
                    head=head.name,
                    body=instance.body_signature,
                    template=instance.template.name,
                    weight=strength,
                    metadata={
                        "pos_score": pos_score,
                        "neg_score": neg_score,
                        "positives": len(label_set.positives),
                        "negatives": len(label_set.negatives),
                    },
                )
                ranked.append((pos_score - neg_score, clause))
        ranked.sort(key=lambda item: item[0], reverse=True)
        return [clause for _, clause in ranked[: self.config.max_clauses_per_head]]

    def _should_accept(self, strength: float, pos_score: float, neg_score: float) -> bool:
        if strength < self.config.min_strength:
            return False
        if pos_score < self.config.positive_threshold:
            return False
        if (pos_score - neg_score) < self.config.min_positive_margin:
            return False
        return True


def _normalise_labels(
    raw_labels: Dict[str, Dict[str, Sequence[Tuple[str, ...]]]] | Dict[str, LabelSet]
) -> Dict[str, LabelSet]:
    normalised: Dict[str, LabelSet] = {}
    for head, payload in raw_labels.items():
        if isinstance(payload, LabelSet):
            normalised[head] = payload
        else:
            normalised[head] = LabelSet(
                positives=tuple(payload.get("pos", ())),
                negatives=tuple(payload.get("neg", ())),
            )
    return normalised


def run_induction_and_update_kb(
    kb: KnowledgeBase,
    label_store: Dict[str, Dict[str, Sequence[Tuple[str, ...]]]] | Dict[str, LabelSet],
    *,
    assignment=None,
    templates: Optional[Sequence[InductionTemplate]] = None,
    config: Optional[Dict[str, float]] = None,
) -> List[InducedClause]:
    if assignment is None:
        assignment = kb.build_assignment_from_truth_functions()
    cfg = InductionConfig(**config) if config else InductionConfig()
    template_list = list(templates) if templates else [ChainTemplate()]
    labels = _normalise_labels(label_store)
    engine = InductionEngine(kb, labels, assignment, template_list, cfg)
    return engine.run()
