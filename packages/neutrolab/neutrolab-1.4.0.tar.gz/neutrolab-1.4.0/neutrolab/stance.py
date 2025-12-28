"""
Neutrosophic Stance Detection (NSD) Module
==========================================

This module implements the Neutrosophic Stance Detection framework for analyzing
scientific literature and producing Refined Neutrosophic Numbers (T, PS, I, PO, F).

Based on the methodology from:
"Modeling Ambiguity in AI-Enhanced Learning: A Neutrosophic Approach to 
Stance Detection and Causal Evaluation" - Alejo Machado et al. (2025)
International Journal of Neutrosophic Science (IJNS), Vol. 26, No. 04

Mathematical Foundation:
------------------------
The Refined Neutrosophic Set A is defined as:
    A = {x, T_A(x), I_PS(x), I(x), I_PO(x), F_A(x) | x ∈ X}

Where:
    - T_A(x): Complete support (Truth)
    - I_PS(x): Partial support
    - I(x): Neutrality/Indeterminacy
    - I_PO(x): Partial opposition
    - F_A(x): Complete opposition (Falsity)

Normalization constraint:
    T_A(x) + I_PS(x) + I(x) + I_PO(x) + F_A(x) = 1

This ensures the total evaluative mass is distributed across all five
subcomponents, preserving internal consistency while enabling fine-grained
differentiation between levels of support and opposition.

The classical neutrosophic stance detection function:
    g_N: X × Θ → [0,1]³
    g_N(x, θ) = (T(x,θ), I(x,θ), F(x,θ))

Is extended to refined neutrosophic:
    g_RN: X × Θ → [0,1]⁵
    g_RN(x, θ) = (T, PS, I, PO, F)

Example:
--------
>>> from neutrolab.stance import NeutrosophicStanceDetector
>>> 
>>> detector = NeutrosophicStanceDetector()
>>> hypothesis = "AI tutoring improves student performance"
>>> 
>>> # Analyze a single text
>>> result = detector.analyze_text(
...     "Studies show AI tutors enhance learning outcomes significantly",
...     hypothesis
... )
>>> print(f"Neutrosophic Stance: {result}")
>>> 
>>> # Search and analyze literature
>>> results = detector.analyze_literature(hypothesis, max_papers=10)
>>> print(f"Aggregated: T={results['aggregated']['T']:.3f}")

References:
-----------
[1] Alejo Machado et al. (2025). Modeling Ambiguity in AI-Enhanced Learning.
    International Journal of Neutrosophic Science, 26(04), 298-308.
[2] Smarandache, F. (1998). Neutrosophy: Neutrosophic Probability, Set, and Logic.
[3] Lewis et al. (2019). BART: Denoising sequence-to-sequence pre-training.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass, field
from enum import Enum
import warnings

__all__ = [
    'StanceCategory',
    'RefinedNeutrosophicStance',
    'NeutrosophicStanceDetector',
    'StanceAggregator',
    'analyze_hypothesis'
]


class StanceCategory(Enum):
    """
    Stance categories for refined neutrosophic evaluation.
    
    Maps to the five-component refined neutrosophic set:
    - SUPPORT (T): Complete agreement/truth
    - PARTIAL_SUPPORT (PS): Conditional or qualified support
    - NEUTRAL (I): Indeterminacy, ambiguity, or lack of clear stance
    - PARTIAL_OPPOSITION (PO): Conditional or qualified opposition
    - OPPOSITION (F): Complete disagreement/falsity
    """
    SUPPORT = "support"
    PARTIAL_SUPPORT = "partial support"
    NEUTRAL = "neutral"
    PARTIAL_OPPOSITION = "partial opposition"
    OPPOSITION = "opposition"
    
    @classmethod
    def get_labels(cls) -> List[str]:
        """Return list of stance labels for classification."""
        return [c.value for c in cls]


@dataclass
class RefinedNeutrosophicStance:
    """
    Refined Neutrosophic Stance representation.
    
    Represents a stance as a 5-tuple (T, PS, I, PO, F) where:
    - T: Truth/Support degree ∈ [0,1]
    - PS: Partial Support degree ∈ [0,1]
    - I: Indeterminacy/Neutral degree ∈ [0,1]
    - PO: Partial Opposition degree ∈ [0,1]
    - F: Falsity/Opposition degree ∈ [0,1]
    
    Constraint: T + PS + I + PO + F = 1 (normalized)
    
    Attributes:
        T: Truth/complete support degree
        PS: Partial support degree
        I: Indeterminacy/neutral degree
        PO: Partial opposition degree
        F: Falsity/complete opposition degree
        text: Original text analyzed (optional)
        hypothesis: Hypothesis evaluated against (optional)
        confidence: Overall confidence in the classification
    """
    T: float
    PS: float
    I: float
    PO: float
    F: float
    text: Optional[str] = None
    hypothesis: Optional[str] = None
    confidence: float = 1.0
    
    def __post_init__(self):
        """Validate and normalize the neutrosophic values."""
        # Ensure non-negative
        self.T = max(0.0, self.T)
        self.PS = max(0.0, self.PS)
        self.I = max(0.0, self.I)
        self.PO = max(0.0, self.PO)
        self.F = max(0.0, self.F)
        
        # Normalize to sum to 1
        total = self.T + self.PS + self.I + self.PO + self.F
        if total > 0:
            self.T /= total
            self.PS /= total
            self.I /= total
            self.PO /= total
            self.F /= total
        else:
            # Default to maximum indeterminacy
            self.I = 1.0
    
    @property
    def support_degree(self) -> float:
        """Total support = T + PS."""
        return self.T + self.PS
    
    @property
    def opposition_degree(self) -> float:
        """Total opposition = PO + F."""
        return self.PO + self.F
    
    @property
    def certainty(self) -> float:
        """Certainty = 1 - I (how certain the stance is)."""
        return 1.0 - self.I
    
    @property
    def polarity(self) -> float:
        """
        Polarity score ∈ [-1, 1].
        Positive = support dominant, Negative = opposition dominant.
        """
        return self.support_degree - self.opposition_degree
    
    @property
    def dominant_stance(self) -> StanceCategory:
        """Return the dominant stance category."""
        values = {
            StanceCategory.SUPPORT: self.T,
            StanceCategory.PARTIAL_SUPPORT: self.PS,
            StanceCategory.NEUTRAL: self.I,
            StanceCategory.PARTIAL_OPPOSITION: self.PO,
            StanceCategory.OPPOSITION: self.F
        }
        return max(values, key=values.get)
    
    def to_classic_neutrosophic(self) -> Tuple[float, float, float]:
        """
        Convert to classic neutrosophic triplet (T, I, F).
        
        Aggregates:
        - T_classic = T + PS (all support)
        - I_classic = I (indeterminacy)
        - F_classic = PO + F (all opposition)
        
        Returns:
            Tuple of (T, I, F) classic neutrosophic values
        """
        return (self.support_degree, self.I, self.opposition_degree)
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            'T': self.T,
            'PS': self.PS,
            'I': self.I,
            'PO': self.PO,
            'F': self.F,
            'support_degree': self.support_degree,
            'opposition_degree': self.opposition_degree,
            'polarity': self.polarity,
            'certainty': self.certainty,
            'confidence': self.confidence
        }
    
    def to_tuple(self) -> Tuple[float, float, float, float, float]:
        """Return as tuple (T, PS, I, PO, F)."""
        return (self.T, self.PS, self.I, self.PO, self.F)
    
    def __repr__(self) -> str:
        return f"RefinedNeutrosophicStance(T={self.T:.3f}, PS={self.PS:.3f}, I={self.I:.3f}, PO={self.PO:.3f}, F={self.F:.3f})"
    
    def __str__(self) -> str:
        return f"⟨T={self.T:.3f}, PS={self.PS:.3f}, I={self.I:.3f}, PO={self.PO:.3f}, F={self.F:.3f}⟩"


class NeutrosophicStanceDetector:
    """
    Neutrosophic Stance Detector for scientific literature analysis.
    
    Uses zero-shot classification (BART-large-MNLI) to detect stance
    and converts results to Refined Neutrosophic Numbers.
    
    The detector implements the methodology from Alejo Machado et al. (2025):
    1. Retrieve papers from Semantic Scholar API
    2. Classify stance using zero-shot learning
    3. Normalize confidence scores to neutrosophic values
    4. Aggregate results across corpus
    
    Parameters:
        model_name: HuggingFace model for zero-shot classification
        semantic_scholar_api: Base URL for Semantic Scholar API
        use_gpu: Whether to use GPU acceleration
        
    Example:
        >>> detector = NeutrosophicStanceDetector()
        >>> result = detector.analyze_text(
        ...     "AI significantly improves learning outcomes",
        ...     "AI improves education"
        ... )
        >>> print(result)  # ⟨T=0.15, PS=0.72, I=0.08, PO=0.05, F=0.00⟩
    """
    
    DEFAULT_MODEL = "facebook/bart-large-mnli"
    SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1/paper/search"
    
    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        use_gpu: bool = False,
        cache_dir: Optional[str] = None
    ):
        """
        Initialize the Neutrosophic Stance Detector.
        
        Args:
            model_name: HuggingFace model name for zero-shot classification
            use_gpu: Whether to use GPU (requires CUDA)
            cache_dir: Directory to cache the model
        """
        self.model_name = model_name
        self.use_gpu = use_gpu
        self.cache_dir = cache_dir
        self._classifier = None
        self._labels = StanceCategory.get_labels()
    
    @property
    def classifier(self):
        """Lazy-load the classifier pipeline."""
        if self._classifier is None:
            try:
                from transformers import pipeline
                device = 0 if self.use_gpu else -1
                self._classifier = pipeline(
                    "zero-shot-classification",
                    model=self.model_name,
                    device=device
                )
            except ImportError:
                raise ImportError(
                    "transformers library required. Install with: "
                    "pip install transformers torch"
                )
        return self._classifier
    
    def analyze_text(
        self,
        text: str,
        hypothesis: str,
        return_raw: bool = False
    ) -> Union[RefinedNeutrosophicStance, Dict]:
        """
        Analyze a single text against a hypothesis.
        
        Uses zero-shot classification to determine stance, then
        normalizes the confidence scores to refined neutrosophic values.
        
        Args:
            text: Text to analyze (e.g., paper abstract)
            hypothesis: Hypothesis/claim to evaluate stance against
            return_raw: If True, return raw classifier output
            
        Returns:
            RefinedNeutrosophicStance object (or dict if return_raw=True)
        """
        if not text or not text.strip():
            return RefinedNeutrosophicStance(
                T=0, PS=0, I=1, PO=0, F=0,
                text=text, hypothesis=hypothesis, confidence=0
            )
        
        # Run zero-shot classification
        result = self.classifier(text, self._labels)
        
        if return_raw:
            return result
        
        # Extract scores for each label
        label_scores = dict(zip(result['labels'], result['scores']))
        
        # Map to neutrosophic components
        T = label_scores.get('support', 0)
        PS = label_scores.get('partial support', 0)
        I = label_scores.get('neutral', 0)
        PO = label_scores.get('partial opposition', 0)
        F = label_scores.get('opposition', 0)
        
        # Overall confidence is the max score
        confidence = max(result['scores'])
        
        return RefinedNeutrosophicStance(
            T=T, PS=PS, I=I, PO=PO, F=F,
            text=text[:200] + "..." if len(text) > 200 else text,
            hypothesis=hypothesis,
            confidence=confidence
        )
    
    def search_papers(
        self,
        query: str,
        max_papers: int = 15,
        fields: str = "title,abstract"
    ) -> List[Dict]:
        """
        Search for papers using Semantic Scholar API.
        
        Args:
            query: Search query string
            max_papers: Maximum number of papers to retrieve
            fields: Fields to retrieve (comma-separated)
            
        Returns:
            List of paper dictionaries with title and abstract
        """
        try:
            import requests
        except ImportError:
            raise ImportError("requests library required. Install with: pip install requests")
        
        url = f"{self.SEMANTIC_SCHOLAR_API}?query={query}&limit={max_papers}&fields={fields}"
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])
        except Exception as e:
            warnings.warn(f"Error fetching papers: {e}")
            return []
    
    def analyze_literature(
        self,
        hypothesis: str,
        max_papers: int = 15,
        search_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze scientific literature stance on a hypothesis.
        
        Searches for papers related to the hypothesis, classifies each,
        and aggregates results into a corpus-level neutrosophic evaluation.
        
        Args:
            hypothesis: The hypothesis/claim to evaluate
            max_papers: Maximum number of papers to analyze
            search_query: Custom search query (defaults to hypothesis)
            
        Returns:
            Dictionary containing:
            - papers: List of individual paper analyses
            - aggregated: Aggregated RefinedNeutrosophicStance
            - statistics: Summary statistics
        """
        query = search_query or hypothesis
        papers = self.search_papers(query, max_papers)
        
        results = []
        for paper in papers:
            title = paper.get("title", "")
            abstract = paper.get("abstract", "")
            
            if not abstract:
                continue
            
            stance = self.analyze_text(abstract, hypothesis)
            results.append({
                'title': title,
                'stance': stance,
                'abstract_preview': abstract[:150] + "..." if len(abstract) > 150 else abstract
            })
        
        # Aggregate results
        if results:
            aggregated = StanceAggregator.aggregate([r['stance'] for r in results])
        else:
            aggregated = RefinedNeutrosophicStance(T=0, PS=0, I=1, PO=0, F=0)
        
        # Compute statistics
        stats = self._compute_statistics(results)
        
        return {
            'hypothesis': hypothesis,
            'papers_analyzed': len(results),
            'papers': results,
            'aggregated': aggregated,
            'statistics': stats
        }
    
    def _compute_statistics(self, results: List[Dict]) -> Dict:
        """Compute summary statistics from results."""
        if not results:
            return {'dominant_stance': 'indeterminate', 'consensus': 0}
        
        stances = [r['stance'] for r in results]
        
        # Count dominant stances
        stance_counts = {}
        for s in stances:
            dominant = s.dominant_stance.value
            stance_counts[dominant] = stance_counts.get(dominant, 0) + 1
        
        # Most common stance
        dominant = max(stance_counts, key=stance_counts.get)
        
        # Consensus measure (how much agreement)
        consensus = stance_counts[dominant] / len(stances)
        
        # Average values
        avg_T = np.mean([s.T for s in stances])
        avg_PS = np.mean([s.PS for s in stances])
        avg_I = np.mean([s.I for s in stances])
        avg_PO = np.mean([s.PO for s in stances])
        avg_F = np.mean([s.F for s in stances])
        
        return {
            'dominant_stance': dominant,
            'consensus': consensus,
            'stance_distribution': stance_counts,
            'averages': {
                'T': avg_T, 'PS': avg_PS, 'I': avg_I, 'PO': avg_PO, 'F': avg_F
            }
        }


class StanceAggregator:
    """
    Aggregator for combining multiple neutrosophic stances.
    
    Provides methods for aggregating stance evaluations across
    multiple texts/papers into a single neutrosophic value.
    """
    
    @staticmethod
    def aggregate(
        stances: List[RefinedNeutrosophicStance],
        weights: Optional[List[float]] = None,
        method: str = 'weighted_average'
    ) -> RefinedNeutrosophicStance:
        """
        Aggregate multiple stances into a single value.
        
        Args:
            stances: List of RefinedNeutrosophicStance objects
            weights: Optional weights for each stance (defaults to equal)
            method: Aggregation method ('weighted_average', 'max', 'min')
            
        Returns:
            Aggregated RefinedNeutrosophicStance
        """
        if not stances:
            return RefinedNeutrosophicStance(T=0, PS=0, I=1, PO=0, F=0)
        
        if weights is None:
            weights = [1.0] * len(stances)
        
        weights = np.array(weights)
        weights = weights / weights.sum()  # Normalize weights
        
        if method == 'weighted_average':
            T = sum(w * s.T for w, s in zip(weights, stances))
            PS = sum(w * s.PS for w, s in zip(weights, stances))
            I = sum(w * s.I for w, s in zip(weights, stances))
            PO = sum(w * s.PO for w, s in zip(weights, stances))
            F = sum(w * s.F for w, s in zip(weights, stances))
        elif method == 'max':
            T = max(s.T for s in stances)
            PS = max(s.PS for s in stances)
            I = max(s.I for s in stances)
            PO = max(s.PO for s in stances)
            F = max(s.F for s in stances)
        elif method == 'min':
            T = min(s.T for s in stances)
            PS = min(s.PS for s in stances)
            I = min(s.I for s in stances)
            PO = min(s.PO for s in stances)
            F = min(s.F for s in stances)
        else:
            raise ValueError(f"Unknown aggregation method: {method}")
        
        return RefinedNeutrosophicStance(T=T, PS=PS, I=I, PO=PO, F=F)
    
    @staticmethod
    def compute_consensus(stances: List[RefinedNeutrosophicStance]) -> float:
        """
        Compute consensus measure across stances.
        
        Returns value in [0, 1] where 1 = perfect agreement.
        Uses variance of polarity as disagreement measure.
        """
        if len(stances) < 2:
            return 1.0
        
        polarities = [s.polarity for s in stances]
        variance = np.var(polarities)
        
        # Max possible variance is 1 (for polarity in [-1, 1])
        consensus = 1.0 - min(variance, 1.0)
        return consensus


def analyze_hypothesis(
    hypothesis: str,
    max_papers: int = 15,
    return_plot_data: bool = False
) -> Union[RefinedNeutrosophicStance, Tuple[RefinedNeutrosophicStance, Dict]]:
    """
    Convenience function to analyze a hypothesis against literature.
    
    Args:
        hypothesis: The hypothesis to evaluate
        max_papers: Maximum papers to analyze
        return_plot_data: If True, return data for visualization
        
    Returns:
        Aggregated RefinedNeutrosophicStance (and plot data if requested)
        
    Example:
        >>> result = analyze_hypothesis(
        ...     "AI tutoring improves academic performance",
        ...     max_papers=10
        ... )
        >>> print(f"Support: {result.support_degree:.1%}")
        >>> print(f"Opposition: {result.opposition_degree:.1%}")
    """
    detector = NeutrosophicStanceDetector()
    results = detector.analyze_literature(hypothesis, max_papers)
    
    if return_plot_data:
        plot_data = {
            'categories': ['Support', 'Partial Support', 'Neutral', 
                          'Partial Opposition', 'Opposition'],
            'values': [
                results['aggregated'].T * 100,
                results['aggregated'].PS * 100,
                results['aggregated'].I * 100,
                results['aggregated'].PO * 100,
                results['aggregated'].F * 100
            ],
            'colors': ['#2ecc71', '#f1c40f', '#e67e22', '#e74c3c', '#d35400']
        }
        return results['aggregated'], plot_data
    
    return results['aggregated']


def plot_stance_meter(
    stance: RefinedNeutrosophicStance,
    title: str = "Neutrosophic Stance Analysis",
    figsize: Tuple[int, int] = (10, 3)
) -> None:
    """
    Create a "Consensus Meter" style visualization.
    
    Args:
        stance: RefinedNeutrosophicStance to visualize
        title: Plot title
        figsize: Figure size
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        raise ImportError("matplotlib required. Install with: pip install matplotlib")
    
    categories = ['Support (T)', 'Partial Support (PS)', 'Neutral (I)', 
                  'Partial Opposition (PO)', 'Opposition (F)']
    colors = ['#2ecc71', '#82e0aa', '#f5b041', '#e74c3c', '#943126']
    values = [stance.T * 100, stance.PS * 100, stance.I * 100, 
              stance.PO * 100, stance.F * 100]
    
    fig, ax = plt.subplots(figsize=figsize)
    bars = ax.barh(categories, values, color=colors, edgecolor='black', height=0.6)
    
    # Add percentage labels
    for bar, value in zip(bars, values):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                f'{value:.1f}%', va='center', fontsize=10, fontweight='bold')
    
    ax.set_title(title, fontsize=12, fontweight='bold')
    ax.set_xlabel('Percentage', fontsize=10)
    ax.set_xlim(0, 110)
    ax.invert_yaxis()
    
    # Add neutrosophic notation
    notation = f"⟨T={stance.T:.3f}, PS={stance.PS:.3f}, I={stance.I:.3f}, PO={stance.PO:.3f}, F={stance.F:.3f}⟩"
    ax.text(0.5, -0.15, notation, transform=ax.transAxes, ha='center', 
            fontsize=9, style='italic')
    
    plt.tight_layout()
    return fig


# Alias for backward compatibility
NSD = NeutrosophicStanceDetector
