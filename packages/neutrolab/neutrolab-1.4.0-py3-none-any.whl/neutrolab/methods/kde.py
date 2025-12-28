"""
Kernel Density Estimation (KDE) Neutrosophication Method (Established)

This module implements a KDE-based approach for neutrosophication that
uses probability density estimation to derive membership values.

Mathematical Formulation (from paper Section 2.2.4):
----------------------------------------------------
Local density estimation:
    f̂(x) = (1/(n·h)) · Σᵢ K((x - xᵢ)/h)

where:
    n = number of data points
    h = bandwidth parameter
    K(·) = Gaussian kernel function

Normalized density:
    f̂_norm(x) = (f̂(x) - f_min) / (f_max - f_min + ε)

Neutrosophic components (Eq. 11 from paper):
    T(x) = x
    I(x) = 1 - f̂_norm(x)
    F(x) = 1 - x

Indeterminacy is HIGH in sparse regions (low density) and LOW where 
data density is high.

Key Properties:
- Density-based: adapts to data distribution
- Computationally expensive
- Forced complementarity: T + F = 1 (fuzzy-like constraint)
- T+I+F sum typically > 1 (mean sum ≈ 1.260 in experiments)
- High sensitivity to bandwidth parameter
- Best for: Anomaly detection and sparse region identification

References:
    Silverman, B. W. (1986). Density estimation for statistics and data analysis.
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


class KDENeutrosophic(NeutrosophicMethod):
    """
    Kernel Density Estimation Neutrosophication Method (Established).
    
    This method uses KDE to estimate the probability distribution of data
    and derives neutrosophic values from the normalized density.
    
    Indeterminacy is HIGH in sparse regions (low density) and LOW where 
    data density is high.
    
    NOTE: This method enforces T + F = 1 (fuzzy-like complementarity),
    which is NOT true neutrosophic independence.
    
    Attributes
    ----------
    bandwidth : float or None
        Bandwidth parameter for KDE (computed using Silverman's rule if None)
    kernel : str
        Kernel type ('gaussian' only for now)
        
    Examples
    --------
    >>> import numpy as np
    >>> from neutrolab import KDENeutrosophic
    >>> 
    >>> # Bimodal data - high density at 0.2 and 0.8
    >>> data = np.concatenate([np.random.normal(0.2, 0.05, 50),
    ...                        np.random.normal(0.8, 0.05, 50)])
    >>> data = np.clip(data, 0, 1)
    >>> 
    >>> method = KDENeutrosophic()
    >>> T, I, F = method.fit_transform(data)
    >>> 
    >>> # Low indeterminacy at dense regions, high at sparse center
    """
    
    def __init__(self, bandwidth: Optional[float] = None, kernel: str = 'gaussian',
                 epsilon: float = 1e-6):
        """
        Initialize KDE neutrosophication method.
        
        Parameters
        ----------
        bandwidth : float, optional
            Bandwidth for KDE (h in formulas). If None, computed using 
            Silverman's rule of thumb.
        kernel : str, default='gaussian'
            Kernel type (currently only 'gaussian' is supported)
        epsilon : float, default=1e-6
            Small value to prevent division by zero
        """
        super().__init__(name="KDE")
        self.bandwidth = bandwidth
        self.kernel = kernel
        self.epsilon = epsilon
        self._data: Optional[np.ndarray] = None
        self._f_min: Optional[float] = None
        self._f_max: Optional[float] = None
    
    def _gaussian_kernel(self, u: np.ndarray) -> np.ndarray:
        """
        Compute Gaussian kernel function K(u).
        
        K(u) = (1/√(2π)) · exp(-u²/2)
        
        Parameters
        ----------
        u : np.ndarray
            Standardized distances
            
        Returns
        -------
        K : np.ndarray
            Kernel values
        """
        return np.exp(-0.5 * u ** 2) / np.sqrt(2 * np.pi)
    
    def _estimate_density(self, X: np.ndarray) -> np.ndarray:
        """
        Estimate density at given points using KDE.
        
        f̂(x) = (1/(n·h)) · Σᵢ K((x - xᵢ)/h)
        
        Parameters
        ----------
        X : np.ndarray
            Points at which to estimate density
            
        Returns
        -------
        density : np.ndarray
            Estimated density values
        """
        n = len(self._data)
        h = self.bandwidth
        
        density = np.zeros(len(X), dtype=np.float64)
        
        for i, x in enumerate(X):
            u = (x - self._data) / h
            density[i] = np.sum(self._gaussian_kernel(u))
        
        density /= (n * h)
        return density
    
    def fit(self, X: np.ndarray) -> 'KDENeutrosophic':
        """
        Fit KDE to data.
        
        Computes bandwidth using Silverman's rule if not provided,
        and precomputes density range for normalization.
        
        Parameters
        ----------
        X : np.ndarray
            Input data of shape (n_samples,) or (n_samples, 1)
            
        Returns
        -------
        self : KDENeutrosophic
            Returns self for method chaining
        """
        X = validate_input(X, "X")
        self._data = X.copy()
        
        # Compute bandwidth using Silverman's rule if not provided
        if self.bandwidth is None:
            n = len(X)
            std = np.std(X)
            iqr = np.percentile(X, 75) - np.percentile(X, 25)
            # Silverman's rule of thumb
            self.bandwidth = 0.9 * min(std, iqr / 1.34) * (n ** (-0.2))
            self.bandwidth = max(self.bandwidth, self.epsilon)  # Ensure positive
        
        # Compute density range for normalization
        grid = np.linspace(X.min(), X.max(), 100)
        density_grid = self._estimate_density(grid)
        self._f_min = float(np.min(density_grid))
        self._f_max = float(np.max(density_grid))
        
        self.is_fitted = True
        return self
    
    def transform(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Transform data to neutrosophic values using KDE formulas.
        
        Mathematical Formulation (Eq. 11 from paper):
        - T(x) = x
        - I(x) = 1 - f̂_norm(x)  (high I in sparse regions)
        - F(x) = 1 - x
        
        Parameters
        ----------
        X : np.ndarray
            Input data of shape (n_samples,) or (n_samples, 1)
            
        Returns
        -------
        T : np.ndarray
            Truth component (T = x)
        I : np.ndarray
            Indeterminacy component (high where density is low)
        F : np.ndarray
            Falsity component (F = 1 - x)
        """
        if not self.is_fitted:
            raise ValueError("Method must be fitted before transform. Call fit() first.")
        
        X = validate_input(X, "X")
        
        # Ensure values are in [0, 1]
        X = np.clip(X, 0, 1)
        
        # Compute T: direct value (Eq. 11 from paper)
        T = X.copy()
        
        # Compute density and normalize (Eq. 8, 9 from paper)
        density = self._estimate_density(X)
        f_norm = (density - self._f_min) / (self._f_max - self._f_min + self.epsilon)
        
        # Compute I: inverse of normalized density (Eq. 11 from paper)
        # High indeterminacy in sparse regions (low density)
        I = 1.0 - f_norm
        
        # Compute F: complement of T (Eq. 11 from paper)
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
        Get the fitted parameters.
        
        Returns
        -------
        params : dict
            Dictionary containing bandwidth and density statistics
        """
        if not self.is_fitted:
            raise ValueError("Method must be fitted first")
        
        return {
            'bandwidth': self.bandwidth,
            'kernel': self.kernel,
            'n_samples': len(self._data),
            'f_min': self._f_min,
            'f_max': self._f_max,
            'complementarity': 'T + F = 1 (forced)'
        }
