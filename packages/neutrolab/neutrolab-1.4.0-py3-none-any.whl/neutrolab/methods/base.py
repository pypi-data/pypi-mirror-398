"""
Base class for all neutrosophication methods.

This module defines the abstract interface that all neutrosophication methods
must implement, ensuring consistency and interoperability across the library.

References:
    Smarandache, F. (1998). Neutrosophy/neutrosophic probability, set, and logic.
"""

from abc import ABC, abstractmethod
import numpy as np
from typing import Tuple, Optional, Dict
import warnings


class NeutrosophicMethod(ABC):
    """
    Abstract base class for neutrosophication methods.
    
    All neutrosophication methods must inherit from this class and implement
    the required methods. A neutrosophication method transforms a normalized
    input value x ∈ [0, 1] into a neutrosophic triplet (T, I, F) where:
    
    - T (Truth): Degree of truth/membership
    - I (Indeterminacy): Degree of indeterminacy/uncertainty
    - F (Falsity): Degree of falsity/non-membership
    
    In true neutrosophic logic, T, I, and F are independent components,
    unlike fuzzy logic where T + F = 1.
    
    Attributes
    ----------
    name : str
        Name of the neutrosophication method
    is_fitted : bool
        Whether the method has been fitted to data
    T_values : np.ndarray or None
        Last computed Truth values
    I_values : np.ndarray or None
        Last computed Indeterminacy values
    F_values : np.ndarray or None
        Last computed Falsity values
    """
    
    def __init__(self, name: str):
        """
        Initialize the neutrosophication method.
        
        Parameters
        ----------
        name : str
            Name of the method
        """
        self.name = name
        self.is_fitted = False
        self.T_values: Optional[np.ndarray] = None
        self.I_values: Optional[np.ndarray] = None
        self.F_values: Optional[np.ndarray] = None
    
    @abstractmethod
    def fit(self, X: np.ndarray) -> 'NeutrosophicMethod':
        """
        Fit the method to data (if required).
        
        Some methods (like K-Means) require fitting to data, while others
        (like Parabolic) are parameter-free and don't require fitting.
        
        Parameters
        ----------
        X : np.ndarray
            Input data of shape (n_samples,) or (n_samples, 1)
            Values should be normalized to [0, 1]
            
        Returns
        -------
        self : NeutrosophicMethod
            Returns self for method chaining
        """
        pass
    
    @abstractmethod
    def transform(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Transform data to neutrosophic values.
        
        Parameters
        ----------
        X : np.ndarray
            Input data of shape (n_samples,) or (n_samples, 1)
            Values should be normalized to [0, 1]
            
        Returns
        -------
        T : np.ndarray
            Truth component of shape (n_samples,)
        I : np.ndarray
            Indeterminacy component of shape (n_samples,)
        F : np.ndarray
            Falsity component of shape (n_samples,)
        """
        pass
    
    def fit_transform(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Fit the method and transform data in one step.
        
        Parameters
        ----------
        X : np.ndarray
            Input data of shape (n_samples,) or (n_samples, 1)
            
        Returns
        -------
        T : np.ndarray
            Truth component
        I : np.ndarray
            Indeterminacy component
        F : np.ndarray
            Falsity component
        """
        self.fit(X)
        return self.transform(X)
    
    @abstractmethod
    def get_parameters(self) -> Dict:
        """
        Get the method parameters.
        
        Returns
        -------
        params : dict
            Dictionary containing method-specific parameters
        """
        pass
    
    def get_results(self) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Get the last computed T, I, F values.
        
        Returns
        -------
        T : np.ndarray or None
            Truth component
        I : np.ndarray or None
            Indeterminacy component
        F : np.ndarray or None
            Falsity component
        """
        return self.T_values, self.I_values, self.F_values
    
    def validate_output(self, T: np.ndarray, I: np.ndarray, F: np.ndarray) -> bool:
        """
        Validate that T, I, F are in valid range [0, 1].
        
        Parameters
        ----------
        T : np.ndarray
            Truth component
        I : np.ndarray
            Indeterminacy component
        F : np.ndarray
            Falsity component
            
        Returns
        -------
        bool
            True if all values are in [0, 1], False otherwise
        """
        valid = True
        tolerance = 1e-6
        
        if np.any(T < -tolerance) or np.any(T > 1 + tolerance):
            warnings.warn(f"{self.name}: Truth values outside [0, 1]", UserWarning)
            valid = False
        
        if np.any(I < -tolerance) or np.any(I > 1 + tolerance):
            warnings.warn(f"{self.name}: Indeterminacy values outside [0, 1]", UserWarning)
            valid = False
        
        if np.any(F < -tolerance) or np.any(F > 1 + tolerance):
            warnings.warn(f"{self.name}: Falsity values outside [0, 1]", UserWarning)
            valid = False
        
        return valid
    
    def clip_to_range(self, T: np.ndarray, I: np.ndarray, F: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Clip T, I, F values to [0, 1] range.
        
        Parameters
        ----------
        T : np.ndarray
            Truth component
        I : np.ndarray
            Indeterminacy component
        F : np.ndarray
            Falsity component
            
        Returns
        -------
        T : np.ndarray
            Clipped truth component
        I : np.ndarray
            Clipped indeterminacy component
        F : np.ndarray
            Clipped falsity component
        """
        return np.clip(T, 0, 1), np.clip(I, 0, 1), np.clip(F, 0, 1)
    
    def compute_sum_statistics(self) -> Dict[str, float]:
        """
        Compute T+I+F sum statistics (key neutrosophic property).
        
        In true neutrosophic logic, T+I+F can be different from 1,
        unlike fuzzy logic where T+F=1.
        
        Returns
        -------
        stats : dict
            Dictionary with 'mean_sum', 'std_sum', 'min_sum', 'max_sum'
        """
        if self.T_values is None:
            raise ValueError("No results available. Call transform() first.")
        
        tif_sum = self.T_values + self.I_values + self.F_values
        return {
            'mean_sum': float(np.mean(tif_sum)),
            'std_sum': float(np.std(tif_sum)),
            'min_sum': float(np.min(tif_sum)),
            'max_sum': float(np.max(tif_sum))
        }
    
    def __repr__(self) -> str:
        """String representation of the method."""
        return f"{self.__class__.__name__}(name='{self.name}', fitted={self.is_fitted})"
