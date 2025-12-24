"""
Tests for gap distribution and sampling (gaps.py).

Validates CDF-based sampling implementation (Phase 2 optimization).
"""

import random

import pytest

from lulzprime.gaps import (
    get_empirical_gap_distribution,
    sample_gap,
    tilt_gap_distribution,
)


class TestGapSampling:
    """Test gap sampling with CDF + bisect optimization."""

    def test_sample_gap_determinism(self):
        """Test that sampling with fixed seed is deterministic."""
        distribution = {2: 0.4, 4: 0.3, 6: 0.2, 8: 0.1}

        # Sample with seed
        random.seed(42)
        result1 = [sample_gap(distribution) for _ in range(100)]

        # Reseed and sample again
        random.seed(42)
        result2 = [sample_gap(distribution) for _ in range(100)]

        # Must be identical for determinism
        assert result1 == result2, "Sampling must be deterministic with same seed"

    def test_sample_gap_distribution_coverage(self):
        """Test that all gaps in distribution can be sampled."""
        distribution = {2: 0.25, 4: 0.25, 6: 0.25, 8: 0.25}

        # Sample many times
        random.seed(123)
        samples = [sample_gap(distribution) for _ in range(1000)]

        # All gaps should appear at least once
        sampled_gaps = set(samples)
        expected_gaps = set(distribution.keys())

        assert sampled_gaps == expected_gaps, "All gaps must be sampled eventually"

    def test_sample_gap_respects_probabilities(self):
        """Test that sampling respects probability distribution (statistical)."""
        # Heavily biased distribution
        distribution = {2: 0.8, 4: 0.15, 6: 0.04, 8: 0.01}

        # Sample many times
        random.seed(456)
        samples = [sample_gap(distribution) for _ in range(10000)]

        # Count frequencies
        counts = {g: samples.count(g) for g in distribution.keys()}
        frequencies = {g: counts[g] / len(samples) for g in distribution.keys()}

        # Check that observed frequencies are close to expected (within tolerance)
        for gap, expected_prob in distribution.items():
            observed_prob = frequencies[gap]
            # Allow 10% relative error for statistical test
            assert abs(observed_prob - expected_prob) < 0.1 * expected_prob or abs(
                observed_prob - expected_prob
            ) < 0.01, f"Gap {gap}: expected {expected_prob:.3f}, got {observed_prob:.3f}"

    def test_sample_gap_single_element(self):
        """Test sampling from single-element distribution."""
        distribution = {42: 1.0}

        random.seed(789)
        samples = [sample_gap(distribution) for _ in range(10)]

        # All samples should be 42
        assert all(s == 42 for s in samples), "Single-element distribution must always return that element"

    def test_sample_gap_normalized_distribution(self):
        """Test that sampling works with unnormalized distributions."""
        # Unnormalized (sums to 2.0)
        distribution = {2: 0.8, 4: 0.6, 6: 0.4, 8: 0.2}

        random.seed(321)
        samples = [sample_gap(distribution) for _ in range(100)]

        # Should still produce valid gaps
        assert all(g in distribution.keys() for g in samples)

    def test_sample_gap_returns_valid_gap(self):
        """Test that sampled gap is always in the distribution."""
        distribution = get_empirical_gap_distribution(max_gap=100)

        random.seed(111)
        samples = [sample_gap(distribution) for _ in range(500)]

        # All samples must be valid gaps from distribution
        for gap in samples:
            assert gap in distribution, f"Sampled gap {gap} not in distribution"

    def test_sample_gap_cdf_correctness(self):
        """Test that CDF is built correctly (strictly increasing, ends at 1.0)."""
        distribution = {2: 0.1, 4: 0.2, 6: 0.3, 8: 0.4}

        # Build CDF manually to verify
        gaps = sorted(distribution.keys())
        cumulative = []
        total = 0.0
        for gap in gaps:
            total += distribution[gap]
            cumulative.append(total)

        # Normalize
        cumulative = [c / cumulative[-1] for c in cumulative]

        # Check properties
        # 1. Strictly increasing (or equal for ties)
        for i in range(1, len(cumulative)):
            assert cumulative[i] >= cumulative[i - 1], "CDF must be non-decreasing"

        # 2. Ends at 1.0 (within floating point tolerance)
        assert abs(cumulative[-1] - 1.0) < 1e-10, "CDF must end at 1.0"

        # 3. All values in [0, 1]
        assert all(0 <= c <= 1 for c in cumulative), "CDF values must be in [0, 1]"


class TestTiltedDistribution:
    """Test tilted distribution computation."""

    def test_tilt_distribution_normalized(self):
        """Test that tilted distribution sums to 1.0."""
        base_dist = {2: 0.4, 4: 0.3, 6: 0.2, 8: 0.1}
        w = 0.9
        beta = 2.0

        tilted = tilt_gap_distribution(base_dist, w, beta)

        # Sum should be 1.0
        total = sum(tilted.values())
        assert abs(total - 1.0) < 1e-10, f"Tilted distribution should sum to 1.0, got {total}"

    def test_tilt_distribution_positive_weights(self):
        """Test that all tilted weights are positive."""
        base_dist = get_empirical_gap_distribution(max_gap=50)
        w = 1.05
        beta = 1.5

        tilted = tilt_gap_distribution(base_dist, w, beta)

        # All weights should be positive
        assert all(p > 0 for p in tilted.values()), "All tilted probabilities must be positive"

    def test_tilt_distribution_w_less_than_1(self):
        """Test tilting when w < 1 (too dense, favor larger gaps)."""
        base_dist = {2: 0.5, 4: 0.3, 6: 0.15, 8: 0.05}
        w = 0.8  # Too dense
        beta = 2.0

        tilted = tilt_gap_distribution(base_dist, w, beta)

        # When w < 1, larger gaps should get relatively more weight
        # Check that gap=8 has higher relative weight vs base distribution
        base_ratio = base_dist[8] / base_dist[2]  # Ratio of largest to smallest
        tilted_ratio = tilted[8] / tilted[2]

        assert tilted_ratio > base_ratio, "Larger gaps should be favored when w < 1"

    def test_tilt_distribution_w_greater_than_1(self):
        """Test tilting when w > 1 (too sparse, favor smaller gaps)."""
        base_dist = {2: 0.5, 4: 0.3, 6: 0.15, 8: 0.05}
        w = 1.2  # Too sparse
        beta = 2.0

        tilted = tilt_gap_distribution(base_dist, w, beta)

        # When w > 1, smaller gaps should get relatively more weight
        base_ratio = base_dist[2] / base_dist[8]  # Ratio of smallest to largest
        tilted_ratio = tilted[2] / tilted[8]

        assert tilted_ratio > base_ratio, "Smaller gaps should be favored when w > 1"


class TestSimulationDeterminism:
    """Test that simulation maintains determinism with new sampling."""

    def test_simulation_determinism_across_runs(self):
        """Test that simulate() with fixed seed is deterministic."""
        import lulzprime

        result1 = lulzprime.simulate(500, seed=42)
        result2 = lulzprime.simulate(500, seed=42)

        assert result1 == result2, "Simulation must be deterministic with same seed"

    def test_simulation_list_vs_generator_determinism(self):
        """Test that list mode and generator mode produce identical results."""
        import lulzprime

        # List mode
        list_result = lulzprime.simulate(300, seed=999)

        # Generator mode
        gen_result = list(lulzprime.simulate(300, seed=999, as_generator=True))

        # Must be identical
        assert list_result == gen_result, "List and generator modes must be identical"

    def test_simulation_with_annealing_determinism(self):
        """Test that annealing mode is deterministic with new sampling."""
        import lulzprime

        result1 = lulzprime.simulate(400, seed=1337, anneal_tau=1000)
        result2 = lulzprime.simulate(400, seed=1337, anneal_tau=1000)

        assert result1 == result2, "Annealed simulation must be deterministic"


class TestEmpiricalDistribution:
    """Test empirical gap distribution generation."""

    def test_empirical_distribution_normalized(self):
        """Test that empirical distribution sums to 1.0."""
        dist = get_empirical_gap_distribution(max_gap=100)

        total = sum(dist.values())
        assert abs(total - 1.0) < 1e-10, f"Distribution should sum to 1.0, got {total}"

    def test_empirical_distribution_only_even_gaps(self):
        """Test that only even gaps are included."""
        dist = get_empirical_gap_distribution(max_gap=50)

        # All gaps should be even
        assert all(g % 2 == 0 for g in dist.keys()), "All gaps must be even"

    def test_empirical_distribution_positive_probabilities(self):
        """Test that all probabilities are positive."""
        dist = get_empirical_gap_distribution(max_gap=200)

        assert all(p > 0 for p in dist.values()), "All probabilities must be positive"
