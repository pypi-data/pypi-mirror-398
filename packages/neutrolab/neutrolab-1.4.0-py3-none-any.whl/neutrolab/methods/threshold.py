"""
Threshold Distance Neutrosophication Method (Semi-novel)

This module implements a threshold-based approach for neutrosophication
that uses distance to a predefined threshold for computing membership values.

Mathematical Formulation (from paper Section 2.2.3):
----------------------------------------------------
    T(x) = 1 / (1 + exp(-10·(x - θ)))
    I(x) = exp(-λ·(x - θ)²)
    F(x) = 1 - T(x)

where:
    θ = 0.5 (threshold)
    λ = 5.0 (sensitivity parameter)

This method produces maximum indeterminacy at x = θ.

Key Properties:
- Model-based with tunable parameters
- Forced complementarity: T + F = 1 (fuzzy-like constraint)
- T+I+F sum typically > 1 (mean sum ≈ 1.711 in experiments)
- Highest mean indeterminacy (0.711) among tested methods
- Best for: Threshold-based decision making

References:
    Zhang, M., Zhang, L., & Cheng, H. D. (2010). A neutrosophic approach to 
    image segmentation based on watershed method.
"""

import numpy as np
from typing import Tuple, Optional, Dict
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


class ThresholdNeutrosophic(NeutrosophicMethod):
    """
    Threshold Distance Neutrosophication Method (Semi-novel).
    
    This method computes neutrosophic values based on distance to a
    predefined threshold using sigmoid and Gaussian functions.
    
    NOTE: This method enforces T + F = 1 (fuzzy-like complementarity),
    which is NOT true neutrosophic independence.
    
    Attributes
    ----------
    theta : float
        Threshold value (default: 0.5)
    lambda_ : float
        Sensitivity parameter for Gaussian indeterminacy (default: 5.0)
    slope : float
        Slope parameter for sigmoid (default: 10.0)
        
    Examples
    --------
    >>> import numpy as np
    >>> from neutrolab import ThresholdNeutrosophic
    >>> 
    >>> data = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
    >>> method = ThresholdNeutrosophic(theta=0.5, lambda_=5.0)
    >>> T, I, F = method.fit_transform(data)
    >>> 
    >>> # Indeterminacy is maximum at threshold (x=0.5)
    >>> print(f"I at threshold: {I[2]:.3f}")  # Should be 1.0
    """
    
    def __init__(self, theta: float = 0.5, lambda_: float = 5.0, slope: float = 10.0):
        """
        Initialize Threshold neutrosophication method.
        
        Parameters
        ----------
        theta : float, default=0.5
            Threshold value (θ in formulas)
        lambda_ : float, default=5.0
            Sensitivity parameter for Gaussian indeterminacy (λ in formulas)
        slope : float, default=10.0
            Slope parameter for sigmoid function
        """
        super().__init__(name="Threshold Distance")
        self.theta = theta
        self.lambda_ = lambda_
        self.slope = slope
        self.is_fitted = True  # No fitting required
    
    def fit(self, X: np.ndarray) -> 'ThresholdNeutrosophic':
        """
        Fit method (no-op for Threshold).
        
        This method requires no fitting as it uses fixed formulas.
        
        Parameters
        ----------
        X : np.ndarray
            Input data (used only for validation)
            
        Returns
        -------
        self : ThresholdNeutrosophic
            Returns self for method chaining
        """
        X = validate_input(X, "X")
        self.is_fitted = True
        return self
    
    def transform(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Transform data to neutrosophic values using threshold formulas.
        
        Mathematical Formulation (Eq. 7 from paper):
        - T(x) = 1 / (1 + exp(-10·(x - θ)))
        - I(x) = exp(-λ·(x - θ)²)
        - F(x) = 1 - T(x)
        
        Parameters
        ----------
        X : np.ndarray
            Input data of shape (n_samples,) or (n_samples, 1)
            Values should be in [0, 1]
            
        Returns
        -------
        T : np.ndarray
            Truth component (sigmoid centered at threshold)
        I : np.ndarray
            Indeterminacy component (Gaussian centered at threshold)
        F : np.ndarray
            Falsity component (complement of T)
        """
        X = validate_input(X, "X")
        
        # Ensure values are in [0, 1]
        X = np.clip(X, 0, 1)
        
        # Compute T: sigmoid centered at threshold (Eq. 7 from paper)
        # T(x) = 1 / (1 + exp(-10·(x - θ)))
        T = 1.0 / (1.0 + np.exp(-self.slope * (X - self.theta)))
        
        # Compute I: Gaussian centered at threshold (Eq. 7 from paper)
        # I(x) = exp(-λ·(x - θ)²)
        I = np.exp(-self.lambda_ * (X - self.theta) ** 2)
        
        # Compute F: complement of T (Eq. 7 from paper)
        # F(x) = 1 - T(x)
        F = 1.0 - T
        
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
            Dictionary containing threshold and sensitivity parameters
        """
        return {
            'theta': self.theta,
            'lambda': self.lambda_,
            'slope': self.slope,
            'complementarity': 'T + F = 1 (forced)'
        }
