"""
Fuzzy Membership Neutrosophication Method (Classical)

This module implements a classical fuzzy logic approach using triangular
membership functions for neutrosophication.

Mathematical Formulation (from paper Section 2.2.5):
----------------------------------------------------
Triangular membership function (Eq. 12):
    μ(x) = {
        0                  if x ≤ a or x ≥ c
        (x - a)/(b - a)    if a < x ≤ b
        (c - x)/(c - b)    if b < x < c
    }

Predefined Fuzzy Sets:
    Low:    (a_L, b_L, c_L) = (-0.5, 0.0, 0.5)
    Medium: (a_M, b_M, c_M) = (0.25, 0.5, 0.75)
    High:   (a_H, b_H, c_H) = (0.5, 1.0, 1.5)

Neutrosophic Components:
    T(x) = x
    I(x) = 1 - max(μ_L(x), μ_M(x), μ_H(x))
    F(x) = 1 - x

Key Properties:
- Model-based with predefined fuzzy sets
- Highly interpretable (linguistic transparency)
- Forced complementarity: T + F = 1 (fuzzy-like constraint)
- T+I+F sum typically > 1 (mean sum ≈ 1.349 in experiments)
- Best for: Interpretability-focused expert systems

References:
    Zadeh, L. A. (1965). Fuzzy sets. Information and Control, 8(3), 338-353.
"""

import numpy as np
from typing import Tuple, Optional, Dict, List
from .base import NeutrosophicMethod


def validate_input(X: np.ndarray, name: str = "input") -> np.ndarray:
    """Validate and reshape input data."""
    X = np.asarray(X, dtype=np.float64)
    
    if X.ndim == 2:
        if X.shape[1] != 1:
            raise ValueError(f"{name} must have shape (n_samples,) or (n_samples, 1)")
        X = X.flatten()
    elif X.ndim != 1:
        raise ValueError(f"{name} must be 1D or 2D array")
    
    if np.any(np.isnan(X)):
        raise ValueError(f"{name} contains NaN values")
    
    if np.any(np.isinf(X)):
        raise ValueError(f"{name} contains infinite values")
    
    return X


class FuzzyNeutrosophic(NeutrosophicMethod):
    """
    Fuzzy Membership Neutrosophication Method (Classical).
    
    This classical method uses triangular membership functions to compute
    neutrosophic values based on fuzzy set theory.
    
    Uses predefined fuzzy sets for Low, Medium, and High linguistic variables
    as specified in the paper.
    
    NOTE: This method enforces T + F = 1 (fuzzy-like complementarity),
    which is NOT true neutrosophic independence.
    
    Attributes
    ----------
    params_low : tuple
        Parameters for Low fuzzy set (a, b, c) = (-0.5, 0.0, 0.5)
    params_medium : tuple
        Parameters for Medium fuzzy set (a, b, c) = (0.25, 0.5, 0.75)
    params_high : tuple
        Parameters for High fuzzy set (a, b, c) = (0.5, 1.0, 1.5)
        
    Examples
    --------
    >>> import numpy as np
    >>> from neutrolab import FuzzyNeutrosophic
    >>> 
    >>> data = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
    >>> method = FuzzyNeutrosophic()
    >>> T, I, F = method.fit_transform(data)
    >>> 
    >>> # T = x, F = 1-x
    >>> print(T)  # [0.   0.25 0.5  0.75 1.  ]
    >>> print(F)  # [1.   0.75 0.5  0.25 0.  ]
    """
    
    # Default parameters from paper (Section 2.2.5)
    DEFAULT_LOW = (-0.5, 0.0, 0.5)
    DEFAULT_MEDIUM = (0.25, 0.5, 0.75)
    DEFAULT_HIGH = (0.5, 1.0, 1.5)
    
    def __init__(self, 
                 params_low: Optional[Tuple[float, float, float]] = None,
                 params_medium: Optional[Tuple[float, float, float]] = None,
                 params_high: Optional[Tuple[float, float, float]] = None):
        """
        Initialize Fuzzy neutrosophication method.
        
        Parameters
        ----------
        params_low : tuple, optional
            Parameters for Low fuzzy set (a, b, c)
            Default: (-0.5, 0.0, 0.5)
        params_medium : tuple, optional
            Parameters for Medium fuzzy set (a, b, c)
            Default: (0.25, 0.5, 0.75)
        params_high : tuple, optional
            Parameters for High fuzzy set (a, b, c)
            Default: (0.5, 1.0, 1.5)
        """
        super().__init__(name="Fuzzy Membership")
        
        self.params_low = params_low if params_low is not None else self.DEFAULT_LOW
        self.params_medium = params_medium if params_medium is not None else self.DEFAULT_MEDIUM
        self.params_high = params_high if params_high is not None else self.DEFAULT_HIGH
        
        self.is_fitted = True  # No fitting required
    
    def _triangular_mf(self, x: np.ndarray, a: float, b: float, c: float) -> np.ndarray:
        """
        Compute triangular membership function (Eq. 12 from paper).
        
        μ(x) = {
            0                  if x ≤ a or x ≥ c
            (x - a)/(b - a)    if a < x ≤ b
            (c - x)/(c - b)    if b < x < c
        }
        
        Parameters
        ----------
        x : np.ndarray
            Input values
        a : float
            Left foot of triangle
        b : float
            Peak of triangle
        c : float
            Right foot of triangle
            
        Returns
        -------
        mu : np.ndarray
            Membership values in [0, 1]
        """
        mu = np.zeros_like(x, dtype=np.float64)
        
        # Left slope: a < x ≤ b
        left_mask = (x > a) & (x <= b)
        if b > a:
            mu[left_mask] = (x[left_mask] - a) / (b - a)
        
        # Right slope: b < x < c
        right_mask = (x > b) & (x < c)
        if c > b:
            mu[right_mask] = (c - x[right_mask]) / (c - b)
        
        return mu
    
    def fit(self, X: np.ndarray) -> 'FuzzyNeutrosophic':
        """
        Fit method (no-op for Fuzzy).
        
        This method requires no fitting as it uses predefined fuzzy sets.
        
        Parameters
        ----------
        X : np.ndarray
            Input data (used only for validation)
            
        Returns
        -------
        self : FuzzyNeutrosophic
            Returns self for method chaining
        """
        X = validate_input(X, "X")
        self.is_fitted = True
        return self
    
    def transform(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Transform data to neutrosophic values using fuzzy membership.
        
        Mathematical Formulation (from paper):
        - T(x) = x
        - I(x) = 1 - max(μ_L(x), μ_M(x), μ_H(x))
        - F(x) = 1 - x
        
        Parameters
        ----------
        X : np.ndarray
            Input data of shape (n_samples,) or (n_samples, 1)
            Values should be in [0, 1]
            
        Returns
        -------
        T : np.ndarray
            Truth component (T = x)
        I : np.ndarray
            Indeterminacy component (1 - max membership)
        F : np.ndarray
            Falsity component (F = 1 - x)
        """
        X = validate_input(X, "X")
        
        # Ensure values are in [0, 1]
        X = np.clip(X, 0, 1)
        
        # Compute membership values for each fuzzy set
        mu_low = self._triangular_mf(X, *self.params_low)
        mu_medium = self._triangular_mf(X, *self.params_medium)
        mu_high = self._triangular_mf(X, *self.params_high)
        
        # Compute T: direct value
        T = X.copy()
        
        # Compute I: 1 - max(μ_L, μ_M, μ_H)
        # Low indeterminacy when any fuzzy set has high membership
        max_membership = np.maximum(np.maximum(mu_low, mu_medium), mu_high)
        I = 1.0 - max_membership
        
        # Compute F: complement of T
        F = 1.0 - X
        
        # Clip to valid range
        T, I, F = self.clip_to_range(T, I, F)
        
        # Store results
        self.T_values = T
        self.I_values = I
        self.F_values = F
        
        return T, I, F
    
    def get_membership_values(self, X: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Get individual fuzzy membership values for all sets.
        
        Parameters
        ----------
        X : np.ndarray
            Input data
            
        Returns
        -------
        memberships : dict
            Dictionary with 'low', 'medium', 'high' membership arrays
        """
        X = validate_input(X, "X")
        X = np.clip(X, 0, 1)
        
        return {
            'low': self._triangular_mf(X, *self.params_low),
            'medium': self._triangular_mf(X, *self.params_medium),
            'high': self._triangular_mf(X, *self.params_high)
        }
    
    def get_parameters(self) -> Dict:
        """
        Get the method parameters.
        
        Returns
        -------
        params : dict
            Dictionary containing fuzzy set parameters
        """
        return {
            'params_low': self.params_low,
            'params_medium': self.params_medium,
            'params_high': self.params_high,
            'a_L': self.params_low[0],
            'b_L': self.params_low[1],
            'c_L': self.params_low[2],
            'a_M': self.params_medium[0],
            'b_M': self.params_medium[1],
            'c_M': self.params_medium[2],
            'a_H': self.params_high[0],
            'b_H': self.params_high[1],
            'c_H': self.params_high[2],
            'complementarity': 'T + F = 1 (forced)'
        }
