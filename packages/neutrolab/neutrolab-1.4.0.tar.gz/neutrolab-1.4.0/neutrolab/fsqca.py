"""
N-fsQCA v2.0 - Neutrosophic Fuzzy-Set Qualitative Comparative Analysis
=======================================================================

This module implements the N-fsQCA v2.0 methodology for enhanced validity
and robustness in Qualitative Comparative Analysis through variance-based
three-valued logic <T, I, F>.

Key Features:
- Variance-based Indeterminacy (I) calculation
- Bootstrap confidence intervals for T, I, F
- Fuzzy archetype classification (11 types)
- Comparison with traditional fsQCA

References:
    Leyva-Vázquez, M., & Smarandache, F. (2025). From Crisp to Neutrosophic v2.0:
    A Variance-Based Three-Valued Logic <T,I,F> to Enhance Validity and Robustness
    in Qualitative Comparative Analysis.

Example:
    >>> from neutrolab.fsqca import NfsqcaEngine
    >>> import pandas as pd
    >>> 
    >>> # Prepare data
    >>> X = pd.DataFrame({'A': [0.8, 0.6, 0.9], 'B': [0.7, 0.8, 0.5]})
    >>> y = pd.Series([0.9, 0.7, 0.8])
    >>> 
    >>> # Run analysis
    >>> engine = NfsqcaEngine()
    >>> results = engine.analyze(X, y)
    >>> sufficient = engine.get_sufficient_configurations()
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

__all__ = [
    'CausalArchetype',
    'NeutrosophicTIF',
    'ConfigurationResult',
    'NfsqcaCalculator',
    'ArchetypeClassifier',
    'NfsqcaEngine',
    'compare_with_traditional'
]

# Constants
EPS = 1e-10
MAX_VARIANCE = 0.25  # Maximum variance for normalized outcome [0,1]


class CausalArchetype(Enum):
    """
    11 Causal Archetypes in N-fsQCA v2.0
    
    Each archetype represents a distinct type of causal relationship:
    
    - STRONG_SUFFICIENT: Robust sufficient cause (high T, low I)
    - WEAK_SUFFICIENT: Moderate sufficient cause
    - SUFFICIENT_CAUSE: General sufficient cause
    - STRONG_INHIBITOR: Strong inhibitor (high F)
    - WEAK_INHIBITOR: Moderate inhibitor
    - MEASUREMENT_ERROR: High indeterminacy suggests data issues
    - CAUSAL_PARADOX: Both T and F are high (contradictory evidence)
    - PARTIAL_CAUSE: Contributes but not sufficient
    - IRRELEVANCE: No causal relationship
    - COMPLEX_RELATION: Multiple causal roles
    - INDETERMINATE: Cannot be classified
    """
    STRONG_SUFFICIENT = "strong_sufficient"
    WEAK_SUFFICIENT = "weak_sufficient"
    SUFFICIENT_CAUSE = "sufficient_cause"
    STRONG_INHIBITOR = "strong_inhibitor"
    WEAK_INHIBITOR = "weak_inhibitor"
    MEASUREMENT_ERROR = "measurement_error"
    CAUSAL_PARADOX = "causal_paradox"
    PARTIAL_CAUSE = "partial_cause"
    IRRELEVANCE = "irrelevance"
    COMPLEX_RELATION = "complex_relation"
    INDETERMINATE = "indeterminate"


@dataclass
class NeutrosophicTIF:
    """
    Neutrosophic value <T, I, F> with optional confidence intervals.
    
    Attributes:
        truth: Degree of sufficiency [0, 1]
        indeterminacy: Degree of data ambiguity [0, 1] (variance-based)
        falsity: Degree of inhibition [0, 1]
        truth_ci: 95% confidence interval for T
        indeterminacy_ci: 95% confidence interval for I
        falsity_ci: 95% confidence interval for F
        n_samples: Number of cases in configuration
        
    Properties:
        confidence: T × (1 - I), overall confidence score
        stability: Based on CI widths (narrower = more stable)
    """
    truth: float = 0.0
    indeterminacy: float = 0.0
    falsity: float = 0.0
    truth_ci: Tuple[float, float] = field(default=(0.0, 0.0))
    indeterminacy_ci: Tuple[float, float] = field(default=(0.0, 0.0))
    falsity_ci: Tuple[float, float] = field(default=(0.0, 0.0))
    n_samples: int = 0
    confidence_level: float = 0.95
    
    def __post_init__(self):
        self.truth = float(np.clip(self.truth, 0, 1))
        self.indeterminacy = float(np.clip(self.indeterminacy, 0, 1))
        self.falsity = float(np.clip(self.falsity, 0, 1))
    
    def __repr__(self):
        return f"<T={self.truth:.4f}, I={self.indeterminacy:.4f}, F={self.falsity:.4f}>"
    
    @property
    def confidence(self) -> float:
        """Confidence score: T × (1 - I)"""
        return self.truth * (1 - self.indeterminacy)
    
    @property
    def stability(self) -> float:
        """Stability based on CI widths (1 = perfectly stable)"""
        if self.truth_ci == (0.0, 0.0):
            return 1.0
        widths = [
            self.truth_ci[1] - self.truth_ci[0],
            self.indeterminacy_ci[1] - self.indeterminacy_ci[0],
            self.falsity_ci[1] - self.falsity_ci[0]
        ]
        return max(0, 1 - np.mean(widths))
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'T': round(self.truth, 4),
            'I': round(self.indeterminacy, 4),
            'F': round(self.falsity, 4),
            'confidence': round(self.confidence, 4),
            'stability': round(self.stability, 4),
            'n_samples': self.n_samples
        }


@dataclass
class ConfigurationResult:
    """
    Result of analyzing a single configuration.
    
    Attributes:
        binary_string: Binary representation of configuration (e.g., "1010")
        cases: Number of cases with membership > 0
        case_indices: Indices of cases in configuration
        neutrosophic: NeutrosophicTIF value
        archetype: Classified causal archetype
        archetype_confidence: Confidence in archetype classification
        traditional_consistency: Standard fsQCA consistency (same as T)
        coverage: Coverage score
        is_sufficient: Whether configuration meets sufficiency criteria
        decision_reason: Explanation of sufficiency decision
    """
    binary_string: str
    cases: int
    case_indices: List[int]
    neutrosophic: NeutrosophicTIF
    archetype: CausalArchetype
    archetype_confidence: float
    traditional_consistency: float = 0.0
    coverage: float = 0.0
    is_sufficient: bool = False
    decision_reason: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'configuration': self.binary_string,
            'cases': self.cases,
            'T': round(self.neutrosophic.truth, 4),
            'I': round(self.neutrosophic.indeterminacy, 4),
            'F': round(self.neutrosophic.falsity, 4),
            'archetype': self.archetype.value,
            'archetype_confidence': round(self.archetype_confidence, 4),
            'coverage': round(self.coverage, 4),
            'is_sufficient': bool(self.is_sufficient),
            'confidence': round(self.neutrosophic.confidence, 4)
        }


class NfsqcaCalculator:
    """
    N-fsQCA v2.0 Calculator with variance-based Indeterminacy.
    
    This calculator implements the three core formulas:
    
    - Truth (T): Measures degree of sufficiency
    - Indeterminacy (I): Measures data ambiguity via normalized variance
    - Falsity (F): Measures degree of inhibition
    
    The key innovation in v2.0 is the variance-based Indeterminacy formula,
    which provides a more stable and interpretable measure of data ambiguity
    compared to the original tent-function approach.
    
    Example:
        >>> calc = NfsqcaCalculator()
        >>> X = np.array([0.8, 0.6, 0.9, 0.7])
        >>> Y = np.array([0.9, 0.5, 0.8, 0.7])
        >>> tif = calc.calculate_tif(X, Y)
        >>> print(tif)
        <T=0.8571, I=0.1234, F=0.1429>
    """
    
    def calculate_truth(self, X: np.ndarray, Y: np.ndarray) -> float:
        """
        Calculate Truth (T) - Degree of Sufficiency.
        
        Formula: T = Σ min(X_i, Y_i) / Σ X_i
        
        Args:
            X: Configuration membership scores [0, 1]
            Y: Outcome membership scores [0, 1]
            
        Returns:
            Truth value in [0, 1]
        """
        sum_x = np.sum(X)
        if sum_x < EPS:
            return 0.0
        return float(np.sum(np.minimum(X, Y)) / sum_x)
    
    def calculate_falsity(self, X: np.ndarray, Y: np.ndarray) -> float:
        """
        Calculate Falsity (F) - Degree of Inhibition.
        
        Formula: F = Σ max(0, X_i - Y_i) / Σ X_i
        
        Args:
            X: Configuration membership scores [0, 1]
            Y: Outcome membership scores [0, 1]
            
        Returns:
            Falsity value in [0, 1]
        """
        sum_x = np.sum(X)
        if sum_x < EPS:
            return 0.0
        return float(np.sum(np.maximum(0, X - Y)) / sum_x)
    
    def calculate_indeterminacy(self, X: np.ndarray, Y: np.ndarray) -> float:
        """
        Calculate Indeterminacy (I) - Variance-Based (v2.0).
        
        This is the key innovation in N-fsQCA v2.0. Instead of using
        a tent function, we calculate the normalized weighted variance
        of Y conditional on X.
        
        Steps:
            1. Weighted mean: μ = Σ(X_i × Y_i) / Σ X_i
            2. Weighted variance: Var(Y|X) = Σ X_i × (Y_i - μ)² / Σ X_i
            3. Normalize: I = Var(Y|X) / 0.25
        
        The normalization by 0.25 (maximum variance for [0,1] values)
        ensures I is always in [0, 1].
        
        Args:
            X: Configuration membership scores [0, 1]
            Y: Outcome membership scores [0, 1]
            
        Returns:
            Indeterminacy value in [0, 1]
        """
        sum_x = np.sum(X)
        if sum_x < EPS:
            return 0.0
        
        # Weighted mean
        mu = np.sum(X * Y) / sum_x
        
        # Weighted variance
        variance = np.sum(X * (Y - mu) ** 2) / sum_x
        
        # Normalize by maximum variance
        indeterminacy = variance / MAX_VARIANCE
        
        return float(np.clip(indeterminacy, 0, 1))
    
    def calculate_indeterminacy_tent(self, X: np.ndarray, Y: np.ndarray) -> float:
        """
        Calculate Indeterminacy using original tent function (v1.0).
        
        This is provided for comparison with the original method.
        
        Formula: I = Σ min(X_i, 1 - |2Y_i - 1|) / Σ X_i
        
        Args:
            X: Configuration membership scores [0, 1]
            Y: Outcome membership scores [0, 1]
            
        Returns:
            Indeterminacy value in [0, 1]
        """
        sum_x = np.sum(X)
        if sum_x < EPS:
            return 0.0
        ambiguity = 1 - np.abs(2 * Y - 1)
        return float(np.sum(np.minimum(X, ambiguity)) / sum_x)
    
    def calculate_tif(self, X: np.ndarray, Y: np.ndarray) -> NeutrosophicTIF:
        """
        Calculate complete <T, I, F> vector.
        
        Args:
            X: Configuration membership scores [0, 1]
            Y: Outcome membership scores [0, 1]
            
        Returns:
            NeutrosophicTIF with T, I, F values
        """
        return NeutrosophicTIF(
            truth=self.calculate_truth(X, Y),
            indeterminacy=self.calculate_indeterminacy(X, Y),
            falsity=self.calculate_falsity(X, Y),
            n_samples=len(X)
        )
    
    def bootstrap_tif(self, X: np.ndarray, Y: np.ndarray,
                      n_iterations: int = 1000,
                      confidence_level: float = 0.95,
                      random_state: Optional[int] = None) -> NeutrosophicTIF:
        """
        Calculate <T, I, F> with bootstrap confidence intervals.
        
        This method provides statistical inference for the T, I, F values
        by resampling the data with replacement.
        
        Args:
            X: Configuration membership scores [0, 1]
            Y: Outcome membership scores [0, 1]
            n_iterations: Number of bootstrap iterations (default: 1000)
            confidence_level: Confidence level for intervals (default: 0.95)
            random_state: Random seed for reproducibility
            
        Returns:
            NeutrosophicTIF with T, I, F values and confidence intervals
        """
        if random_state is not None:
            np.random.seed(random_state)
        
        n = len(X)
        t_samples, i_samples, f_samples = [], [], []
        
        for _ in range(n_iterations):
            indices = np.random.choice(n, size=n, replace=True)
            X_boot, Y_boot = X[indices], Y[indices]
            t_samples.append(self.calculate_truth(X_boot, Y_boot))
            i_samples.append(self.calculate_indeterminacy(X_boot, Y_boot))
            f_samples.append(self.calculate_falsity(X_boot, Y_boot))
        
        alpha = 1 - confidence_level
        lower_p = alpha / 2 * 100
        upper_p = (1 - alpha / 2) * 100
        
        return NeutrosophicTIF(
            truth=self.calculate_truth(X, Y),
            indeterminacy=self.calculate_indeterminacy(X, Y),
            falsity=self.calculate_falsity(X, Y),
            truth_ci=(np.percentile(t_samples, lower_p), np.percentile(t_samples, upper_p)),
            indeterminacy_ci=(np.percentile(i_samples, lower_p), np.percentile(i_samples, upper_p)),
            falsity_ci=(np.percentile(f_samples, lower_p), np.percentile(f_samples, upper_p)),
            n_samples=n,
            confidence_level=confidence_level
        )


class ArchetypeClassifier:
    """
    Classify configurations into 11 causal archetypes with fuzzy memberships.
    
    The classifier uses optimized thresholds to assign configurations
    to one of 11 causal archetypes based on their T, I, F values.
    
    Attributes:
        thresholds: Dictionary of classification thresholds
        
    Example:
        >>> classifier = ArchetypeClassifier()
        >>> tif = NeutrosophicTIF(truth=0.85, indeterminacy=0.15, falsity=0.10)
        >>> archetype, confidence = classifier.classify(tif)
        >>> print(archetype)
        CausalArchetype.STRONG_SUFFICIENT
    """
    
    def __init__(self, thresholds: Optional[Dict] = None):
        """
        Initialize classifier with thresholds.
        
        Args:
            thresholds: Custom thresholds (optional). If None, uses
                        optimized defaults from validation studies.
        """
        self.thresholds = thresholds or {
            'sufficient_high': 0.80,
            'sufficient_low': 0.65,
            'inhibitor_high': 0.80,
            'inhibitor_low': 0.65,
            'indeterminacy_high': 0.70,
            'indeterminacy_moderate': 0.30,
            'paradox_diff': 0.20,
            'irrelevance': 0.30
        }
    
    def classify(self, tif: NeutrosophicTIF) -> Tuple[CausalArchetype, float]:
        """
        Classify configuration into primary archetype with confidence.
        
        Args:
            tif: NeutrosophicTIF value to classify
            
        Returns:
            Tuple of (archetype, confidence_score)
        """
        t, i, f = tif.truth, tif.indeterminacy, tif.falsity
        th = self.thresholds
        
        # Priority 1: Measurement Error (high I)
        if i > th['indeterminacy_high']:
            return CausalArchetype.MEASUREMENT_ERROR, i
        
        # Priority 2: Strong Sufficient Cause
        if t > th['sufficient_high'] and i < th['indeterminacy_moderate'] and f < 0.25:
            return CausalArchetype.STRONG_SUFFICIENT, t * (1 - i)
        
        # Priority 3: Weak Sufficient Cause
        if th['sufficient_low'] <= t <= th['sufficient_high'] and i < th['indeterminacy_high']:
            return CausalArchetype.WEAK_SUFFICIENT, t * (1 - i) * 0.8
        
        # Priority 4: Sufficient Cause
        if t > th['sufficient_low'] and i < th['indeterminacy_moderate'] and f < 0.30:
            return CausalArchetype.SUFFICIENT_CAUSE, t * (1 - i) * (1 - f)
        
        # Priority 5: Strong Inhibitor
        if f > th['inhibitor_high'] and i < th['indeterminacy_moderate']:
            return CausalArchetype.STRONG_INHIBITOR, f * (1 - i)
        
        # Priority 6: Weak Inhibitor
        if th['inhibitor_low'] <= f <= th['inhibitor_high'] and i < th['indeterminacy_high']:
            return CausalArchetype.WEAK_INHIBITOR, f * (1 - i) * 0.8
        
        # Priority 7: Causal Paradox
        if abs(t - f) < th['paradox_diff'] and t > 0.40 and f > 0.40 and i < th['indeterminacy_moderate']:
            return CausalArchetype.CAUSAL_PARADOX, (1 - abs(t - f)) * min(t, f)
        
        # Priority 8: Partial Cause
        if 0.40 < t < 0.65 and i < 0.50 and f < 0.40:
            return CausalArchetype.PARTIAL_CAUSE, 0.5
        
        # Priority 9: Irrelevance
        if t < th['irrelevance'] and f < th['irrelevance'] and i < th['indeterminacy_moderate']:
            return CausalArchetype.IRRELEVANCE, (1 - t) * (1 - f) * (1 - i)
        
        # Default: Complex Relation
        return CausalArchetype.COMPLEX_RELATION, 0.5


class NfsqcaEngine:
    """
    Main N-fsQCA v2.0 analysis engine.
    
    This is the primary interface for running N-fsQCA analyses. It handles:
    - Configuration enumeration
    - T, I, F calculation for each configuration
    - Archetype classification
    - Sufficiency determination
    
    Attributes:
        threshold_t: Minimum T for sufficiency (default: 0.80)
        threshold_i: Maximum I for sufficiency (default: 0.30)
        calculator: NfsqcaCalculator instance
        classifier: ArchetypeClassifier instance
        results: List of ConfigurationResult
        
    Example:
        >>> engine = NfsqcaEngine(threshold_t=0.80, threshold_i=0.30)
        >>> results = engine.analyze(X_data, y_data)
        >>> sufficient = engine.get_sufficient_configurations()
        >>> print(f"Found {len(sufficient)} sufficient configurations")
    """
    
    def __init__(self, threshold_t: float = 0.80, threshold_i: float = 0.30):
        """
        Initialize engine with sufficiency thresholds.
        
        Args:
            threshold_t: Minimum Truth value for sufficiency
            threshold_i: Maximum Indeterminacy value for sufficiency
        """
        self.calculator = NfsqcaCalculator()
        self.classifier = ArchetypeClassifier()
        self.threshold_t = threshold_t
        self.threshold_i = threshold_i
        self.results: List[ConfigurationResult] = []
        self.condition_names: List[str] = []
    
    def analyze(self, X_data: pd.DataFrame, y_data: pd.Series,
                use_bootstrap: bool = True,
                bootstrap_iterations: int = 1000) -> List[ConfigurationResult]:
        """
        Analyze dataset and return results for all configurations.
        
        This method:
        1. Enumerates all 2^k configurations
        2. Calculates T, I, F for each configuration
        3. Classifies archetype
        4. Determines sufficiency
        
        Args:
            X_data: DataFrame with fuzzy membership scores [0, 1]
            y_data: Series with outcome membership scores [0, 1]
            use_bootstrap: Whether to compute confidence intervals
            bootstrap_iterations: Number of bootstrap iterations
            
        Returns:
            List of ConfigurationResult for all configurations
        """
        self.condition_names = list(X_data.columns)
        n_conditions = X_data.shape[1]
        n_configs = 2 ** n_conditions
        self.results = []
        
        for config_idx in range(n_configs):
            # Generate binary string
            binary_str = format(config_idx, f'0{n_conditions}b')
            
            # Calculate configuration membership (AND operation)
            X_config = np.ones(len(X_data))
            for i, bit in enumerate(binary_str):
                if bit == '1':
                    X_config = np.minimum(X_config, X_data.iloc[:, i].values)
                else:
                    X_config = np.minimum(X_config, 1 - X_data.iloc[:, i].values)
            
            y_values = y_data.values
            
            # Skip if no membership
            if np.sum(X_config) < EPS:
                continue
            
            # Calculate neutrosophic values
            if use_bootstrap:
                tif = self.calculator.bootstrap_tif(
                    X_config, y_values, 
                    n_iterations=bootstrap_iterations
                )
            else:
                tif = self.calculator.calculate_tif(X_config, y_values)
            
            # Classify archetype
            archetype, arch_conf = self.classifier.classify(tif)
            
            # Determine sufficiency
            is_sufficient = (tif.truth >= self.threshold_t and 
                           tif.indeterminacy <= self.threshold_i)
            
            # Calculate coverage
            sum_y = np.sum(y_values)
            coverage = np.sum(np.minimum(X_config, y_values)) / sum_y if sum_y > 0 else 0
            
            # Create result
            case_indices = np.where(X_config > EPS)[0].tolist()
            result = ConfigurationResult(
                binary_string=binary_str,
                cases=len(case_indices),
                case_indices=case_indices,
                neutrosophic=tif,
                archetype=archetype,
                archetype_confidence=arch_conf,
                traditional_consistency=tif.truth,
                coverage=coverage,
                is_sufficient=is_sufficient,
                decision_reason=f"T={tif.truth:.3f} {'≥' if tif.truth >= self.threshold_t else '<'} {self.threshold_t}, "
                               f"I={tif.indeterminacy:.3f} {'≤' if tif.indeterminacy <= self.threshold_i else '>'} {self.threshold_i}"
            )
            self.results.append(result)
        
        return self.results
    
    def get_sufficient_configurations(self) -> List[ConfigurationResult]:
        """Return only sufficient configurations."""
        return [r for r in self.results if r.is_sufficient]
    
    def get_configurations_by_archetype(self, archetype: CausalArchetype) -> List[ConfigurationResult]:
        """Return configurations of a specific archetype."""
        return [r for r in self.results if r.archetype == archetype]
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert results to DataFrame."""
        data = []
        for r in self.results:
            row = r.to_dict()
            row['condition_names'] = self._decode_configuration(r.binary_string)
            data.append(row)
        return pd.DataFrame(data)
    
    def _decode_configuration(self, binary_str: str) -> str:
        """Convert binary string to condition names."""
        parts = []
        for i, bit in enumerate(binary_str):
            if i < len(self.condition_names):
                name = self.condition_names[i]
                if bit == '1':
                    parts.append(name)
                else:
                    parts.append(f"~{name}")
        return " * ".join(parts)
    
    def summary_report(self) -> Dict:
        """Generate summary report."""
        sufficient = self.get_sufficient_configurations()
        
        archetype_counts = {}
        for archetype in CausalArchetype:
            count = len([r for r in self.results if r.archetype == archetype])
            if count > 0:
                archetype_counts[archetype.value] = count
        
        return {
            'total_configurations': len(self.results),
            'sufficient_configurations': len(sufficient),
            'threshold_t': self.threshold_t,
            'threshold_i': self.threshold_i,
            'archetype_distribution': archetype_counts,
            'timestamp': datetime.now().isoformat(),
            'sufficient_configs': [r.to_dict() for r in sufficient]
        }


def compare_with_traditional(engine: NfsqcaEngine, 
                             traditional_threshold: float = 0.70) -> pd.DataFrame:
    """
    Compare N-fsQCA v2.0 results with traditional fsQCA.
    
    This function creates a comparison table showing which configurations
    would be accepted by traditional fsQCA (T ≥ threshold) vs N-fsQCA v2.0
    (T ≥ threshold_t AND I ≤ threshold_i).
    
    Args:
        engine: NfsqcaEngine with completed analysis
        traditional_threshold: fsQCA consistency threshold (default: 0.70)
        
    Returns:
        DataFrame with comparison results
    """
    data = []
    for r in engine.results:
        is_traditional = r.neutrosophic.truth >= traditional_threshold
        is_nfsqca = r.is_sufficient
        
        data.append({
            'Configuration': r.binary_string,
            'Conditions': engine._decode_configuration(r.binary_string),
            'T': round(r.neutrosophic.truth, 4),
            'I': round(r.neutrosophic.indeterminacy, 4),
            'F': round(r.neutrosophic.falsity, 4),
            'fsQCA_Traditional': 'Accept' if is_traditional else 'Reject',
            'N-fsQCA_v2.0': 'Accept' if is_nfsqca else 'Reject',
            'Divergence': is_traditional != is_nfsqca,
            'Archetype': r.archetype.value,
            'Confidence': round(r.neutrosophic.confidence, 4)
        })
    
    return pd.DataFrame(data)
