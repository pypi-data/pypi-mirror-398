"""
Unit tests for NeutroLab library.

These tests verify that the implementations match the mathematical formulations
described in the paper "A Comparative Analysis of Data-Driven and Model-Based 
Neutrosophication Methods".
"""

import numpy as np
import pytest
from neutrolab import (
    KMeansNeutrosophic,
    ParabolicNeutrosophic,
    ThresholdNeutrosophic,
    KDENeutrosophic,
    FuzzyNeutrosophic,
    normalize_data,
    validate_input,
    compute_statistics,
    compute_tf_consistency
)


class TestNormalization:
    """Tests for data normalization (Eq. 1 from paper)."""
    
    def test_minmax_normalization(self):
        """Test Min-Max normalization: x_norm = (x - x_min)/(x_max - x_min)"""
        data = np.array([29, 54, 77])  # Age range from paper
        normalized = normalize_data(data, method='minmax')
        
        assert normalized[0] == pytest.approx(0, abs=1e-6)  # min -> 0
        assert normalized[2] == pytest.approx(1, abs=1e-6)  # max -> 1
        assert 0 < normalized[1] < 1  # middle value
    
    def test_normalization_preserves_order(self):
        """Normalization should preserve data ordering."""
        data = np.array([10, 30, 50, 70, 90])
        normalized = normalize_data(data)
        
        for i in range(len(normalized) - 1):
            assert normalized[i] < normalized[i + 1]


class TestValidation:
    """Tests for input validation."""
    
    def test_valid_1d_input(self):
        data = np.array([0.1, 0.5, 0.9])
        validated = validate_input(data)
        assert validated.shape == (3,)
    
    def test_valid_2d_input_single_column(self):
        data = np.array([[0.1], [0.5], [0.9]])
        validated = validate_input(data)
        assert validated.shape == (3,)
    
    def test_nan_raises_error(self):
        data = np.array([0.1, np.nan, 0.9])
        with pytest.raises(ValueError, match="NaN"):
            validate_input(data)
    
    def test_inf_raises_error(self):
        data = np.array([0.1, np.inf, 0.9])
        with pytest.raises(ValueError, match="infinite"):
            validate_input(data)


class TestKMeansNeutrosophic:
    """
    Tests for K-Means method (Proposed).
    
    Verifies Equations 2, 3, 4 from paper:
    - T(x) = 1 / (1 + exp(-10·(x - c_high)/(σ_high + ε)))
    - I(x) = 1 / (1 + |x - c_mid|/(σ_mid + ε))
    - F(x) = 1 / (1 + exp(10·(x - c_low)/(σ_low + ε)))
    """
    
    def test_fit_transform_shape(self):
        """Output shape should match input shape."""
        np.random.seed(42)
        data = np.random.random(100)
        
        method = KMeansNeutrosophic(random_state=42)
        T, I, F = method.fit_transform(data)
        
        assert T.shape == (100,)
        assert I.shape == (100,)
        assert F.shape == (100,)
    
    def test_values_in_range(self):
        """All T, I, F values should be in [0, 1]."""
        np.random.seed(42)
        data = np.random.random(100)
        
        method = KMeansNeutrosophic(random_state=42)
        T, I, F = method.fit_transform(data)
        
        assert np.all(T >= 0) and np.all(T <= 1)
        assert np.all(I >= 0) and np.all(I <= 1)
        assert np.all(F >= 0) and np.all(F <= 1)
    
    def test_tif_sum_less_than_fuzzy(self):
        """K-Means T+I+F sum should be less than 1 (true neutrosophic)."""
        np.random.seed(42)
        data = np.random.random(100)
        
        method = KMeansNeutrosophic(random_state=42)
        T, I, F = method.fit_transform(data)
        
        mean_sum = np.mean(T + I + F)
        # Paper reports ≈ 0.639, should be less than 1
        assert mean_sum < 1.0
    
    def test_tf_independence(self):
        """K-Means should have LOW T+F consistency (independent T, F)."""
        np.random.seed(42)
        data = np.random.random(100)
        
        method = KMeansNeutrosophic(random_state=42)
        T, I, F = method.fit_transform(data)
        
        consistency = compute_tf_consistency(T, F)
        # Paper reports ≈ 0.291, should be much less than 1
        assert consistency < 0.5
    
    def test_centroids_sorted(self):
        """Centroids should be sorted: c_low < c_mid < c_high."""
        np.random.seed(42)
        data = np.random.random(100)
        
        method = KMeansNeutrosophic(random_state=42)
        method.fit(data)
        
        params = method.get_parameters()
        assert params['c_low'] < params['c_mid'] < params['c_high']
    
    def test_not_fitted_raises_error(self):
        method = KMeansNeutrosophic()
        with pytest.raises(ValueError, match="fitted"):
            method.transform(np.array([0.5]))


class TestParabolicNeutrosophic:
    """
    Tests for Parabolic method (Classical).
    
    Verifies Equation 5 from paper:
    - T(x) = x
    - I(x) = 4·x·(1-x)·α
    - F(x) = 1 - x
    """
    
    def test_truth_equals_input(self):
        """T(x) should equal x."""
        data = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
        method = ParabolicNeutrosophic(alpha=0.5)
        T, I, F = method.fit_transform(data)
        
        np.testing.assert_array_almost_equal(T, data)
    
    def test_falsity_complement(self):
        """F(x) should equal 1 - x."""
        data = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
        method = ParabolicNeutrosophic(alpha=0.5)
        T, I, F = method.fit_transform(data)
        
        np.testing.assert_array_almost_equal(F, 1 - data)
    
    def test_indeterminacy_parabolic(self):
        """I(x) = 4·x·(1-x)·α, maximum at x=0.5."""
        data = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
        method = ParabolicNeutrosophic(alpha=0.5)
        T, I, F = method.fit_transform(data)
        
        # At x=0.5: I = 4*0.5*0.5*0.5 = 0.5
        assert I[2] == pytest.approx(0.5, abs=1e-6)
        
        # At x=0 or x=1: I = 0
        assert I[0] == pytest.approx(0, abs=1e-6)
        assert I[4] == pytest.approx(0, abs=1e-6)
    
    def test_tf_complementarity(self):
        """Parabolic should have T+F=1 (fuzzy complementarity)."""
        data = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
        method = ParabolicNeutrosophic(alpha=0.5)
        T, I, F = method.fit_transform(data)
        
        np.testing.assert_array_almost_equal(T + F, np.ones(5))
    
    def test_invalid_alpha_raises(self):
        with pytest.raises(ValueError):
            ParabolicNeutrosophic(alpha=0)
        with pytest.raises(ValueError):
            ParabolicNeutrosophic(alpha=1.5)


class TestThresholdNeutrosophic:
    """
    Tests for Threshold method (Semi-novel).
    
    Verifies Equation 7 from paper:
    - T(x) = 1 / (1 + exp(-10·(x - θ)))
    - I(x) = exp(-λ·(x - θ)²)
    - F(x) = 1 - T(x)
    """
    
    def test_indeterminacy_max_at_threshold(self):
        """I(x) should be maximum (=1) at x = θ."""
        data = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
        method = ThresholdNeutrosophic(theta=0.5, lambda_=5.0)
        T, I, F = method.fit_transform(data)
        
        # At x=θ=0.5: I = exp(0) = 1
        assert I[2] == pytest.approx(1.0, abs=1e-6)
    
    def test_tf_complementarity(self):
        """Threshold should have F = 1 - T."""
        data = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
        method = ThresholdNeutrosophic(theta=0.5, lambda_=5.0)
        T, I, F = method.fit_transform(data)
        
        np.testing.assert_array_almost_equal(T + F, np.ones(5))
    
    def test_sigmoid_behavior(self):
        """T should be sigmoid: T(θ) ≈ 0.5, T(low) ≈ 0, T(high) ≈ 1."""
        method = ThresholdNeutrosophic(theta=0.5)
        T, I, F = method.fit_transform(np.array([0.5]))
        
        assert T[0] == pytest.approx(0.5, abs=1e-6)


class TestKDENeutrosophic:
    """
    Tests for KDE method (Established).
    
    Verifies Equations 8, 9, 11 from paper:
    - T(x) = x
    - I(x) = 1 - f̂_norm(x)
    - F(x) = 1 - x
    """
    
    def test_truth_equals_input(self):
        """T(x) should equal x."""
        np.random.seed(42)
        data = np.random.random(50)
        
        method = KDENeutrosophic()
        T, I, F = method.fit_transform(data)
        
        np.testing.assert_array_almost_equal(T, np.clip(data, 0, 1))
    
    def test_falsity_complement(self):
        """F(x) should equal 1 - x."""
        np.random.seed(42)
        data = np.random.random(50)
        
        method = KDENeutrosophic()
        T, I, F = method.fit_transform(data)
        
        expected_F = 1 - np.clip(data, 0, 1)
        np.testing.assert_array_almost_equal(F, expected_F)
    
    def test_indeterminacy_in_range(self):
        """I should be in [0, 1]."""
        np.random.seed(42)
        data = np.random.random(50)
        
        method = KDENeutrosophic()
        T, I, F = method.fit_transform(data)
        
        assert np.all(I >= 0) and np.all(I <= 1)


class TestFuzzyNeutrosophic:
    """
    Tests for Fuzzy method (Classical).
    
    Verifies Equation 12 and fuzzy sets from paper:
    - Low: (-0.5, 0.0, 0.5)
    - Medium: (0.25, 0.5, 0.75)
    - High: (0.5, 1.0, 1.5)
    """
    
    def test_default_fuzzy_sets(self):
        """Default parameters should match paper values."""
        method = FuzzyNeutrosophic()
        params = method.get_parameters()
        
        assert params['params_low'] == (-0.5, 0.0, 0.5)
        assert params['params_medium'] == (0.25, 0.5, 0.75)
        assert params['params_high'] == (0.5, 1.0, 1.5)
    
    def test_truth_equals_input(self):
        """T(x) should equal x."""
        data = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
        method = FuzzyNeutrosophic()
        T, I, F = method.fit_transform(data)
        
        np.testing.assert_array_almost_equal(T, data)
    
    def test_falsity_complement(self):
        """F(x) should equal 1 - x."""
        data = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
        method = FuzzyNeutrosophic()
        T, I, F = method.fit_transform(data)
        
        np.testing.assert_array_almost_equal(F, 1 - data)
    
    def test_membership_values(self):
        """Test individual fuzzy membership values."""
        method = FuzzyNeutrosophic()
        
        # At x=0: Low membership should be 1 (peak at b_L=0)
        memberships = method.get_membership_values(np.array([0.0]))
        assert memberships['low'][0] == pytest.approx(1.0, abs=1e-6)
        
        # At x=0.5: Medium membership should be 1 (peak at b_M=0.5)
        memberships = method.get_membership_values(np.array([0.5]))
        assert memberships['medium'][0] == pytest.approx(1.0, abs=1e-6)
        
        # At x=1: High membership should be 1 (peak at b_H=1.0)
        memberships = method.get_membership_values(np.array([1.0]))
        assert memberships['high'][0] == pytest.approx(1.0, abs=1e-6)


class TestComputeStatistics:
    """Tests for statistics computation (Eq. 13-15 from paper)."""
    
    def test_tf_consistency_metric(self):
        """T+F Consistency = 1 − mean(|T + F − 1|)"""
        # Perfect complementarity: T + F = 1
        T = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
        F = np.array([1.0, 0.75, 0.5, 0.25, 0.0])
        
        from neutrolab.utils import compute_tf_consistency
        consistency = compute_tf_consistency(T, F)
        
        assert consistency == pytest.approx(1.0, abs=1e-6)
    
    def test_statistics_keys(self):
        """compute_statistics should return all required metrics."""
        T = np.array([0.1, 0.5, 0.9])
        I = np.array([0.2, 0.4, 0.2])
        F = np.array([0.9, 0.5, 0.1])
        
        stats = compute_statistics(T, I, F)
        
        # Check key metrics from paper
        assert 'mean_sum' in stats  # T+I+F sum
        assert 'tf_consistency' in stats  # Eq. 13
        assert 'indeterminacy_range' in stats  # Eq. 14
        assert 'entropy_I' in stats  # Eq. 15


class TestMethodComparison:
    """Integration tests comparing all methods."""
    
    def test_all_methods_work(self):
        """All five methods should run without errors."""
        np.random.seed(42)
        data = np.random.random(50)
        
        methods = [
            KMeansNeutrosophic(random_state=42),
            ParabolicNeutrosophic(),
            ThresholdNeutrosophic(),
            KDENeutrosophic(),
            FuzzyNeutrosophic()
        ]
        
        for method in methods:
            T, I, F = method.fit_transform(data)
            assert T.shape == (50,)
            assert I.shape == (50,)
            assert F.shape == (50,)
    
    def test_kmeans_unique_independence(self):
        """K-Means should be the only method with T+F independence."""
        np.random.seed(42)
        data = np.random.random(100)
        
        methods = {
            'K-Means': KMeansNeutrosophic(random_state=42),
            'Parabolic': ParabolicNeutrosophic(),
            'Threshold': ThresholdNeutrosophic(),
            'KDE': KDENeutrosophic(),
            'Fuzzy': FuzzyNeutrosophic()
        }
        
        consistencies = {}
        for name, method in methods.items():
            T, I, F = method.fit_transform(data)
            consistencies[name] = compute_tf_consistency(T, F)
        
        # K-Means should have significantly lower T+F consistency
        assert consistencies['K-Means'] < 0.5
        
        # Other methods should have high T+F consistency (≈ 1)
        for name in ['Parabolic', 'Threshold', 'KDE', 'Fuzzy']:
            assert consistencies[name] > 0.99


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
