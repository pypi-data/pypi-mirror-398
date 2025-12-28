"""
NeutroLab: A Unified Library for Neutrosophic Learning, Configuration Analysis, and Decision-Making under Uncertainty
=====================================================================================================================

A comprehensive Python library implementing neutrosophic set theory methods for
transforming crisp data into neutrosophic values, with extensible architecture
for advanced neutrosophic computing.

Current Modules:

1. Neutrosophication Methods:
   - K-Means Clustering with Sigmoid Membership Functions (Data-driven)
   - Parabolic Method (Model-based)
   - Threshold Distance Method (Model-based)
   - Kernel Density Estimation (KDE) (Density-based)
   - Fuzzy Membership with Triangular Functions (Model-based)

2. N-fsQCA v2.0 - Neutrosophic Fuzzy-Set Qualitative Comparative Analysis:
   - Variance-based Indeterminacy calculation
   - Bootstrap confidence intervals for T, I, F
   - 11 causal archetypes classification
   - Comparison with traditional fsQCA

3. NML - Neutrosophic Meta-Learning for Tsetlin Machines:
   - Post-hoc neutrosophic analysis of learned rules
   - Uncertainty quantification via ⟨T, I, F⟩
   - Rule classification (certain, uncertain, contradictory)
   - Minimal computational overhead (~4%)

4. IFAO - Indeterminacy-First Aggregation Operator:
   - Multi-criteria decision-making (MCDM) with conflict-first paradigm
   - Indeterminacy (I) as PRIMARY from contradiction
   - Truth (T) and Falsity (F) derived as residuals
   - Formal axiomatization and cross-domain analogies

5. NSD - Neutrosophic Stance Detection (NEW):
   - Refined Neutrosophic Numbers ⟨T, PS, I, PO, F⟩
   - Zero-shot classification using BART-large-MNLI
   - Scientific literature analysis via Semantic Scholar API
   - Stance aggregation across multiple papers

Authors:
    Maikel Yelandi Leyva-Vázquez (mleyvaz@gmail.com) - Universidad de Guayaquil
    Florentin Smarandache - University of New Mexico

Version: 1.4.0
License: MIT
PyPI: https://pypi.org/project/neutrolab/

References:
    [1] Smarandache, F. (1998). Neutrosophy/neutrosophic probability, set, and logic.
    [2] Smarandache, F. (2014). Introduction to Neutrosophic Statistics.
    [3] Wang, H., et al. (2010). Single valued neutrosophic sets.
    [4] Leyva-Vázquez, M., & Smarandache, F. (2025). From Crisp to Neutrosophic v2.0.
    [5] Granmo, O. C. (2018). The Tsetlin Machine.
    [6] Leyva-Vázquez, M., & Smarandache, F. (2025). Indeterminacy as Foundation of Truth.
    [7] Alejo Machado et al. (2025). Modeling Ambiguity in AI-Enhanced Learning. IJNS.
"""

__version__ = "1.4.0"
__author__ = "Maikel Yelandi Leyva-Vázquez"
__email__ = "mleyvaz@gmail.com"
__license__ = "MIT"

# Neutrosophication Methods
from .methods.base import NeutrosophicMethod
from .methods.kmeans import KMeansNeutrosophic
from .methods.parabolic import ParabolicNeutrosophic
from .methods.threshold import ThresholdNeutrosophic
from .methods.kde import KDENeutrosophic
from .methods.fuzzy import FuzzyNeutrosophic

# Utility Functions
from .utils import (
    normalize_data,
    validate_input,
    compute_statistics,
    compare_methods,
    compute_correlation,
    compute_distance,
    compute_tf_consistency
)

# N-fsQCA v2.0 Module
from .fsqca import (
    CausalArchetype,
    NeutrosophicTIF,
    ConfigurationResult,
    NfsqcaCalculator,
    ArchetypeClassifier,
    NfsqcaEngine,
    compare_with_traditional
)

# Neutrosophic Tsetlin Machine (NML) Module
from .tsetlin import (
    RuleCategory,
    NeutroRule,
    NMLAnalyzer,
    NeutroTsetlinMachine
)

# Neutrosophic Aggregation Module - Indeterminacy First
from .aggregation import (
    DecisionCategory,
    AggregationResult,
    IndeterminacyFirstAggregator,
    MCDMEvaluator,
    batch_evaluate,
    ModeloIndeterminacionBase
)

# Neutrosophic Stance Detection (NSD) Module
from .stance import (
    StanceCategory,
    RefinedNeutrosophicStance,
    NeutrosophicStanceDetector,
    StanceAggregator,
    analyze_hypothesis,
    plot_stance_meter
)

__all__ = [
    # Base class
    'NeutrosophicMethod',
    # Neutrosophication methods
    'KMeansNeutrosophic',
    'ParabolicNeutrosophic',
    'ThresholdNeutrosophic',
    'KDENeutrosophic',
    'FuzzyNeutrosophic',
    # Utilities
    'normalize_data',
    'validate_input',
    'compute_statistics',
    'compare_methods',
    'compute_correlation',
    'compute_distance',
    'compute_tf_consistency',
    # N-fsQCA v2.0
    'CausalArchetype',
    'NeutrosophicTIF',
    'ConfigurationResult',
    'NfsqcaCalculator',
    'ArchetypeClassifier',
    'NfsqcaEngine',
    'compare_with_traditional',
    # Neutrosophic Tsetlin Machine (NML)
    'RuleCategory',
    'NeutroRule',
    'NMLAnalyzer',
    'NeutroTsetlinMachine',
    # Neutrosophic Aggregation - Indeterminacy First
    'DecisionCategory',
    'AggregationResult',
    'IndeterminacyFirstAggregator',
    'MCDMEvaluator',
    'batch_evaluate',
    'ModeloIndeterminacionBase',
    # Neutrosophic Stance Detection (NSD)
    'StanceCategory',
    'RefinedNeutrosophicStance',
    'NeutrosophicStanceDetector',
    'StanceAggregator',
    'analyze_hypothesis',
    'plot_stance_meter',
]
