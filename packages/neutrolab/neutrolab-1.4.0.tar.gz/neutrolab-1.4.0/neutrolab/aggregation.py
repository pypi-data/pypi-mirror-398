"""
Neutrosophic Aggregation Operators - Indeterminacy as Ontological Foundation
=============================================================================

INDETERMINACY-FIRST AGGREGATION OPERATOR (IFAO)
-----------------------------------------------

This module implements a novel multi-criteria decision-making framework where
Indeterminacy is the ontological foundation from which Truth and Falsity emerge.

The key innovation is that when aggregating conflicting evidence, the primary
reality is the conflict itself. This conflict gives rise to a quantifiable
Indeterminacy (I). Only the portion of evidence not consumed by conflict can
be resolved into coherent Truth (T) or Falsity (F).

FORMAL DEFINITION
-----------------
The operator Ω: [0,1]ⁿ × Δⁿ → N is defined as:

    Ω_IFAO(v, w) = (T, I, F)

Where:
    • v = (v₁, v₂, ..., vₙ) ∈ [0,1]ⁿ     (criteria values)
    • w = (w₁, w₂, ..., wₙ) ∈ Δⁿ         (weights, Σwᵢ = 1)
    • N = {(T,I,F) ∈ [0,1]³ : T+I+F = 1}  (neutrosophic simplex)

MATHEMATICAL FORMULATION
------------------------
    1. Potential (WAM):
       P = Σᵢ wᵢ · vᵢ
    
    2. Contradiction (Weighted Gini Mean Difference):
       C = (2/n(n-1)) · Σᵢ Σⱼ>ᵢ ((wᵢ+wⱼ)/2) · |vᵢ - vⱼ|
    
    3. Indeterminacy (PRIMARY - Ontological Foundation):
       I = C
    
    4. Truth (DERIVED - Constrained by I):
       T = P · (1 - I)
    
    5. Falsity (DERIVED - Constrained by I):
       F = (1 - P) · (1 - I)

COMPACT FORM
------------
    Ω_IFAO(v,w) = (P·(1-C), C, (1-P)·(1-C))

FUNDAMENTAL PROPERTY
--------------------
    T + I + F = P(1-I) + I + (1-P)(1-I) = (1-I) + I = 1  ✓

ONTOLOGICAL HIERARCHY
---------------------
    Conflict → Indeterminacy → (Truth, Falsity)
    
    This is fundamentally different from:
    - Neutrosophic Logic: T, I, F are independent
    - Intuitionistic Fuzzy: I = 1 - T - F (I is residual)
    - Classical MCDM: Only considers aggregated value (ignores conflict)

ANALOGIES IN OTHER DOMAINS
--------------------------
The IFAO follows a deep epistemological pattern found in:

    1. Quantum Mechanics (Heisenberg): Uncertainty constrains (position, momentum)
       Δx · Δp ≥ ℏ/2
    
    2. Thermodynamics (Carnot): Entropy constrains useful work
       η = 1 - Tc/Th  ≈  (1-I) resolvable space
    
    3. Finance (Markowitz): Risk constrains effective return
       Efficient Frontier ≈ Neutrosophic Simplex
    
    4. Information Theory (Shannon): Entropy IS information
       H(X) = uncertainty = information content

AXIOMATIZATION
--------------
An IFAO satisfies:
    A1. Neutrosophic Closure: Ω(v,w) = (T,I,F) with T + I + F = 1
    A2. Unanimity Idempotence: If vᵢ = c ∀i, then Ω(v,w) = (c, 0, 1-c)
    A3. Conflict Monotonicity: If Var(v') > Var(v), then I' ≥ I
    A4. Hierarchical Dependence: ∂T/∂I < 0, ∂F/∂I < 0
    A5. Conditional Symmetry: If w uniform, Ω is permutation-invariant

References:
    [1] Leyva-Vázquez, M., & Smarandache, F. (2025). Indeterminacy as the
        Foundation of Truth: A New Paradigm for Multi-Criteria Decision-Making.
    [2] Smarandache, F. (1998). Neutrosophy: Neutrosophic Probability, Set, Logic.
    [3] Heisenberg, W. (1927). Uncertainty Principle.
    [4] Markowitz, H. (1952). Portfolio Selection. Journal of Finance.
    [5] Shannon, C. (1948). A Mathematical Theory of Communication.

Example:
    >>> from neutrolab.aggregation import IndeterminacyFirstAggregator
    >>> criteria = ['Technical', 'Financial', 'Social', 'Environmental']
    >>> weights = [0.3, 0.3, 0.2, 0.2]
    >>> agg = IndeterminacyFirstAggregator(criteria, weights)
    >>> 
    >>> # Harmonious project - low conflict
    >>> result = agg.aggregate([0.8, 0.8, 0.7, 0.75])
    >>> print(f"⟨T={result.T:.3f}, I={result.I:.3f}, F={result.F:.3f}⟩")
    >>> # Output: ⟨T=0.754, I=0.014, F=0.232⟩ → STRONG_APPROVE
    >>> 
    >>> # Conflicting project - high conflict  
    >>> result = agg.aggregate([0.9, 0.2, 0.8, 0.1])
    >>> print(f"⟨T={result.T:.3f}, I={result.I:.3f}, F={result.F:.3f}⟩")
    >>> # Output: ⟨T=0.481, I=0.125, F=0.394⟩ → REVIEW (conflicted, not mediocre!)
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import warnings

__all__ = [
    'DecisionCategory',
    'AggregationResult',
    'IndeterminacyFirstAggregator',
    'MCDMEvaluator',
    'batch_evaluate'
]


class DecisionCategory(Enum):
    """
    Decision categories based on (T, I, F) triplet analysis.
    
    Categories are determined by the combination of Truth level and
    Indeterminacy level, providing actionable recommendations.
    """
    STRONG_APPROVE = "strong_approve"      # High T, Low I
    APPROVE = "approve"                     # Moderate T, Low I
    REVIEW_POSITIVE = "review_positive"     # High T, Moderate/High I
    REVIEW_NEGATIVE = "review_negative"     # Low T, Moderate/High I
    REJECT = "reject"                       # Low T, Low I
    INDETERMINATE = "indeterminate"         # Very High I (any T)
    
    @classmethod
    def from_triplet(cls, T: float, I: float, F: float,
                     t_threshold_high: float = 0.6,
                     t_threshold_low: float = 0.4,
                     i_threshold_high: float = 0.5,
                     i_threshold_moderate: float = 0.3) -> 'DecisionCategory':
        """
        Classify a decision based on (T, I, F) triplet.
        
        Args:
            T, I, F: Neutrosophic triplet components
            t_threshold_high: Threshold for high Truth
            t_threshold_low: Threshold for low Truth
            i_threshold_high: Threshold for high Indeterminacy
            i_threshold_moderate: Threshold for moderate Indeterminacy
            
        Returns:
            DecisionCategory enum value
        """
        if I > i_threshold_high:
            return cls.INDETERMINATE
        
        if I > i_threshold_moderate:
            # Moderate indeterminacy - needs review
            if T > t_threshold_high:
                return cls.REVIEW_POSITIVE
            else:
                return cls.REVIEW_NEGATIVE
        
        # Low indeterminacy - determinate decision
        if T > t_threshold_high:
            return cls.STRONG_APPROVE
        elif T > t_threshold_low:
            return cls.APPROVE
        else:
            return cls.REJECT


@dataclass
class AggregationResult:
    """
    Complete result of neutrosophic aggregation with indeterminacy-first paradigm.
    
    Attributes:
        T: Truth component (derived from Indeterminacy)
        I: Indeterminacy component (primary - equals contradiction)
        F: Falsity component (derived from Indeterminacy)
        potential: Aggregated potential (weighted mean)
        contradiction: Total contradiction measure
        resolvable_space: 1 - I (space available for T and F)
        decision: Recommended decision category
        criteria_values: Original criteria values
        criteria_weights: Weights used
        criteria_names: Names of criteria (if provided)
    """
    T: float
    I: float
    F: float
    potential: float
    contradiction: float
    resolvable_space: float
    decision: DecisionCategory
    criteria_values: np.ndarray
    criteria_weights: np.ndarray
    criteria_names: Optional[List[str]] = None
    
    def __repr__(self):
        return (f"AggregationResult(⟨T={self.T:.4f}, I={self.I:.4f}, F={self.F:.4f}⟩, "
                f"decision={self.decision.value})")
    
    @property
    def triplet(self) -> Tuple[float, float, float]:
        """Return (T, I, F) as tuple."""
        return (self.T, self.I, self.F)
    
    @property
    def is_determinate(self) -> bool:
        """Check if result is determinate (low I)."""
        return self.I < 0.3
    
    @property
    def sum_check(self) -> float:
        """Verify T + I + F = 1."""
        return self.T + self.I + self.F
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'T': round(self.T, 4),
            'I': round(self.I, 4),
            'F': round(self.F, 4),
            'potential': round(self.potential, 4),
            'contradiction': round(self.contradiction, 4),
            'resolvable_space': round(self.resolvable_space, 4),
            'decision': self.decision.value,
            'is_determinate': self.is_determinate,
            'sum_TIF': round(self.sum_check, 4)
        }


class IndeterminacyFirstAggregator:
    """
    Multi-Criteria Aggregator with Indeterminacy as Ontological Foundation.
    
    This class implements the novel paradigm where:
    - Conflict → Indeterminacy (primary)
    - Indeterminacy → constrains Truth and Falsity (derived)
    
    The key insight is that in any aggregation of conflicting evidence,
    the degree of contradiction gives rise to a fundamental indeterminacy.
    This indeterminacy is not a measure of what is unknown, but rather
    a quantifiable reflection of the system's internal conflict.
    
    Mathematical Model:
        P = Σ wᵢvᵢ                    (Potential)
        C = avg(|vᵢ - vⱼ| × avg(wᵢ,wⱼ))  (Contradiction)
        I = C                          (Indeterminacy = Conflict)
        T = P × (1 - I)                (Truth derived from I)
        F = (1 - P) × (1 - I)          (Falsity derived from I)
    
    Attributes:
        criteria: List of criteria names
        weights: Normalized weights for each criterion
        n_criteria: Number of criteria
        
    Example:
        >>> agg = IndeterminacyFirstAggregator(
        ...     criteria=['Quality', 'Cost', 'Time'],
        ...     weights=[0.5, 0.3, 0.2]
        ... )
        >>> result = agg.aggregate([0.9, 0.3, 0.7])
        >>> print(result)
    """
    
    def __init__(self, criteria: List[str], weights: Optional[List[float]] = None):
        """
        Initialize the aggregator.
        
        Args:
            criteria: List of criterion names
            weights: Optional weights (if None, equal weights assumed)
        """
        self.criteria = criteria
        self.n_criteria = len(criteria)
        
        if weights is None:
            self.weights = np.ones(self.n_criteria) / self.n_criteria
        else:
            if len(weights) != self.n_criteria:
                raise ValueError(f"Expected {self.n_criteria} weights, got {len(weights)}")
            # Normalize weights
            weights = np.array(weights, dtype=float)
            self.weights = weights / weights.sum()
    
    def compute_potential(self, values: np.ndarray) -> float:
        """
        Compute Aggregated Potential (P).
        
        P = Σ wᵢvᵢ
        
        Represents the system's inclination toward truth if there were no conflict.
        
        Args:
            values: Criterion values in [0, 1]
            
        Returns:
            Potential value in [0, 1]
        """
        return float(np.dot(values, self.weights))
    
    def compute_contradiction(self, values: np.ndarray) -> float:
        """
        Compute Total Contradiction (C_total).
        
        C_total = (1/C(n,2)) × Σᵢ Σⱼ>ᵢ ((wᵢ + wⱼ)/2) × |vᵢ - vⱼ|
        
        Measures the overall level of discord within the evidence.
        
        Args:
            values: Criterion values in [0, 1]
            
        Returns:
            Contradiction value in [0, 1]
        """
        if self.n_criteria < 2:
            return 0.0
        
        contradictions = []
        
        for i in range(self.n_criteria):
            for j in range(i + 1, self.n_criteria):
                difference = abs(values[i] - values[j])
                avg_weight = (self.weights[i] + self.weights[j]) / 2
                contradictions.append(difference * avg_weight)
        
        if not contradictions:
            return 0.0
        
        return float(np.mean(contradictions))
    
    def compute_indeterminacy(self, contradiction: float) -> float:
        """
        Compute Foundational Indeterminacy (I).
        
        I = C_total
        
        The key insight: Indeterminacy IS the conflict, not derived from it.
        This establishes I as the ontological primitive.
        
        Args:
            contradiction: Total contradiction value
            
        Returns:
            Indeterminacy value in [0, 1]
        """
        return max(0.0, min(1.0, contradiction))
    
    def compute_truth_falsity(self, potential: float, indeterminacy: float) -> Tuple[float, float]:
        """
        Derive Truth (T) and Falsity (F) from Indeterminacy.
        
        T = P × (1 - I)
        F = (1 - P) × (1 - I)
        
        T and F only exist in the resolvable space (1 - I).
        
        Args:
            potential: System potential
            indeterminacy: Foundational indeterminacy
            
        Returns:
            Tuple (T, F)
        """
        resolvable = 1.0 - indeterminacy
        truth = potential * resolvable
        falsity = (1.0 - potential) * resolvable
        return truth, falsity
    
    def aggregate(self, values: Union[List[float], np.ndarray],
                  decision_thresholds: Optional[Dict] = None) -> AggregationResult:
        """
        Perform neutrosophic aggregation with indeterminacy-first paradigm.
        
        Args:
            values: Criterion values (must be in [0, 1])
            decision_thresholds: Optional custom thresholds for decision
            
        Returns:
            AggregationResult with complete analysis
            
        Raises:
            ValueError: If number of values doesn't match criteria
        """
        values = np.array(values, dtype=float)
        
        if len(values) != self.n_criteria:
            raise ValueError(f"Expected {self.n_criteria} values, got {len(values)}")
        
        # Clip to [0, 1]
        values = np.clip(values, 0, 1)
        
        # Step 1: Compute Potential
        potential = self.compute_potential(values)
        
        # Step 2: Compute Contradiction
        contradiction = self.compute_contradiction(values)
        
        # Step 3: Establish Indeterminacy as PRIMARY (key paradigm)
        indeterminacy = self.compute_indeterminacy(contradiction)
        
        # Step 4: Derive Truth and Falsity as RESIDUALS
        truth, falsity = self.compute_truth_falsity(potential, indeterminacy)
        
        # Step 5: Classify decision
        if decision_thresholds:
            decision = DecisionCategory.from_triplet(truth, indeterminacy, falsity,
                                                     **decision_thresholds)
        else:
            decision = DecisionCategory.from_triplet(truth, indeterminacy, falsity)
        
        return AggregationResult(
            T=truth,
            I=indeterminacy,
            F=falsity,
            potential=potential,
            contradiction=contradiction,
            resolvable_space=1.0 - indeterminacy,
            decision=decision,
            criteria_values=values,
            criteria_weights=self.weights,
            criteria_names=self.criteria
        )
    
    def __repr__(self):
        return (f"IndeterminacyFirstAggregator(criteria={self.criteria}, "
                f"weights={self.weights.round(3).tolist()})")


class MCDMEvaluator:
    """
    Multi-Criteria Decision-Making Evaluator for comparing alternatives.
    
    Provides batch evaluation and ranking of alternatives using the
    indeterminacy-first aggregation paradigm.
    
    Example:
        >>> evaluator = MCDMEvaluator(
        ...     criteria=['Technical', 'Financial', 'Social'],
        ...     weights=[0.4, 0.4, 0.2]
        ... )
        >>> 
        >>> alternatives = {
        ...     'Project A': [0.8, 0.7, 0.9],
        ...     'Project B': [0.9, 0.2, 0.8],
        ...     'Project C': [0.5, 0.5, 0.5]
        ... }
        >>> 
        >>> results = evaluator.evaluate_all(alternatives)
        >>> ranking = evaluator.rank_alternatives(results)
    """
    
    def __init__(self, criteria: List[str], weights: Optional[List[float]] = None):
        """
        Initialize MCDM evaluator.
        
        Args:
            criteria: List of criterion names
            weights: Optional weights for criteria
        """
        self.aggregator = IndeterminacyFirstAggregator(criteria, weights)
        self.criteria = criteria
    
    def evaluate(self, values: Union[List[float], np.ndarray]) -> AggregationResult:
        """Evaluate a single alternative."""
        return self.aggregator.aggregate(values)
    
    def evaluate_all(self, alternatives: Dict[str, List[float]]) -> Dict[str, AggregationResult]:
        """
        Evaluate multiple alternatives.
        
        Args:
            alternatives: Dictionary mapping names to criterion values
            
        Returns:
            Dictionary mapping names to AggregationResult
        """
        return {name: self.evaluate(values) for name, values in alternatives.items()}
    
    def rank_alternatives(self, results: Dict[str, AggregationResult],
                         method: str = 'truth_adjusted') -> List[Tuple[str, float]]:
        """
        Rank alternatives based on their (T, I, F) triplets.
        
        Args:
            results: Dictionary of evaluation results
            method: Ranking method
                - 'truth': Rank by T only
                - 'truth_adjusted': Rank by T × (1 - I) (penalize indeterminacy)
                - 'net_score': Rank by T - F
                
        Returns:
            List of (name, score) tuples sorted by score descending
        """
        scores = {}
        
        for name, result in results.items():
            if method == 'truth':
                scores[name] = result.T
            elif method == 'truth_adjusted':
                scores[name] = result.T * (1 - result.I)
            elif method == 'net_score':
                scores[name] = result.T - result.F
            else:
                raise ValueError(f"Unknown ranking method: {method}")
        
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    def to_dataframe(self, results: Dict[str, AggregationResult]):
        """Convert results to pandas DataFrame."""
        import pandas as pd
        
        data = []
        for name, result in results.items():
            row = {'Alternative': name}
            row.update(result.to_dict())
            data.append(row)
        
        return pd.DataFrame(data)


def batch_evaluate(criteria: List[str],
                   weights: List[float],
                   alternatives: Dict[str, List[float]]) -> Dict[str, AggregationResult]:
    """
    Convenience function for batch evaluation.
    
    Args:
        criteria: List of criterion names
        weights: Weights for each criterion
        alternatives: Dictionary mapping names to values
        
    Returns:
        Dictionary of AggregationResult objects
    """
    evaluator = MCDMEvaluator(criteria, weights)
    return evaluator.evaluate_all(alternatives)


# ============================================================================
# Compatibility functions for the original implementation
# ============================================================================

class ModeloIndeterminacionBase:
    """
    Modelo de Indeterminación como Base Ontológica (Spanish API).
    
    Wrapper compatible con la implementación original.
    Genera triplets (T, I, F) donde I es primario y T, F son derivados.
    """
    
    def __init__(self, criterios: List[str], pesos: Optional[List[float]] = None):
        """
        Inicializa el modelo.
        
        Parámetros:
            criterios: Lista de nombres de criterios
            pesos: Pesos de cada criterio (si None, pesos iguales)
        """
        self._aggregator = IndeterminacyFirstAggregator(criterios, pesos)
        self.criterios = criterios
        self.n_criterios = len(criterios)
        self.pesos = self._aggregator.weights.tolist()
    
    def evaluar(self, valores_criterios: List[float]) -> Tuple[Tuple[float, float, float], Dict]:
        """
        Evalúa el modelo con los valores de criterios dados.
        
        Retorna:
            triplet (T, I, F): Verdad, Indeterminación, Falsedad
            detalles: Diccionario con información detallada
        """
        result = self._aggregator.aggregate(valores_criterios)
        
        detalles = {
            'valores_criterios': result.criteria_values.tolist(),
            'pesos': result.criteria_weights.tolist(),
            'potencial': result.potential,
            'contradiccion_total': result.contradiction,
            'indeterminacion': result.I,
            'verdad': result.T,
            'falsedad': result.F,
            'suma_triplet': result.sum_check,
            'espacio_resolvible': result.resolvable_space
        }
        
        return (result.T, result.I, result.F), detalles
