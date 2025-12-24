"""
Tests for OMPC simulator.

Verifies implementation from docs/manual/part_5.md section 5.7.
"""

import pytest

import lulzprime
from lulzprime.diagnostics import simulator_diagnostics
from lulzprime.pi import pi


class TestSimulator:
    """Test simulate() function."""

    def test_simulate_basic(self):
        """Test basic simulation functionality."""
        result = lulzprime.simulate(10, seed=42)

        assert isinstance(result, list)
        assert len(result) == 10
        assert all(isinstance(q, int) for q in result)

    def test_simulate_determinism(self):
        """Test that simulation is deterministic with fixed seed."""
        result1 = lulzprime.simulate(50, seed=123)
        result2 = lulzprime.simulate(50, seed=123)

        assert result1 == result2

    def test_simulate_different_seeds(self):
        """Test that different seeds give different results."""
        result1 = lulzprime.simulate(50, seed=1)
        result2 = lulzprime.simulate(50, seed=2)

        # Should be different (extremely unlikely to be same)
        assert result1 != result2

    def test_simulate_with_diagnostics(self):
        """Test simulation with diagnostics enabled."""
        result, diag = lulzprime.simulate(100, seed=42, diagnostics=True)

        assert isinstance(result, list)
        assert len(result) == 100

        assert isinstance(diag, list)
        assert len(diag) > 0

        # Check diagnostic structure
        for entry in diag:
            assert "step" in entry
            assert "q" in entry
            assert "w" in entry

    def test_simulate_increasing_sequence(self):
        """Test that simulated sequence is strictly increasing."""
        result = lulzprime.simulate(100, seed=42)

        for i in range(1, len(result)):
            assert result[i] > result[i - 1], f"Not increasing at index {i}"

    def test_simulate_convergence(self):
        """Test that simulator shows expected convergence behavior."""
        # Run longer simulation
        result = lulzprime.simulate(200, seed=42)

        # Use diagnostics to check convergence
        diag = simulator_diagnostics(result, pi)

        # Should show reasonable convergence (Part 7, section 7.4)
        assert diag["convergence_acceptable"], "Simulator not converging properly"
        assert abs(diag["density_ratio"] - 1.0) < 0.2, "Density ratio too far from 1.0"

    def test_simulate_input_validation(self):
        """Test simulate() input validation."""
        with pytest.raises(ValueError):
            lulzprime.simulate(0)

        with pytest.raises(ValueError):
            lulzprime.simulate(-5)
