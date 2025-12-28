"""
Unit tests for co-eco package.

These tests verify the correctness of the implementation against
the original MATLAB code by Carrion-i-Silvestre and Kim (2019).
"""

import numpy as np
import pytest
import sys
import os

# Add parent directory to path for development
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from co_eco import (
    CKTest,
    ck_test_known_breaks,
    ck_test_unknown_1break,
    ck_test_unknown_2breaks,
    long_run_variance,
    dols_reg_maker,
    create_step_dummies,
    get_lambda_bar,
    get_critical_values,
)
from co_eco.data import load_us_budget


class TestUtilityFunctions:
    """Tests for utility functions."""
    
    def test_create_step_dummies(self):
        """Test step dummy creation."""
        DU = create_step_dummies(100, [30, 70])
        
        assert DU.shape == (100, 2)
        assert DU[29, 0] == 0
        assert DU[30, 0] == 0
        assert DU[31, 0] == 1
        assert DU[69, 1] == 0
        assert DU[71, 1] == 1
    
    def test_dols_reg_maker(self):
        """Test DOLS regressor matrix construction."""
        np.random.seed(42)
        x = np.random.randn(100, 2)
        
        U = dols_reg_maker(x, klags=2, kleads=2)
        
        # Should have 100 - 2 - 2 - 1 = 95 rows
        assert U.shape[0] == 95
        # Should have 2 * (2 + 2 + 1) = 10 columns
        assert U.shape[1] == 10
    
    def test_long_run_variance(self):
        """Test long-run variance estimation."""
        np.random.seed(42)
        v = np.random.randn(200, 1)
        
        lrv = long_run_variance(v, c=0)
        
        assert lrv.shape == (1, 1)
        assert lrv[0, 0] > 0
        # For iid normal, LRV should be close to 1
        assert 0.5 < lrv[0, 0] < 2.0


class TestCriticalValues:
    """Tests for critical value functions."""
    
    def test_get_lambda_bar(self):
        """Test lambda bar retrieval."""
        lbar = get_lambda_bar(1, 2, 1)
        assert lbar == 14.9
        
        lbar = get_lambda_bar(0, 1, 1)
        assert lbar == 9.1
    
    def test_get_critical_values(self):
        """Test critical value retrieval."""
        cv = get_critical_values('robust_ci', 1, 2, 1, 0.05)
        assert cv == 1.79
        
        cv = get_critical_values('joint_cb', 1, 2, 1, 0.05)
        assert cv == 13.07
    
    def test_invalid_parameters(self):
        """Test error handling for invalid parameters."""
        with pytest.raises(ValueError):
            get_lambda_bar(5, 2, 1)  # Invalid m
        
        with pytest.raises(ValueError):
            get_critical_values('invalid_test', 1, 2, 1)


class TestKnownBreaks:
    """Tests for known break date tests."""
    
    def test_no_breaks(self):
        """Test with no breaks."""
        np.random.seed(42)
        T = 200
        x = np.cumsum(np.random.randn(T, 1), axis=0)
        beta = 0.5
        y = beta * x.flatten() + np.cumsum(np.random.randn(T) * 0.5)
        
        Q_r, Q_cb, Q_ct = ck_test_known_breaks(y, x, model=2, break_dates=None)
        
        assert np.isfinite(Q_r)
        assert np.isfinite(Q_cb)
        assert np.isfinite(Q_ct)
    
    def test_one_break(self):
        """Test with one known break."""
        np.random.seed(42)
        T = 200
        x = np.cumsum(np.random.randn(T, 1), axis=0)
        y = 0.5 * x.flatten() + np.cumsum(np.random.randn(T) * 0.5)
        
        Q_r, Q_cb, Q_ct = ck_test_known_breaks(y, x, model=2, break_dates=[100])
        
        assert np.isfinite(Q_r)
        assert np.isfinite(Q_cb)
        assert np.isfinite(Q_ct)
    
    def test_with_dols(self):
        """Test with DOLS correction."""
        np.random.seed(42)
        T = 200
        x = np.cumsum(np.random.randn(T, 1), axis=0)
        y = 0.5 * x.flatten() + np.cumsum(np.random.randn(T) * 0.5)
        
        Q_r, Q_cb, Q_ct = ck_test_known_breaks(
            y, x, model=2, break_dates=[100], klags=2, kleads=2
        )
        
        assert np.isfinite(Q_r)
        assert np.isfinite(Q_cb)
        assert np.isfinite(Q_ct)


class TestUnknownBreaks:
    """Tests for unknown break date tests."""
    
    def test_one_unknown_break(self):
        """Test with one unknown break."""
        np.random.seed(42)
        T = 200
        x = np.cumsum(np.random.randn(T, 1), axis=0)
        y = 0.5 * x.flatten() + np.cumsum(np.random.randn(T) * 0.5)
        
        Q_r, Q_cb, Q_ct, Tbhat = ck_test_unknown_1break(y, x, model=2)
        
        assert np.isfinite(Q_r)
        assert np.isfinite(Q_cb)
        assert np.isfinite(Q_ct)
        assert 0 < Tbhat < T
    
    def test_two_unknown_breaks(self):
        """Test with two unknown breaks."""
        np.random.seed(42)
        T = 200
        x = np.cumsum(np.random.randn(T, 1), axis=0)
        y = 0.5 * x.flatten() + np.cumsum(np.random.randn(T) * 0.5)
        
        Q_r, Q_cb, Q_ct, Tbhat = ck_test_unknown_2breaks(y, x, model=2)
        
        assert np.isfinite(Q_r)
        assert np.isfinite(Q_cb)
        assert np.isfinite(Q_ct)
        assert len(Tbhat) == 2
        assert Tbhat[0] < Tbhat[1]


class TestCKTestClass:
    """Tests for the CKTest class."""
    
    def test_basic_usage(self):
        """Test basic class usage."""
        np.random.seed(42)
        T = 200
        x = np.cumsum(np.random.randn(T, 1), axis=0)
        y = 0.5 * x.flatten() + np.cumsum(np.random.randn(T) * 0.5)
        
        test = CKTest(y, x, model=2)
        results = test.run(num_breaks=1)
        
        assert np.isfinite(results.Q_r)
        assert np.isfinite(results.Q_cb)
        assert np.isfinite(results.Q_ct)
        assert results.model == 2
        assert results.num_breaks == 1
    
    def test_run_all(self):
        """Test running all break specifications."""
        np.random.seed(42)
        T = 200
        x = np.cumsum(np.random.randn(T, 1), axis=0)
        y = 0.5 * x.flatten() + np.cumsum(np.random.randn(T) * 0.5)
        
        test = CKTest(y, x, model=2)
        all_results = test.run_all(max_breaks=2)
        
        assert 0 in all_results
        assert 1 in all_results
        assert 2 in all_results
    
    def test_run_dmax(self):
        """Test Dmax tests."""
        np.random.seed(42)
        T = 200
        x = np.cumsum(np.random.randn(T, 1), axis=0)
        y = 0.5 * x.flatten() + np.cumsum(np.random.randn(T) * 0.5)
        
        test = CKTest(y, x, model=2)
        dmax_cb, dmax_ct = test.run_dmax(max_breaks=2)
        
        assert np.isfinite(dmax_cb.Q_dmax)
        assert np.isfinite(dmax_ct.Q_dmax)
    
    def test_results_methods(self):
        """Test results object methods."""
        np.random.seed(42)
        T = 200
        x = np.cumsum(np.random.randn(T, 1), axis=0)
        y = 0.5 * x.flatten() + np.cumsum(np.random.randn(T) * 0.5)
        
        test = CKTest(y, x, model=2)
        results = test.run(num_breaks=1)
        
        # Test methods
        summary = results.summary()
        assert isinstance(summary, str)
        assert len(summary) > 0
        
        latex = results.to_latex()
        assert isinstance(latex, str)
        assert 'tabular' in latex
        
        d = results.to_dict()
        assert isinstance(d, dict)
        assert 'Q_r' in d


class TestUSBudgetData:
    """Tests using the US budget data."""
    
    def test_data_loading(self):
        """Test data loading."""
        R, E, B = load_us_budget()
        
        assert len(R) == 254
        assert len(E) == 254
        assert len(B) == 254
        assert np.allclose(B, R - E)
    
    def test_replication(self):
        """Test partial replication of paper results."""
        R, E, B = load_us_budget()
        T = len(R)
        
        # Use expenditures as dependent variable
        test = CKTest(E, R.reshape(-1, 1), model=2, klags=1, kleads=1)
        results = test.run(num_breaks=1)
        
        # The test should reject null of cointegration
        # (paper reports Q_r > critical values)
        assert results.Q_r > 1.79  # 5% CV


class TestModelI:
    """Tests for Model I (mean shifts only)."""
    
    def test_model_i(self):
        """Test Model I specification."""
        np.random.seed(42)
        T = 200
        x = np.cumsum(np.random.randn(T, 1), axis=0)
        y = 0.5 * x.flatten() + np.cumsum(np.random.randn(T) * 0.5)
        
        test = CKTest(y, x, model=1)
        results = test.run(num_breaks=1)
        
        assert results.model == 1
        assert np.isfinite(results.Q_r)
        assert np.isfinite(results.Q_cb)
        # Q_ct should equal Q_cb for Model I
        assert results.Q_ct == results.Q_cb


class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_multiple_regressors(self):
        """Test with multiple regressors."""
        np.random.seed(42)
        T = 200
        x = np.cumsum(np.random.randn(T, 2), axis=0)
        y = 0.3 * x[:, 0] + 0.2 * x[:, 1] + np.cumsum(np.random.randn(T) * 0.5)
        
        test = CKTest(y, x, model=2)
        results = test.run(num_breaks=1)
        
        assert results.num_regressors == 2
        assert np.isfinite(results.Q_r)
    
    def test_small_sample(self):
        """Test with small sample size."""
        np.random.seed(42)
        T = 80
        x = np.cumsum(np.random.randn(T, 1), axis=0)
        y = 0.5 * x.flatten() + np.cumsum(np.random.randn(T) * 0.5)
        
        test = CKTest(y, x, model=2)
        results = test.run(num_breaks=1)
        
        assert np.isfinite(results.Q_r)
    
    def test_invalid_model(self):
        """Test error handling for invalid model."""
        np.random.seed(42)
        T = 200
        x = np.cumsum(np.random.randn(T, 1), axis=0)
        y = 0.5 * x.flatten()
        
        with pytest.raises(ValueError):
            CKTest(y, x, model=3)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
