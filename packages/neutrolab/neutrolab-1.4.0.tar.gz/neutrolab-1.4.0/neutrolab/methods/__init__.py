"""
Neutrosophication Methods Module
================================

This module contains all neutrosophication methods implemented in NeutroLab.
Each method transforms normalized input values x ∈ [0, 1] into neutrosophic
triplets (T, I, F) where:

- T (Truth): Degree of truth/membership
- I (Indeterminacy): Degree of indeterminacy/uncertainty  
- F (Falsity): Degree of falsity/non-membership

All components map to [0, 1].
"""

from .base import NeutrosophicMethod
from .kmeans import KMeansNeutrosophic
from .parabolic import ParabolicNeutrosophic
from .threshold import ThresholdNeutrosophic
from .kde import KDENeutrosophic
from .fuzzy import FuzzyNeutrosophic

__all__ = [
    'NeutrosophicMethod',
    'KMeansNeutrosophic',
    'ParabolicNeutrosophic',
    'ThresholdNeutrosophic',
    'KDENeutrosophic',
    'FuzzyNeutrosophic',
]
