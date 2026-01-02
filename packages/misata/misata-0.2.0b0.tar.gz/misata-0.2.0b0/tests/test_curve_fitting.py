
"""
Tests for Mathematical Graph Solver (Curve Fitting).
"""

import pytest
import numpy as np
from misata.curve_fitting import CurveFitter
from scipy.stats import norm

class TestCurveFitting:
    """Tests for CurveFitter using scipy.optimize."""
    
    def test_fit_normal_distribution(self):
        """Test fitting a normal distribution to points."""
        fitter = CurveFitter()
        
        # Ground truth: Mean=100, Std=10
        target_dist = norm(loc=100, scale=10)
        
        # Create control points
        points = []
        for x in [80, 90, 100, 110, 120]:
            points.append({"x": x, "y": target_dist.pdf(x)})
            
        params = fitter.fit_distribution(points, "normal")
        
        print(f"Fitted Params: {params}")
        
        # Allow small error margin due to optimization
        assert 99 <= params["mean"] <= 101
        assert 9 <= params["std"] <= 11

    def test_fit_exponential_distribution(self):
        """Test fitting an exponential distribution."""
        fitter = CurveFitter()
        
        # Ground truth: Scale=10 (Lambda=0.1)
        # PDF = (1/scale) * exp(-x/scale)
        # x=10 -> 0.1 * e^-1 ~ 0.036
        
        points = [
            {"x": 5, "y": 0.06}, # approx
            {"x": 10, "y": 0.036},
            {"x": 20, "y": 0.013}
        ]
        
        params = fitter.fit_distribution(points, "exponential")
        print(f"Fitted Expo Params: {params}")
        
        # Should be roughly 10
        assert 8 <= params["scale"] <= 12

    def test_fit_unknown_distribution(self):
        """Test error handling for unknown distribution."""
        fitter = CurveFitter()
        with pytest.raises(ValueError):
            fitter.fit_distribution([], "unknown_dist")
