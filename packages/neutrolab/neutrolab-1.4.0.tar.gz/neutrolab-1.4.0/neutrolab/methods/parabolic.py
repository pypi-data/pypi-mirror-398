"""
Parabolic Neutrosophication Method (Classical)

This module implements the classical parabolic approach for neutrosophication.
It is parameter-free (except for α) and uses a fixed parabolic function for 
indeterminacy.

Mathematical Formulation (from paper Section 2.2.2):
----------------------------------------------------
    T(x) = x
    I(x) = 4 · x · (1 - x) · α
    F(x) = 1 - x

where α = 0.5 (default scaling factor).

The indeterminacy follows a parabolic shape with maximum value α at x = 0.5.

Key Properties:
- Model-based: no fitting required
- Computationally efficient
- Forced complementarity: T + F = 1 (fuzzy-like constraint)
- T+I+F sum typically > 1 (mean sum ≈ 1.331 in experiments)
- Best for: Speed-critical or real-time scenarios

References:
    Smarandache, F. (2014). Introduction to Neutrosophic Statistics.
"""

import numpy as np
from typing import Tuple, Dict
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


class ParabolicNeutrosophic(NeutrosophicMethod):
    """
    Parabolic Neutrosophication Method (Classical).
    
    This classical method uses direct value for truth, a parabolic function
    for indeterminacy, and complement for falsity.
    
    NOTE: This method enforces T + F = 1 (fuzzy-like complementarity),
    which is NOT true neutrosophic independence.
    
    Attributes
    ----------
    alpha : float
        Scaling factor for indeterminacy parabola (default: 0.5)
        
    Examples
    --------
    >>> import numpy as np
    >>> from neutrolab import ParabolicNeutrosophic
    >>> 
    >>> data = np.array([0, 0.25, 0.5, 0.75, 1.0])
    >>> method = ParabolicNeutrosophic(alpha=0.5)
    >>> T, I, F = method.fit_transform(data)
    >>> 
    >>> # T = x, so T equals input
    >>> print(T)  # [0.   0.25 0.5  0.75 1.  ]
    >>> 
    >>> # I is maximum at x=0.5
    >>> print(I)  # [0.   0.375 0.5  0.375 0.  ]
    >>> 
    >>> # F = 1 - x
    >>> print(F)  # [1.   0.75 0.5  0.25 0.  ]
    """
    
    def __init__(self, alpha: float = 0.5):
        """
        Initialize Parabolic neutrosophication method.
        
        Parameters
        ----------
        alpha : float, default=0.5
            Scaling factor for indeterminacy (should be in (0, 1])
            The maximum indeterminacy value equals α at x = 0.5
        """
        super().__init__(name="Parabolic")
        
        if not (0 < alpha <= 1):
            raise ValueError("alpha must be in (0, 1]")
        
        self.alpha = alpha
        self.is_fitted = True  # No fitting required
    
    def fit(self, X: np.ndarray) -> 'ParabolicNeutrosophic':
        """
        Fit method (no-op for Parabolic).
        
        This method requires no fitting as it uses fixed formulas.
        
        Parameters
        ----------
        X : np.ndarray
            Input data (used only for validation)
            
        Returns
        -------
        self : ParabolicNeutrosophic
            Returns self for method chaining
        """
        X = validate_input(X, "X")
        self.is_fitted = True
        return self
    
    def transform(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Transform data to neutrosophic values using parabolic formulas.
        
        Mathematical Formulation (Eq. 5 from paper):
        - T(x) = x
        - I(x) = 4 · x · (1 - x) · α
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
            Indeterminacy component (I = 4x(1-x) × α)
        F : np.ndarray
            Falsity component (F = 1 - x)
        """
        X = validate_input(X, "X")
        
        # Ensure values are in [0, 1]
        X = np.clip(X, 0, 1)
        
        # Compute components according to paper Eq. 5
        # T(x) = x
        T = X.copy()
        
        # I(x) = 4 · x · (1 - x) · α
        I = 4.0 * X * (1.0 - X) * self.alpha
        
        # F(x) = 1 - x
        F = 1.0 - X
        
        # Clip to valid range
        T, I, F = self.clip_to_range(T, I, F)
        
        # Store results
        self.T_values = T
        self.I_values = I
        self.F_values = F
        
        return T, I, F
    
    def get_parameters(self) -> Dict:
        """
        Get the method parameters.
        
        Returns
        -------
        params : dict
            Dictionary containing alpha parameter
        """
        return {
            'alpha': self.alpha,
            'max_indeterminacy': self.alpha,  # Maximum I at x=0.5
            'complementarity': 'T + F = 1 (forced)'
        }
