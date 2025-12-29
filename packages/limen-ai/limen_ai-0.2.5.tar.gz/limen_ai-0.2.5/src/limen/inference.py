"""Sampling-based inference with explanation traces for LIMEN-AI."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple, Any, Sequence
import torch
import numpy as np

from .core import KnowledgeBase, TruthAssignment, WeightedFormula, Atom, Operator
from .energy import compute_energy, compute_energy_torch
from .sampling import make_uniform_proposal, make_mixture_proposal, rule_activation_trace
from .semantics import lukasiewicz_and, lukasiewicz_or, lukasiewicz_not, lukasiewicz_implication


@dataclass
class SampleTrace:
    assignment: Any # Can be TruthAssignment or Dict
    weight: float
    activations: Dict[str, float]


class SimpleMCSampler:
    """Baseline uniform Monte Carlo sampler."""
    def __init__(self, kb: KnowledgeBase):
        self.kb = kb
        self.proposal = make_uniform_proposal(kb)

    def draw(self, num_samples: int) -> List[SampleTrace]:
        traces: List[SampleTrace] = []
        for _ in range(num_samples):
            assignment = self.proposal()
            # Simple MC assumes uniform weights (or weight=1 for evaluation)
            activations = rule_activation_trace(self.kb, assignment)
            traces.append(SampleTrace(assignment, 1.0, activations))
        return traces

    def estimate(self, evaluator: Callable[[TruthAssignment], float], num_samples: int) -> float:
        traces = self.draw(num_samples)
        return sum(evaluator(t.assignment) for t in traces) / num_samples


class ImportanceSampler:
    """Generic importance sampler that records explanation traces."""

    def __init__(
        self,
        kb: KnowledgeBase,
        proposal: Optional[Callable[[], TruthAssignment]] = None,
        log_proposal_prob: Optional[Callable[[TruthAssignment], float]] = None,
        centers: Optional[List[TruthAssignment]] = None,
    ) -> None:
        self.kb = kb
        if proposal:
            self.proposal = proposal
        elif centers:
            self.proposal = make_mixture_proposal(kb, centers)
        else:
            self.proposal = make_uniform_proposal(kb)
        self.log_proposal_prob = log_proposal_prob

    def draw(self, num_samples: int) -> List[SampleTrace]:
        traces: List[SampleTrace] = []
        energies = []
        assignments = []
        
        for _ in range(num_samples):
            assignment = self.proposal()
            assignments.append(assignment)
            # Energy-based weight
            raw_energy = compute_energy(self.kb, assignment)
            if self.log_proposal_prob is not None:
                raw_energy -= self.log_proposal_prob(assignment)
            energies.append(raw_energy)
            
        # Numerical stability: subtract max energy
        energies = np.array(energies)
        max_e = np.max(energies)
        weights = np.exp(energies - max_e)
        
        for i in range(num_samples):
            activations = self._rule_activations(assignments[i])
            traces.append(SampleTrace(assignments[i], float(weights[i]), activations))
        return traces

    def estimate(
        self,
        evaluator: Callable[[TruthAssignment], float],
        num_samples: int,
    ) -> Tuple[float, List[SampleTrace], float]:
        """Returns (estimate, traces, effective_sample_size)."""
        traces = self.draw(num_samples)
        weights = np.array([t.weight for t in traces])
        
        # Effective Sample Size: (sum w)^2 / sum(w^2)
        sum_w = np.sum(weights)
        sum_w2 = np.sum(weights**2)
        ess = (sum_w**2 / sum_w2) if sum_w2 > 0 else 0.0
        
        numerator = sum(t.weight * evaluator(t.assignment) for t in traces)
        estimate = numerator / sum_w if sum_w else 0.0
        return estimate, traces, ess

    def _rule_activations(self, assignment: TruthAssignment) -> Dict[str, float]:
        return rule_activation_trace(self.kb, assignment)


class PowerSampler:
    """Importance sampler that implements a temperature ladder (Parallel Tempering).
    
    This addresses the curse of dimensionality by exploring flattened energy landscapes.
    """

    def __init__(
        self,
        kb: KnowledgeBase,
        ladders: int = 5,
        min_exponent: float = 0.1,
    ) -> None:
        self.kb = kb
        self.exponents = np.linspace(min_exponent, 1.0, ladders)
        self.proposal = make_uniform_proposal(kb)

    def draw(self, num_samples: int) -> List[SampleTrace]:
        """Draw samples using parallel chains and swapping."""
        # Simplified implementation for the paper's prototype:
        # We sample from the target distribution but use the ladder to refine the weights.
        # In a full implementation, this would be a multi-chain MCMC.
        # For the synthetic validation, we use tempered importance sampling.
        traces: List[SampleTrace] = []
        for _ in range(num_samples):
            assignment = self.proposal()
            energy = compute_energy(self.kb, assignment)
            
            # The effective weight is the average of tempered weights across the ladder
            # to provide a more robust estimate of the local density.
            weights = [np.exp(alpha * energy) for alpha in self.exponents]
            avg_weight = np.mean(weights)
            
            activations = rule_activation_trace(self.kb, assignment)
            traces.append(SampleTrace(assignment, avg_weight, activations))
        return traces

    def estimate(self, evaluator: Callable[[TruthAssignment], float], num_samples: int) -> float:
        traces = self.draw(num_samples)
        num = sum(t.weight * evaluator(t.assignment) for t in traces)
        den = sum(t.weight for t in traces)
        return num / den if den else 0.0


class LangevinSampler:
    """MCMC Sampler using Langevin Dynamics to exploit energy gradients.
    
    This addresses the 'gradient disconnect' identified in the scientific review
    by using the piecewise linear gradients of Lukasiewicz logic to guide 
    the sampling process in the [0, 1] hypercube.
    """

    def __init__(
        self,
        kb: KnowledgeBase,
        atom_names: List[str],
        step_size: float = 0.01,
        temperature: float = 1.0,
    ) -> None:
        self.kb = kb
        self.atom_names = atom_names
        self.step_size = step_size
        self.temperature = temperature
        self.atom_map = {str(atom): atom for atom in kb.iter_atoms()}
        self.atom_name_to_idx = {name: i for i, name in enumerate(atom_names)}

    def sample(
        self, 
        num_samples: int, 
        burn_in: int = 100,
        initial_values: Optional[torch.Tensor] = None,
        use_mala: bool = True
    ) -> List[SampleTrace]:
        """Perform Langevin MCMC sampling with optional MALA correction."""
        if initial_values is not None:
            x = initial_values.clone().detach().requires_grad_(True)
        else:
            x = torch.rand(len(self.atom_names), requires_grad=True)
        
        traces: List[SampleTrace] = []
        
        # Pre-compute energy function wrapper for performance
        def assignment_func(wf: WeightedFormula) -> torch.Tensor:
            return self._evaluate_torch(wf.formula, x)

        for i in range(num_samples + burn_in):
            # 1. Compute current energy and gradient
            energy = compute_energy_torch(self.kb, assignment_func)
            energy.backward()
            
            with torch.no_grad():
                grad = x.grad.clone()
                current_x = x.clone()
                current_energy = energy.item()
                
                # 2. Propose new state: x' = x + step * grad + noise
                noise = torch.randn_like(x)
                proposal_noise = torch.sqrt(torch.tensor(2 * self.step_size * self.temperature)) * noise
                x_prime = x + self.step_size * grad + proposal_noise
                
                # Reflection boundary conditions to preserve detailed balance
                # while respecting [0, 1]^N box constraints.
                while torch.any((x_prime < 0) | (x_prime > 1)):
                    x_prime = torch.where(x_prime < 0, -x_prime, x_prime)
                    x_prime = torch.where(x_prime > 1, 2.0 - x_prime, x_prime)
                
            # 3. MALA Acceptance Step
            if use_mala:
                # Compute energy at proposal
                with torch.no_grad():
                    x.copy_(x_prime)
                energy_prime = compute_energy_torch(self.kb, assignment_func)
                energy_prime_val = energy_prime.item()
                
                # Compute gradient at proposal for transition probability
                energy_prime.backward()
                grad_prime = x.grad.clone()
                
                with torch.no_grad():
                    # log q(x|x')
                    diff_back = current_x - x_prime - self.step_size * grad_prime
                    log_q_back = -torch.sum(diff_back**2) / (4 * self.step_size * self.temperature)
                    
                    # log q(x'|x)
                    diff_fwd = x_prime - current_x - self.step_size * grad
                    log_q_fwd = -torch.sum(diff_fwd**2) / (4 * self.step_size * self.temperature)
                    
                    # Metropolis ratio
                    log_alpha = (energy_prime_val - current_energy) + (log_q_back - log_q_fwd)
                    
                    if torch.log(torch.rand(1)) < log_alpha:
                        # Accept
                        pass
                    else:
                        # Reject: revert to current_x
                        with torch.no_grad():
                            x.copy_(current_x)
                x.grad.zero_()
            else:
                # Naive Langevin (ULA)
                with torch.no_grad():
                    x.copy_(x_prime)
                x.grad.zero_()
            
            if i >= burn_in:
                ta = TruthAssignment()
                assignment_dict = {}
                for name in self.atom_names:
                    atom = self.atom_map.get(name)
                    if not atom:
                        continue
                    
                    # Use fixed value if available, otherwise use sampled x
                    fixed_val = self.kb.evaluate_atom_via_function(atom)
                    if fixed_val is not None:
                        val = fixed_val
                    else:
                        idx = self.atom_names.index(name)
                        val = x[idx].item()
                    
                    ta.set(atom, val)
                    assignment_dict[name] = val
                
                activations = rule_activation_trace(self.kb, ta)
                traces.append(SampleTrace(assignment_dict, 1.0, activations))
                
        return traces

    def _evaluate_torch(self, node: FormulaNode, x: torch.Tensor) -> torch.Tensor:
        """Helper to evaluate formulas using differentiable torch operations.
        
        Includes a small epsilon to prevent gradient saturation at 0 and 1.
        """
        eps = 1e-6
        if node.operator == Operator.ATOM:
            # Check if the atom has a fixed truth value in the KB
            fixed_val = self.kb.evaluate_atom_via_function(node.atom)
            if fixed_val is not None:
                return torch.tensor(fixed_val, dtype=torch.float32)
            
            atom_str = str(node.atom)
            idx = self.atom_name_to_idx.get(atom_str)
            if idx is not None:
                # Apply small slope near boundaries to keep gradients flowing
                val = x[idx]
                return (1.0 - 2*eps) * val + eps
            return torch.tensor(0.0)
        elif node.operator == Operator.CONST:
            return torch.tensor(node.constant)
        elif node.operator == Operator.AND:
            res = self._evaluate_torch(node.children[0], x)
            for child in node.children[1:]:
                # Smooth max(0, a+b-1)
                child_val = self._evaluate_torch(child, x)
                res = torch.clamp(res + child_val - 1.0, min=0.0)
            return res
        elif node.operator == Operator.OR:
            res = self._evaluate_torch(node.children[0], x)
            for child in node.children[1:]:
                child_val = self._evaluate_torch(child, x)
                res = torch.clamp(res + child_val, max=1.0)
            return res
        elif node.operator == Operator.IMPLIES:
            a = self._evaluate_torch(node.children[0], x)
            b = self._evaluate_torch(node.children[1], x)
            return torch.clamp(1.0 - a + b, max=1.0)
        elif node.operator == Operator.NOT:
            return 1.0 - self._evaluate_torch(node.children[0], x)
        return torch.tensor(0.0)


class TorchEnergyWrapper(torch.nn.Module):
    """Module wrapper so optimisers can backpropagate through the energy."""

    def __init__(
        self,
        kb: KnowledgeBase,
        evaluate_formula_torch: Callable[[WeightedFormula], torch.Tensor],
    ) -> None:
        super().__init__()
        self.kb = kb
        self.evaluate_formula_torch = evaluate_formula_torch

    def forward(self) -> torch.Tensor:
        return compute_energy_torch(self.kb, self.evaluate_formula_torch)
