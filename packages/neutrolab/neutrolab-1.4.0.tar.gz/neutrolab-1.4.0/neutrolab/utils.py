"""
Utility functions for NeutroLab library.

This module provides helper functions for data preprocessing, validation,
statistical analysis, and method comparison.

References:
    Leyva-Vázquez, M. Y., et al. "A Comparative Analysis of Data-Driven and 
    Model-Based Neutrosophication Methods"
"""

import numpy as np
import pandas as pd
from typing import Union, Tuple, Dict
from scipy.stats import entropy, skew, kurtosis


def normalize_data(X: Union[np.ndarray, pd.DataFrame, pd.Series], 
                   method: str = 'minmax') -> Union[np.ndarray, pd.DataFrame, pd.Series]:
    """
    Normalize data to [0, 1] range using Min-Max scaling.
    
    This is the normalization method used in the paper (Eq. 1):
        x_norm = (x - x_min) / (x_max - x_min)
    
    Parameters
    ----------
    X : np.ndarray, pd.DataFrame, or pd.Series
        Input data
    method : str, default='minmax'
        Normalization method: 'minmax' or 'zscore'
        
    Returns
    -------
    X_normalized : same type as input
        Normalized data in [0, 1] range (for minmax)
        
    Examples
    --------
    >>> data = np.array([29, 54, 77])  # Age range from paper
    >>> normalized = normalize_data(data)
    >>> print(normalized)  # [0.   0.52 1.  ]
    """
    epsilon = 1e-10  # Prevent division by zero
    
    if isinstance(X, pd.DataFrame):
        if method == 'minmax':
            return (X - X.min()) / (X.max() - X.min() + epsilon)
        elif method == 'zscore':
            return (X - X.mean()) / (X.std() + epsilon)
        else:
            raise ValueError(f"Unknown normalization method: {method}")
    
    elif isinstance(X, pd.Series):
        if method == 'minmax':
            return (X - X.min()) / (X.max() - X.min() + epsilon)
        elif method == 'zscore':
            return (X - X.mean()) / (X.std() + epsilon)
        else:
            raise ValueError(f"Unknown normalization method: {method}")
    
    else:
        X = np.asarray(X, dtype=np.float64)
        if method == 'minmax':
            return (X - X.min()) / (X.max() - X.min() + epsilon)
        elif method == 'zscore':
            return (X - X.mean()) / (X.std() + epsilon)
        else:
            raise ValueError(f"Unknown normalization method: {method}")


def validate_input(X: np.ndarray, name: str = "input") -> np.ndarray:
    """
    Validate and reshape input data.
    
    Parameters
    ----------
    X : array-like
        Input data
    name : str
        Name of the input for error messages
        
    Returns
    -------
    X : np.ndarray
        Validated and reshaped data of shape (n_samples,)
        
    Raises
    ------
    ValueError
        If input contains NaN, Inf, or has invalid shape
    """
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


def compute_statistics(T: np.ndarray, I: np.ndarray, F: np.ndarray) -> Dict[str, float]:
    """
    Compute statistical properties of neutrosophic values.
    
    Includes metrics used in the paper for method comparison:
    - T+F Consistency (Eq. 13)
    - Indeterminacy Range (Eq. 14)
    - Entropy (Eq. 15)
    
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
    stats : dict
        Dictionary containing comprehensive statistics
        
    Examples
    --------
    >>> T, I, F = method.fit_transform(data)
    >>> stats = compute_statistics(T, I, F)
    >>> print(f"Mean T+I+F: {stats['mean_sum']:.3f}")
    """
    # Compute histogram for entropy calculation
    hist_I, _ = np.histogram(I, bins=20)
    hist_I = hist_I + 1e-10  # Avoid log(0)
    hist_I = hist_I / hist_I.sum()  # Normalize to probabilities
    
    stats = {
        # Truth statistics
        'mean_T': float(np.mean(T)),
        'std_T': float(np.std(T)),
        'min_T': float(np.min(T)),
        'max_T': float(np.max(T)),
        'median_T': float(np.median(T)),
        
        # Indeterminacy statistics
        'mean_I': float(np.mean(I)),
        'std_I': float(np.std(I)),
        'min_I': float(np.min(I)),
        'max_I': float(np.max(I)),
        'median_I': float(np.median(I)),
        
        # Indeterminacy Range (Eq. 14 from paper)
        'indeterminacy_range': float(np.max(I) - np.min(I)),
        
        # Entropy (Eq. 15 from paper)
        'entropy_I': float(entropy(hist_I)),
        
        # Higher moments for indeterminacy
        'skewness_I': float(skew(I)),
        'kurtosis_I': float(kurtosis(I)),
        
        # Falsity statistics
        'mean_F': float(np.mean(F)),
        'std_F': float(np.std(F)),
        'min_F': float(np.min(F)),
        'max_F': float(np.max(F)),
        'median_F': float(np.median(F)),
        
        # Combined statistics
        'mean_sum': float(np.mean(T + I + F)),  # T+I+F sum
        'std_sum': float(np.std(T + I + F)),
        
        # T+F Consistency (Eq. 13 from paper)
        # Measures how close T+F is to 1 (fuzzy complementarity)
        'tf_consistency': float(1 - np.mean(np.abs((T + F) - 1))),
    }
    
    return stats


def compare_methods(results: Dict[str, Tuple[np.ndarray, np.ndarray, np.ndarray]]) -> pd.DataFrame:
    """
    Compare multiple neutrosophication methods.
    
    Useful for replicating the comparative analysis from the paper.
    
    Parameters
    ----------
    results : dict
        Dictionary with method names as keys and (T, I, F) tuples as values
        
    Returns
    -------
    comparison : pd.DataFrame
        Comparison table with statistics for each method
        
    Examples
    --------
    >>> from neutrolab import KMeansNeutrosophic, ParabolicNeutrosophic
    >>> 
    >>> methods = {
    ...     'K-Means': KMeansNeutrosophic(random_state=42),
    ...     'Parabolic': ParabolicNeutrosophic()
    ... }
    >>> 
    >>> results = {}
    >>> for name, method in methods.items():
    ...     results[name] = method.fit_transform(data)
    >>> 
    >>> comparison = compare_methods(results)
    >>> print(comparison[['Method', 'mean_sum', 'tf_consistency', 'entropy_I']])
    """
    comparison_data = []
    
    for method_name, (T, I, F) in results.items():
        stats = compute_statistics(T, I, F)
        stats['Method'] = method_name
        comparison_data.append(stats)
    
    df = pd.DataFrame(comparison_data)
    
    # Reorder columns to put Method first
    cols = ['Method'] + [c for c in df.columns if c != 'Method']
    return df[cols]


def compute_correlation(I1: np.ndarray, I2: np.ndarray) -> float:
    """
    Compute Pearson correlation between two indeterminacy distributions.
    
    Used in the paper for correlation analysis between methods (Figure 2).
    
    Parameters
    ----------
    I1 : np.ndarray
        First indeterminacy component
    I2 : np.ndarray
        Second indeterminacy component
        
    Returns
    -------
    correlation : float
        Pearson correlation coefficient in [-1, 1]
        
    Examples
    --------
    >>> r = compute_correlation(I_kmeans, I_parabolic)
    >>> print(f"Correlation: {r:.3f}")
    """
    return float(np.corrcoef(I1, I2)[0, 1])


def compute_distance(T1: np.ndarray, I1: np.ndarray, F1: np.ndarray,
                     T2: np.ndarray, I2: np.ndarray, F2: np.ndarray,
                     metric: str = 'euclidean') -> float:
    """
    Compute distance between two neutrosophic value sets.
    
    Parameters
    ----------
    T1, I1, F1 : np.ndarray
        First neutrosophic set
    T2, I2, F2 : np.ndarray
        Second neutrosophic set
    metric : str, default='euclidean'
        Distance metric: 'euclidean', 'manhattan', or 'chebyshev'
        
    Returns
    -------
    distance : float
        Distance between the two sets
        
    Examples
    --------
    >>> d = compute_distance(T1, I1, F1, T2, I2, F2, metric='euclidean')
    >>> print(f"Euclidean distance: {d:.4f}")
    """
    if metric == 'euclidean':
        return float(np.sqrt(np.mean((T1-T2)**2 + (I1-I2)**2 + (F1-F2)**2)))
    elif metric == 'manhattan':
        return float(np.mean(np.abs(T1-T2) + np.abs(I1-I2) + np.abs(F1-F2)))
    elif metric == 'chebyshev':
        return float(np.max([np.max(np.abs(T1-T2)), 
                           np.max(np.abs(I1-I2)), 
                           np.max(np.abs(F1-F2))]))
    else:
        raise ValueError(f"Unknown metric: {metric}")


def compute_tf_consistency(T: np.ndarray, F: np.ndarray) -> float:
    """
    Compute T+F Consistency metric (Eq. 13 from paper).
    
    T+F Consistency = 1 − mean(|T(x) + F(x) − 1|)
    
    A value of 1.0 indicates perfect complementarity (T+F = 1, fuzzy-like),
    while lower values indicate independence between T and F (true neutrosophic).
    
    Parameters
    ----------
    T : np.ndarray
        Truth component
    F : np.ndarray
        Falsity component
        
    Returns
    -------
    consistency : float
        T+F consistency in [0, 1]
        
    Examples
    --------
    >>> # Fuzzy-like method (T+F=1): consistency ≈ 1.0
    >>> # K-Means (independent T,F): consistency ≈ 0.291
    >>> consistency = compute_tf_consistency(T, F)
    """
    return float(1 - np.mean(np.abs((T + F) - 1)))
