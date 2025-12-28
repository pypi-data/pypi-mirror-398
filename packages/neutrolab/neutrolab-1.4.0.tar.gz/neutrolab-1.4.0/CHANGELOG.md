# Changelog

All notable changes to NeutroLab will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.0] - 2025-12-17

### Added - Neutrosophic Stance Detection (NSD) Module
New module implementing the methodology from Alejo Machado et al. (2025) "Modeling Ambiguity in AI-Enhanced Learning" (IJNS Vol. 26, No. 04).

**New Classes:**
- `StanceCategory`: Enum for 5 stance categories (support, partial_support, neutral, partial_opposition, opposition)
- `RefinedNeutrosophicStance`: Dataclass representing ⟨T, PS, I, PO, F⟩ refined neutrosophic numbers
- `NeutrosophicStanceDetector`: Main detector using BART-large-MNLI zero-shot classification
- `StanceAggregator`: Aggregate multiple stances with weighted averaging

**New Functions:**
- `analyze_hypothesis()`: Convenience function for literature analysis
- `plot_stance_meter()`: Visualization of stance distribution

**Features:**
- Zero-shot classification via HuggingFace transformers
- Semantic Scholar API integration for paper retrieval
- Automatic normalization: T + PS + I + PO + F = 1
- Conversion to classic neutrosophic triplet (T, I, F)
- Polarity, certainty, and consensus metrics

**Mathematical Foundation:**
- Refined Neutrosophic Set: A = {x, T_A(x), I_PS(x), I(x), I_PO(x), F_A(x) | x ∈ X}
- Normalization constraint: T + PS + I + PO + F = 1
- Extended stance function: g_RN: X × Θ → [0,1]⁵

## [1.3.3] - 2025-12-16

### Improved (Addressing Reviewer Feedback)
- **K-Means Neutrosophication**: Clarified variable definitions (c_low, c_mid, c_high, σ_low, σ_mid, σ_high) with step-by-step algorithm description
- **NML Module**: Made Laplace smoothing parameter α explicit (default=1.0) with formula T_c = (TP + α) / (TP + FN + 2α)
- **IFAO**: Added complete axiomatization (A1-A5) with proof sketch deriving the operator form
- **Validation**: Added statistical significance tests (Wilcoxon signed-rank, p<0.001) and confidence intervals for N-fsQCA results

### Added
- **Background and Related Work** section covering existing neutrosophic software, aggregation operators, and ML uncertainty methods
- **Limitations Section** discussing K-Means sensitivity, IFAO scalability O(n²), N-fsQCA small-N issues
- Comparison with TOPSIS and VIKOR baselines for MCDM evaluation
- Monte Carlo validation protocol with data generation process specification

### Documentation
- Revised preprint paper addressing all reviewer concerns
- Mathematical derivations for IFAO from axioms
- Interpretation of T+I+F ≠ 1 in K-Means method

## [1.3.2] - 2025-12-16

### Added
- **Preprint Paper**: "NeutroLab: A Unified Library for Neutrosophic Learning, Configuration Analysis, and Decision-Making under Uncertainty"
- Complete documentation of all four modules with mathematical foundations
- Cross-domain analogies (Quantum Mechanics, Thermodynamics, Finance, Information Theory)

### Updated
- Author affiliation: Universidad de Guayaquil, Ecuador
- Contact email: mleyvaz@gmail.com
- Package description aligned with preprint paper title

### Documentation
- Comprehensive preprint covering:
  - 5 Neutrosophication methods (K-Means achieving true T,I,F independence)
  - N-fsQCA v2.0 with 11 causal archetypes
  - NML for Tsetlin Machines with ~4% overhead
  - IFAO with formal axiomatization

## [1.3.1] - 2025-12-16

### Enhanced
- **IFAO Formal Mathematical Definition**
  - Operator: Ω_IFAO: [0,1]ⁿ × Δⁿ → N₁
  - Compact form: Ω_IFAO(v,w) = (P·(1-C), C, (1-P)·(1-C))
  - Contradiction measure based on Weighted Gini Mean Difference
  
- **Complete Axiomatization**
  - A1. Neutrosophic Closure: T + I + F = 1
  - A2. Unanimity Idempotence: If vᵢ = c ∀i → Ω(v,w) = (c, 0, 1-c)
  - A3. Conflict Monotonicity: Var(v') > Var(v) → I' ≥ I
  - A4. Hierarchical Dependence: ∂T/∂I < 0, ∂F/∂I < 0
  - A5. Conditional Symmetry: Permutation-invariant with uniform weights

- **Cross-Domain Analogies Documentation**
  - Quantum Mechanics (Heisenberg): Δx·Δp ≥ ℏ/2
  - Thermodynamics (Carnot): η = 1 - Tc/Th ≈ (1-I)
  - Finance (Markowitz): Efficient Frontier ≈ Neutrosophic Simplex
  - Information Theory (Shannon): Entropy as primary quantity

- **Updated Q1 Paper** with formal operator definition and interdisciplinary foundations

## [1.3.0] - 2025-12-15

### Added
- **Neutrosophic Aggregation** module (`neutrolab.aggregation`) - Indeterminacy as Ontological Foundation
  - `IndeterminacyFirstAggregator`: MCDM with conflict-first paradigm
  - `MCDMEvaluator`: Batch evaluation and ranking of alternatives
  - `AggregationResult`: Complete result with ⟨T, I, F⟩ triplet
  - `DecisionCategory`: Decision classification (STRONG_APPROVE, APPROVE, REVIEW, REJECT, INDETERMINATE)
  - `ModeloIndeterminacionBase`: Spanish API compatibility
  - Mathematical model: I = C (Contradiction), T = P×(1-I), F = (1-P)×(1-I)
  - Property: T + I + F = 1
- Q1 Paper: "Indeterminacy as the Ontological Foundation of Truth"

### Key Innovation
- Indeterminacy (I) is the PRIMARY quantity derived from conflict
- Truth (T) and Falsity (F) are DERIVED as residuals in the resolvable space (1-I)
- Ontological hierarchy: Conflict → Indeterminacy → (Truth, Falsity)

## [1.2.0] - 2025-12-15

### Added
- **Neutrosophic Tsetlin Machine (NML)** module (`neutrolab.tsetlin`)
  - `NeutroTsetlinMachine`: Wrapper for Tsetlin Machine with neutrosophic analysis
  - `NMLAnalyzer`: Post-hoc neutrosophic analysis of learned clauses
  - `NeutroRule`: Dataclass for neutrosophic rule representation
  - `RuleCategory`: Enum for rule classification (CERTAIN, UNCERTAIN, CONTRADICTORY, INACTIVE, NORMAL)
  - Laplace smoothing for stable T, I, F estimates
  - Rule classification based on indeterminacy thresholds
  - ~4% computational overhead for neutrosophic analysis
- Position paper: "NeutroLab: A Unified Library for Neutrosophic Learning, Configuration Analysis, and Logical Machines"

### Changed
- Updated package description to include NML module
- Enhanced documentation with NML usage examples

### Dependencies
- Optional: pyTsetlinMachine for NeutroTsetlinMachine functionality

## [1.1.0] - 2025-12-14

### Added
- **N-fsQCA v2.0** module (`neutrolab.fsqca`) - Neutrosophic Fuzzy-Set QCA
  - Variance-based Indeterminacy formula (superior to tent-function)
  - Bootstrap confidence intervals for T, I, F
  - 11 causal archetypes classification
  - Comparison with traditional fsQCA
  - Monte Carlo validation: 98% Jaccard similarity

## [1.0.0] - 2024-12-10

### Added
- Initial release of NeutroLab library
- Five neutrosophication methods as described in the paper:
  - **KMeansNeutrosophic**: K-Means clustering with sigmoid membership functions (Proposed)
    - Achieves TRUE independence of T, I, F components
    - Equations 2, 3, 4 from paper
  - **ParabolicNeutrosophic**: Classical parabolic approach (Equation 5)
  - **ThresholdNeutrosophic**: Threshold distance method (Equation 7)
  - **KDENeutrosophic**: Kernel density estimation approach (Equations 8-11)
  - **FuzzyNeutrosophic**: Fuzzy membership with triangular functions (Equation 12)
- Utility functions:
  - `normalize_data()`: Min-Max normalization (Equation 1)
  - `validate_input()`: Input validation and reshaping
  - `compute_statistics()`: Statistical analysis including metrics from paper
  - `compare_methods()`: Method comparison utility
  - `compute_correlation()`: Correlation between indeterminacy distributions
  - `compute_distance()`: Distance metrics between neutrosophic sets
  - `compute_tf_consistency()`: T+F Consistency metric (Equation 13)
- Comprehensive test suite verifying conformity with paper formulas
- Full type hints support
- MIT License

### Paper Reference
Based on: "A Comparative Analysis of Data-Driven and Model-Based Neutrosophication 
Methods: Advancing True Neutrosophic Logic in Medical Data Transformation"

Authors: Leyva-Vázquez, M. Y., Cevallos-Torres, L., Mar Cornelio, O., & Smarandache, F.

## [Planned] Future Releases

### [2.0.0] - Planned
- Interval-Valued Neutrosophic Sets (IVNS)
- Neutrosophic Cognitive Maps
- Multi-criteria decision making tools
- GPU acceleration for large-scale applications
- Integration with deep learning frameworks
