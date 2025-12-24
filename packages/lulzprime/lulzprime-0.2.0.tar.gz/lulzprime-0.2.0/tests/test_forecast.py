"""
Tests for forecast() refinement levels and accuracy guarantees.

Validates v0.2.0 contract compliance per docs/0.2.0/part_2.md and part_6.md.
"""

import pytest

import lulzprime
from lulzprime import forecast


class TestForecastRefinementLevels:
    """Test refinement_level parameter and level-specific behavior."""

    def test_level_1_backward_compatibility(self):
        """Level 1 must maintain v0.1.2 behavior (contract requirement)."""
        # Test default parameter (refinement_level=1 is default)
        result_default = forecast(1000000)
        result_explicit = forecast(1000000, refinement_level=1)
        assert result_default == result_explicit

        # Known value from Part 6 accuracy table
        # Level 1 for n=10^6: ~15,441,302 (0.29% error)
        result = forecast(1000000, refinement_level=1)
        expected_approx = 15_441_302
        # Allow ±1% variance due to rounding changes
        assert abs(result - expected_approx) < 155_000

    def test_level_2_improved_accuracy(self):
        """Level 2 must provide <0.2% error for large n (contract requirement)."""
        # Known value from Part 6 accuracy table
        # Level 2 for n=10^6: ~15,479,821 (0.039% error)
        # Actual p_10^6 = 15,485,863
        result = forecast(1000000, refinement_level=2)
        actual = 15_485_863
        expected_approx = 15_479_821

        # Verify result is close to documented approximation
        assert abs(result - expected_approx) < 10_000

        # Verify improved accuracy vs actual (should be <0.2%)
        relative_error = abs(result - actual) / actual
        assert relative_error < 0.002  # <0.2%

    def test_level_2_better_than_level_1(self):
        """Level 2 must be more accurate than Level 1 for large n."""
        n = 10_000_000
        actual = 179_424_673  # p_10^7 from Part 6 table

        result_l1 = forecast(n, refinement_level=1)
        result_l2 = forecast(n, refinement_level=2)

        error_l1 = abs(result_l1 - actual) / actual
        error_l2 = abs(result_l2 - actual) / actual

        # Level 2 must have smaller error
        assert error_l2 < error_l1

        # Level 2 should be <0.2% (Part 6 contract)
        assert error_l2 < 0.002

    def test_level_3_reserved(self):
        """Level 3 is reserved for future but must not crash."""
        # Should execute without error
        result = forecast(1000000, refinement_level=3)
        assert isinstance(result, int)
        assert result > 0

    def test_invalid_refinement_level_rejected(self):
        """refinement_level must be 1, 2, or 3 (contract requirement)."""
        with pytest.raises(ValueError, match="refinement_level must be 1, 2, or 3"):
            forecast(1000, refinement_level=0)

        with pytest.raises(ValueError, match="refinement_level must be 1, 2, or 3"):
            forecast(1000, refinement_level=4)

        with pytest.raises(ValueError, match="refinement_level must be 1, 2, or 3"):
            forecast(1000, refinement_level=-1)


class TestForecastDeterminism:
    """Test deterministic behavior across refinement levels."""

    def test_determinism_level_1(self):
        """Level 1 must be deterministic."""
        result1 = forecast(100000, refinement_level=1)
        result2 = forecast(100000, refinement_level=1)
        assert result1 == result2

    def test_determinism_level_2(self):
        """Level 2 must be deterministic."""
        result1 = forecast(100000, refinement_level=2)
        result2 = forecast(100000, refinement_level=2)
        assert result1 == result2

    def test_different_levels_different_results(self):
        """Different refinement levels must produce different results for large n."""
        n = 1000000
        result_l1 = forecast(n, refinement_level=1)
        result_l2 = forecast(n, refinement_level=2)

        # Should differ for large n
        assert result_l1 != result_l2


class TestForecastSmallIndices:
    """Test that small indices use hardcoded values regardless of level."""

    def test_small_indices_exact(self):
        """Small indices should use exact hardcoded values."""
        # First 10 primes: 2, 3, 5, 7, 11, 13, 17, 19, 23, 29
        assert forecast(1) == 2
        assert forecast(2) == 3
        assert forecast(10) == 29

    def test_small_indices_independent_of_level(self):
        """Small indices should be same across refinement levels."""
        for n in [1, 5, 10, 20]:
            result_l1 = forecast(n, refinement_level=1)
            result_l2 = forecast(n, refinement_level=2)
            # Should be identical (uses hardcoded table)
            assert result_l1 == result_l2


class TestForecastAccuracyBounds:
    """Test accuracy bounds per Part 2 and Part 6 contracts."""

    def test_level_1_accuracy_at_10e6(self):
        """Level 1: <0.3% error for n ≥ 10^6 (Part 2 contract)."""
        n = 1_000_000
        actual = 15_485_863  # Known p_10^6
        result = forecast(n, refinement_level=1)

        relative_error = abs(result - actual) / actual
        assert relative_error < 0.003  # <0.3%

    def test_level_2_accuracy_at_10e8(self):
        """Level 2: <0.2% error for n ≥ 10^8 (Part 2 contract)."""
        n = 100_000_000
        actual = 2_038_074_743  # Known p_10^8
        result = forecast(n, refinement_level=2)

        relative_error = abs(result - actual) / actual
        assert relative_error < 0.002  # <0.2%

    def test_level_2_accuracy_at_10e9(self):
        """Level 2 maintains accuracy at 10^9 (Part 6 table validation)."""
        n = 1_000_000_000
        actual = 22_801_763_489  # Known p_10^9
        result = forecast(n, refinement_level=2)

        relative_error = abs(result - actual) / actual
        # Part 6 shows 0.010% error at this scale
        assert relative_error < 0.0002  # <0.02% (even better than contract)
