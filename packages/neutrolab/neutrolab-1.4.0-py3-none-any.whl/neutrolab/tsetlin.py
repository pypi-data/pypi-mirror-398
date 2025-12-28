"""
Neutrosophic Tsetlin Machine (NML) - Neutrosophic Meta-Learning Framework
==========================================================================

This module implements the Neutrosophic Meta-Learning (NML) framework for
enhanced interpretability in Tsetlin Machines through post-hoc analysis
with uncertainty quantification.

The Tsetlin Machine is a machine learning algorithm based on propositional
logic that learns patterns as conjunctions of literals. NML extends this
by computing neutrosophic ⟨T, I, F⟩ values for each clause, providing:

- Truth (T): Probability that the clause correctly predicts its target class
- Indeterminacy (I): Uncertainty or ambiguity in the clause's behavior
- Falsity (F): Probability that the clause incorrectly predicts

Key Features:
- Post-hoc neutrosophic analysis of Tsetlin Machine clauses
- Rule classification (certain, uncertain, contradictory)
- Laplace smoothing for stable estimates
- Minimal computational overhead (~4%)

Requirements:
    pyTsetlinMachine: pip install pyTsetlinMachine

References:
    Leyva-Vázquez, M., & Smarandache, F. (2025). Neutrosophic Meta-Learning
    Framework for Enhanced Interpretability in Tsetlin Machines.
    
    Granmo, O. C. (2018). The Tsetlin Machine - A Game Theoretic Bandit
    Driven Approach to Optimal Pattern Recognition.

Example:
    >>> from neutrolab.tsetlin import NeutroTsetlinMachine
    >>> import numpy as np
    >>> 
    >>> # Prepare binary data
    >>> X_train = np.array([[1,0,1,0], [0,1,0,1], [1,1,0,0]])
    >>> y_train = np.array([1, 0, 1])
    >>> 
    >>> # Train and analyze
    >>> ntm = NeutroTsetlinMachine(n_clauses=20, T=10, s=3.0)
    >>> ntm.fit(X_train, y_train, epochs=100)
    >>> ntm.analyze_neutrosophic(X_train, y_train)
    >>> summary = ntm.get_summary()
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import warnings

__all__ = [
    'RuleCategory',
    'NeutroRule',
    'NeutroTsetlinMachine',
    'NMLAnalyzer'
]


class RuleCategory(Enum):
    """
    Categories for classifying neutrosophic rules based on their T, I, F values.
    
    - CERTAIN: High certainty rules with low indeterminacy (I < 0.35)
    - UNCERTAIN: Rules with high indeterminacy (I > 0.45)
    - CONTRADICTORY: Rules where T ≈ F (|T - F| < 0.15)
    - INACTIVE: Rules that never activate
    - NORMAL: Rules that don't fit other categories
    """
    CERTAIN = "certain"
    UNCERTAIN = "uncertain"
    CONTRADICTORY = "contradictory"
    INACTIVE = "inactive"
    NORMAL = "normal"


@dataclass
class NeutroRule:
    """
    Represents a neutrosophic rule extracted from a Tsetlin Machine clause.
    
    Each clause in a Tsetlin Machine votes for a specific class. This class
    stores the neutrosophic analysis of how reliably the clause predicts
    its target class.
    
    Attributes:
        clause_id: Index of the clause within its class
        class_id: The class this clause votes for (0 or 1 for binary)
        T: Truth component - probability of correct prediction when activated
        I: Indeterminacy component - uncertainty measure
        F: Falsity component - probability of incorrect prediction
        activations: Total number of samples that activated this clause
        correct: Number of correct predictions when activated
        coverage: Proportion of samples that activate this clause
        category: Classification of the rule (certain, uncertain, etc.)
        
    Properties:
        confidence: T × (1 - I), overall confidence score
        precision: Alias for T (probability of correctness)
    """
    clause_id: int
    class_id: int
    T: float
    I: float
    F: float
    activations: int
    correct: int
    coverage: float
    category: RuleCategory = field(default=RuleCategory.NORMAL)
    
    def __post_init__(self):
        """Classify the rule based on T, I, F values."""
        if self.activations == 0:
            self.category = RuleCategory.INACTIVE
        elif self.I < 0.35:
            self.category = RuleCategory.CERTAIN
        elif self.I > 0.45:
            self.category = RuleCategory.UNCERTAIN
        elif abs(self.T - self.F) < 0.15:
            self.category = RuleCategory.CONTRADICTORY
        else:
            self.category = RuleCategory.NORMAL
    
    def __repr__(self):
        return (f"NeutroRule(clause={self.clause_id}, class={self.class_id}, "
                f"⟨T={self.T:.3f}, I={self.I:.3f}, F={self.F:.3f}⟩, "
                f"category={self.category.value})")
    
    @property
    def confidence(self) -> float:
        """Confidence score: T × (1 - I)"""
        return self.T * (1 - self.I)
    
    @property
    def precision(self) -> float:
        """Precision (alias for T)"""
        return self.T
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'clause_id': self.clause_id,
            'class_id': self.class_id,
            'T': round(self.T, 4),
            'I': round(self.I, 4),
            'F': round(self.F, 4),
            'activations': self.activations,
            'correct': self.correct,
            'coverage': round(self.coverage, 4),
            'category': self.category.value,
            'confidence': round(self.confidence, 4)
        }


class NMLAnalyzer:
    """
    Neutrosophic Meta-Learning Analyzer for Tsetlin Machines.
    
    This class performs post-hoc analysis of a trained Tsetlin Machine,
    computing neutrosophic ⟨T, I, F⟩ values for each clause based on
    its activation behavior across the training set.
    
    The key insight is that each clause can be viewed as a rule, and we can
    measure how reliably that rule predicts its target class:
    
    - T (Truth): P(correct | clause activated)
    - F (Falsity): P(incorrect | clause activated)  
    - I (Indeterminacy): 1 - |T - F|, measuring uncertainty
    
    Attributes:
        tm: The trained Tsetlin Machine model
        n_clauses: Number of clauses in the model
        rules: List of NeutroRule objects after analysis
        laplace_smoothing: Whether to apply Laplace smoothing
        
    Example:
        >>> analyzer = NMLAnalyzer(tm, n_clauses=60)
        >>> analyzer.analyze(X_train, y_train)
        >>> summary = analyzer.summary()
        >>> print(f"Active clauses: {summary['n_active']}")
    """
    
    def __init__(self, tm: Any, n_clauses: int, laplace_smoothing: bool = True, alpha: float = 1.0):
        """
        Initialize NML Analyzer.
        
        Args:
            tm: Trained Tsetlin Machine model (must have transform() method)
            n_clauses: Number of clauses in the model
            laplace_smoothing: Whether to apply Laplace smoothing for
                              stability with small sample sizes
            alpha: Laplace smoothing parameter (default: 1.0 = add-one smoothing)
                   T_c = (TP + α) / (TP + FN + 2α)
                   Higher values give more conservative estimates
        """
        self.tm = tm
        self.n_clauses = n_clauses
        self.rules: List[NeutroRule] = []
        self.laplace_smoothing = laplace_smoothing
        self.alpha = alpha
        self._analyzed = False
    
    def analyze(self, X: np.ndarray, y: np.ndarray) -> 'NMLAnalyzer':
        """
        Analyze clause activations and compute neutrosophic components.
        
        For each clause, we:
        1. Find all samples where the clause activates
        2. Count how many of those have the target class
        3. Compute T = P(correct | activated), F = P(incorrect | activated)
        4. Compute I = 1 - |T - F| as uncertainty measure
        5. Normalize so T + I + F = 1
        
        Args:
            X: Input features (n_samples, n_features), must be binarized
            y: Target labels (n_samples,), binary {0, 1}
            
        Returns:
            self: Updated NMLAnalyzer instance with computed rules
            
        Raises:
            ValueError: If model doesn't have transform() method
        """
        # Get clause activations via transform
        if hasattr(self.tm, 'transform'):
            bits = self.tm.transform(X)
        else:
            raise ValueError("Model must have transform() method. "
                           "Ensure you're using pyTsetlinMachine.")
        
        n_samples = len(X)
        self.rules = []
        
        # For binary classification, clauses are split:
        # First half vote for class 0, second half for class 1
        n_classes = 2  # Binary classification
        clauses_per_class = self.n_clauses // n_classes
        
        for class_id in range(n_classes):
            start = class_id * clauses_per_class
            end = start + clauses_per_class
            
            for j, clause_idx in enumerate(range(start, end)):
                # Get activation pattern for this clause
                clause_bits = bits[:, clause_idx]
                total_act = int(np.sum(clause_bits))
                
                if total_act == 0:
                    # Inactive clause - maximum indeterminacy
                    T, I, F = 0, 1, 0
                    correct = 0
                else:
                    # Find samples where clause activates
                    active_idx = np.where(clause_bits == 1)[0]
                    y_active = y[active_idx]
                    
                    # Count correct predictions (where y matches class_id)
                    correct = int(np.sum(y_active == class_id))
                    
                    # Compute raw T and F
                    if self.laplace_smoothing:
                        # Laplace smoothing: T_c = (TP + α) / (TP + FN + 2α)
                        T_raw = (correct + self.alpha) / (total_act + 2 * self.alpha)
                        F_raw = (total_act - correct + self.alpha) / (total_act + 2 * self.alpha)
                    else:
                        T_raw = correct / total_act
                        F_raw = (total_act - correct) / total_act
                    
                    # Indeterminacy as uncertainty measure
                    I_raw = 1 - abs(T_raw - F_raw)
                    
                    # Normalize to sum to 1
                    total = T_raw + I_raw + F_raw
                    if total > 0:
                        T, I, F = T_raw/total, I_raw/total, F_raw/total
                    else:
                        T, I, F = 0, 1, 0
                
                # Create rule
                rule = NeutroRule(
                    clause_id=j,
                    class_id=class_id,
                    T=T, I=I, F=F,
                    activations=total_act,
                    correct=correct,
                    coverage=total_act / n_samples
                )
                self.rules.append(rule)
        
        self._analyzed = True
        return self
    
    def get_rules(self, category: Optional[RuleCategory] = None) -> List[NeutroRule]:
        """
        Get rules, optionally filtered by category.
        
        Args:
            category: If provided, only return rules of this category
            
        Returns:
            List of NeutroRule objects
        """
        if category is None:
            return self.rules
        return [r for r in self.rules if r.category == category]
    
    def get_active_rules(self) -> List[NeutroRule]:
        """Get only rules that have been activated at least once."""
        return [r for r in self.rules if r.activations > 0]
    
    def summary(self) -> Dict:
        """
        Get summary statistics of neutrosophic components.
        
        Returns:
            Dictionary with:
            - n_total: Total number of clauses
            - n_active: Number of active clauses
            - T_mean, T_std: Statistics for Truth
            - I_mean, I_std: Statistics for Indeterminacy
            - F_mean, F_std: Statistics for Falsity
            - n_certain: Count of certain rules
            - n_uncertain: Count of uncertain rules
            - n_contra: Count of contradictory rules
        """
        active = self.get_active_rules()
        
        if not active:
            return {
                'n_total': len(self.rules),
                'n_active': 0,
                'analyzed': self._analyzed
            }
        
        T_vals = [r.T for r in active]
        I_vals = [r.I for r in active]
        F_vals = [r.F for r in active]
        
        return {
            'n_total': len(self.rules),
            'n_active': len(active),
            'utilization': len(active) / len(self.rules) if self.rules else 0,
            'T_mean': float(np.mean(T_vals)),
            'T_std': float(np.std(T_vals)),
            'I_mean': float(np.mean(I_vals)),
            'I_std': float(np.std(I_vals)),
            'F_mean': float(np.mean(F_vals)),
            'F_std': float(np.std(F_vals)),
            'n_certain': len(self.get_rules(RuleCategory.CERTAIN)),
            'n_uncertain': len(self.get_rules(RuleCategory.UNCERTAIN)),
            'n_contra': len(self.get_rules(RuleCategory.CONTRADICTORY)),
            'analyzed': self._analyzed
        }
    
    def to_dataframe(self):
        """Convert rules to pandas DataFrame."""
        import pandas as pd
        return pd.DataFrame([r.to_dict() for r in self.rules])


class NeutroTsetlinMachine:
    """
    Neutrosophic Tsetlin Machine - Tsetlin Machine with built-in NML analysis.
    
    This class wraps a standard Tsetlin Machine and adds automatic
    neutrosophic analysis capabilities. After training, you can analyze
    the learned clauses to understand their reliability and uncertainty.
    
    The Tsetlin Machine is an interpretable ML algorithm that learns
    patterns as conjunctions of Boolean literals. Each clause votes for
    a class, and the final prediction is based on the vote sum.
    
    NeutroTsetlinMachine adds:
    - Automatic neutrosophic analysis of clause behavior
    - Rule classification (certain, uncertain, contradictory)
    - Uncertainty quantification via ⟨T, I, F⟩ values
    - Minimal overhead (~4% additional computation)
    
    Attributes:
        n_clauses: Number of clauses (rules) to learn
        T: Voting margin threshold
        s: Specificity parameter
        epochs: Training epochs
        analyzer: NMLAnalyzer instance after analysis
        
    Example:
        >>> ntm = NeutroTsetlinMachine(n_clauses=60, T=15, s=3.5)
        >>> ntm.fit(X_train, y_train, epochs=100)
        >>> ntm.analyze_neutrosophic(X_train, y_train)
        >>> 
        >>> # Get summary
        >>> summary = ntm.get_summary()
        >>> print(f"Certain rules: {summary['n_certain']}")
        >>> 
        >>> # Get specific rules
        >>> certain_rules = ntm.get_rules(RuleCategory.CERTAIN)
    
    Note:
        Requires pyTsetlinMachine: pip install pyTsetlinMachine
    """
    
    def __init__(self, n_clauses: int = 60, T: int = 15, s: float = 3.5,
                 random_state: Optional[int] = None):
        """
        Initialize Neutrosophic Tsetlin Machine.
        
        Args:
            n_clauses: Number of clauses (rules) to learn. More clauses
                      can capture more complex patterns but increase
                      computation.
            T: Voting margin threshold. Controls the granularity of
               the learning. Higher T means more precise learning.
            s: Specificity parameter. Controls the specificity of
               learned patterns. Higher s means more specific patterns.
            random_state: Random seed for reproducibility
        """
        self.n_clauses = n_clauses
        self.T = T
        self.s = s
        self.random_state = random_state
        self._tm = None
        self.analyzer: Optional[NMLAnalyzer] = None
        self._fitted = False
        self._n_features = None
    
    def _check_tsetlin_available(self):
        """Check if pyTsetlinMachine is available."""
        try:
            from pyTsetlinMachine.tm import MultiClassTsetlinMachine
            return True
        except ImportError:
            raise ImportError(
                "pyTsetlinMachine is required for NeutroTsetlinMachine. "
                "Install it with: pip install pyTsetlinMachine"
            )
    
    def fit(self, X: np.ndarray, y: np.ndarray, epochs: int = 100) -> 'NeutroTsetlinMachine':
        """
        Train the Tsetlin Machine on binary data.
        
        Args:
            X: Training features (n_samples, n_features). Must be binary
               (0 or 1 values). If not binary, use binarize() first.
            y: Training labels (n_samples,). Must be integer class labels.
            epochs: Number of training epochs
            
        Returns:
            self: Fitted NeutroTsetlinMachine
            
        Note:
            Input X must be binary (0/1). For continuous data, first
            binarize using a threshold or the binarize() method.
        """
        self._check_tsetlin_available()
        from pyTsetlinMachine.tm import MultiClassTsetlinMachine
        
        # Ensure binary input
        X = np.asarray(X, dtype=np.uint32)
        y = np.asarray(y, dtype=np.int32)
        
        self._n_features = X.shape[1]
        
        # Create and train Tsetlin Machine
        self._tm = MultiClassTsetlinMachine(
            number_of_clauses=self.n_clauses,
            T=self.T,
            s=self.s,
            max_included_features=self._n_features
        )
        
        self._tm.fit(X, y, epochs=epochs)
        self._fitted = True
        
        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class labels for samples.
        
        Args:
            X: Features (n_samples, n_features). Must be binary.
            
        Returns:
            Predicted class labels
        """
        if not self._fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        X = np.asarray(X, dtype=np.uint32)
        return self._tm.predict(X)
    
    def analyze_neutrosophic(self, X: np.ndarray, y: np.ndarray,
                             laplace_smoothing: bool = True) -> 'NeutroTsetlinMachine':
        """
        Perform neutrosophic analysis of learned clauses.
        
        This computes ⟨T, I, F⟩ values for each clause based on how
        reliably it predicts its target class across the given data.
        
        Args:
            X: Features to analyze (typically training data)
            y: Labels corresponding to X
            laplace_smoothing: Whether to apply Laplace smoothing
            
        Returns:
            self: With analyzer populated
        """
        if not self._fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        X = np.asarray(X, dtype=np.uint32)
        y = np.asarray(y, dtype=np.int32)
        
        self.analyzer = NMLAnalyzer(self._tm, self.n_clauses, laplace_smoothing)
        self.analyzer.analyze(X, y)
        
        return self
    
    def get_summary(self) -> Dict:
        """
        Get summary of neutrosophic analysis.
        
        Returns:
            Dictionary with T, I, F statistics and rule counts
        """
        if self.analyzer is None:
            raise ValueError("Analysis not performed. Call analyze_neutrosophic() first.")
        return self.analyzer.summary()
    
    def get_rules(self, category: Optional[RuleCategory] = None) -> List[NeutroRule]:
        """
        Get neutrosophic rules, optionally filtered by category.
        
        Args:
            category: If provided, only return rules of this category
            
        Returns:
            List of NeutroRule objects
        """
        if self.analyzer is None:
            raise ValueError("Analysis not performed. Call analyze_neutrosophic() first.")
        return self.analyzer.get_rules(category)
    
    def to_dataframe(self):
        """Convert rules to pandas DataFrame."""
        if self.analyzer is None:
            raise ValueError("Analysis not performed. Call analyze_neutrosophic() first.")
        return self.analyzer.to_dataframe()
    
    @staticmethod
    def binarize(X: np.ndarray, threshold: float = 0.5,
                 normalize: bool = True) -> np.ndarray:
        """
        Binarize continuous data for Tsetlin Machine input.
        
        Args:
            X: Continuous features (n_samples, n_features)
            threshold: Threshold for binarization (after normalization)
            normalize: Whether to normalize to [0,1] first
            
        Returns:
            Binary array (n_samples, n_features) with dtype uint32
        """
        X = np.asarray(X)
        
        if normalize:
            # Min-max normalization per feature
            X_min = X.min(axis=0, keepdims=True)
            X_max = X.max(axis=0, keepdims=True)
            X_range = X_max - X_min
            X_range[X_range == 0] = 1  # Avoid division by zero
            X = (X - X_min) / X_range
        
        return (X > threshold).astype(np.uint32)
