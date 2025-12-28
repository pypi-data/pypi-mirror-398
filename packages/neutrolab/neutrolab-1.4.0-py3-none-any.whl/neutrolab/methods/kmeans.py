"""
K-Means Clustering Neutrosophication Method (Proposed)

This module implements the proposed K-Means clustering approach with sigmoid
membership functions for neutrosophication. This method is data-driven and
achieves true independence of T, I, and F components.

This is the method proposed in:
"A Comparative Analysis of Data-Driven and Model-Based Neutrosophication Methods"

Mathematical Formulation (from paper Section 2.2.1):
----------------------------------------------------
Truth Component (T):
    T(x) = 1 / (1 + exp(-10 · (x - c_high) / (σ_high + ε)))
    
    where c_high is the centroid of the "high" cluster and σ_high is its
    standard deviation. This sigmoid ensures T(x) ≈ 1 for high values.

Indeterminacy Component (I):
    I(x) = 1 / (1 + |x - c_mid| / (σ_mid + ε))
    
    Indeterminacy is maximized when x = c_mid and decreases as x moves
    away from the medium centroid.

Falsity Component (F):
    F(x) = 1 / (1 + exp(10 · (x - c_low) / (σ_low + ε)))
    
    This is the inverse sigmoid centered at c_low, ensuring F(x) ≈ 1 
    for low values and ≈ 0 for high values.

where ε = 10⁻⁶ prevents division by zero.

Key Properties:
- Achieves TRUE INDEPENDENCE of T, I, F components (core neutrosophic principle)
- T+I+F sum typically ≠ 1 (mean sum ≈ 0.639 in experiments)
- Data-driven: automatically learns cluster centroids from data
- High indeterminacy range (0.894) and moderate entropy (2.149)

References:
    Leyva-Vázquez, M. Y., et al. "A Comparative Analysis of Data-Driven and 
    Model-Based Neutrosophication Methods"
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


class KMeansNeutrosophic(NeutrosophicMethod):
    """
    K-Means Clustering Neutrosophication Method (Proposed).
    
    This method clusters data into three groups (low, medium, high) using K-Means
    and derives neutrosophic components based on distances to these clusters.
    It achieves TRUE INDEPENDENCE of T, I, and F - a key neutrosophic principle.
    
    This is the PROPOSED METHOD from the paper, showing superior theoretical
    consistency with neutrosophic logic principles.
    
    Attributes
    ----------
    n_clusters : int
        Number of clusters (fixed at 3 for low, medium, high)
    centroids : np.ndarray
        Cluster centroids after fitting [c_low, c_mid, c_high]
    stds : np.ndarray
        Standard deviations of each cluster [σ_low, σ_mid, σ_high]
    epsilon : float
        Small value to prevent division by zero (default: 1e-6)
    slope : float
        Slope parameter for sigmoid functions (default: 10)
        
    Examples
    --------
    >>> import numpy as np
    >>> from neutrolab import KMeansNeutrosophic
    >>> 
    >>> # Sample normalized data
    >>> data = np.random.random(100)
    >>> 
    >>> # Create and fit method
    >>> method = KMeansNeutrosophic(random_state=42)
    >>> T, I, F = method.fit_transform(data)
    >>> 
    >>> # Check T+I+F independence (should NOT equal 1)
    >>> print(f"Mean T+I+F: {np.mean(T + I + F):.3f}")  # ≈ 0.639
    """
    
    def __init__(self, n_clusters: int = 3, random_state: Optional[int] = None, 
                 max_iter: int = 100, epsilon: float = 1e-6, slope: float = 10.0):
        """
        Initialize K-Means neutrosophication method.
        
        Parameters
        ----------
        n_clusters : int, default=3
            Number of clusters (should be 3 for low, medium, high)
        random_state : int, optional
            Random state for reproducibility
        max_iter : int, default=100
            Maximum iterations for K-Means
        epsilon : float, default=1e-6
            Small value to prevent division by zero (ε in formulas)
        slope : float, default=10.0
            Slope parameter for sigmoid functions (controls steepness)
        """
        super().__init__(name="K-Means")
        self.n_clusters = n_clusters
        self.random_state = random_state
        self.max_iter = max_iter
        self.epsilon = epsilon
        self.slope = slope
        self.centroids: Optional[np.ndarray] = None
        self.stds: Optional[np.ndarray] = None
    
    def fit(self, X: np.ndarray) -> 'KMeansNeutrosophic':
        """
        Fit K-Means clustering to data.
        
        Parameters
        ----------
        X : np.ndarray
            Input data of shape (n_samples,) or (n_samples, 1)
            Values should be normalized to [0, 1]
            
        Returns
        -------
        self : KMeansNeutrosophic
            Returns self for method chaining
        """
        X = validate_input(X, "X")
        
        # Set random seed for reproducibility
        if self.random_state is not None:
            np.random.seed(self.random_state)
        
        # Initialize centroids randomly from data points
        indices = np.random.choice(len(X), self.n_clusters, replace=False)
        self.centroids = X[indices].copy()
        
        # K-Means iterations
        for _ in range(self.max_iter):
            # Assign points to nearest centroid
            distances = np.abs(X[:, np.newaxis] - self.centroids)
            labels = np.argmin(distances, axis=1)
            
            # Update centroids
            old_centroids = self.centroids.copy()
            for k in range(self.n_clusters):
                mask = labels == k
                if np.any(mask):
                    self.centroids[k] = np.mean(X[mask])
            
            # Check convergence
            if np.allclose(old_centroids, self.centroids):
                break
        
        # Sort centroids to get [c_low, c_mid, c_high]
        self.centroids = np.sort(self.centroids)
        
        # Compute standard deviations for each cluster
        self.stds = np.zeros(self.n_clusters)
        distances = np.abs(X[:, np.newaxis] - self.centroids)
        labels = np.argmin(distances, axis=1)
        
        for k in range(self.n_clusters):
            mask = labels == k
            if np.any(mask) and np.sum(mask) > 1:
                self.stds[k] = np.std(X[mask])
            else:
                self.stds[k] = 0.1  # Default std if cluster is empty or has 1 point
        
        self.is_fitted = True
        return self
    
    def transform(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Transform data to neutrosophic values using the paper's formulas.
        
        Mathematical Formulation:
        - T(x) = 1 / (1 + exp(-10·(x - c_high)/(σ_high + ε)))
        - I(x) = 1 / (1 + |x - c_mid|/(σ_mid + ε))
        - F(x) = 1 / (1 + exp(10·(x - c_low)/(σ_low + ε)))
        
        Parameters
        ----------
        X : np.ndarray
            Input data of shape (n_samples,) or (n_samples, 1)
            Values should be normalized to [0, 1]
            
        Returns
        -------
        T : np.ndarray
            Truth component (based on high cluster)
        I : np.ndarray
            Indeterminacy component (based on medium cluster)
        F : np.ndarray
            Falsity component (based on low cluster)
        """
        if not self.is_fitted:
            raise ValueError("Method must be fitted before transform. Call fit() first.")
        
        X = validate_input(X, "X")
        
        # Extract cluster parameters
        c_low = self.centroids[0]
        c_mid = self.centroids[1]
        c_high = self.centroids[2]
        
        sigma_low = self.stds[0]
        sigma_mid = self.stds[1]
        sigma_high = self.stds[2]
        
        # Compute T: sigmoid centered at high cluster (Eq. 2 from paper)
        # T(x) = 1 / (1 + exp(-10·(x - c_high)/(σ_high + ε)))
        T = 1.0 / (1.0 + np.exp(-self.slope * (X - c_high) / (sigma_high + self.epsilon)))
        
        # Compute I: distance-based centered at medium cluster (Eq. 3 from paper)
        # I(x) = 1 / (1 + |x - c_mid|/(σ_mid + ε))
        I = 1.0 / (1.0 + np.abs(X - c_mid) / (sigma_mid + self.epsilon))
        
        # Compute F: inverse sigmoid centered at low cluster (Eq. 4 from paper)
        # F(x) = 1 / (1 + exp(10·(x - c_low)/(σ_low + ε)))
        F = 1.0 / (1.0 + np.exp(self.slope * (X - c_low) / (sigma_low + self.epsilon)))
        
        # Clip to valid range [0, 1]
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
            Dictionary containing:
            - centroids: array of [c_low, c_mid, c_high]
            - stds: array of [σ_low, σ_mid, σ_high]
            - c_low, c_mid, c_high: individual centroids
            - sigma_low, sigma_mid, sigma_high: individual std devs
            - slope: sigmoid slope parameter
            - epsilon: numerical stability parameter
        """
        if not self.is_fitted:
            raise ValueError("Method must be fitted first")
        
        return {
            'centroids': self.centroids.copy(),
            'stds': self.stds.copy(),
            'c_low': float(self.centroids[0]),
            'c_mid': float(self.centroids[1]),
            'c_high': float(self.centroids[2]),
            'sigma_low': float(self.stds[0]),
            'sigma_mid': float(self.stds[1]),
            'sigma_high': float(self.stds[2]),
            'slope': self.slope,
            'epsilon': self.epsilon
        }
