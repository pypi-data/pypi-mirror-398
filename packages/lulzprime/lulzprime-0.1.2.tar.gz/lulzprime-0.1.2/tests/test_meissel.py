"""
Tests for Meissel-Lehmer π(x) implementation with P2 correction.

Validates correctness of _pi_meissel() against segmented sieve backend.
Tests both exact correctness and asymptotic behavior.
"""

import random

from lulzprime.lehmer import _integer_cube_root, _pi_meissel
from lulzprime.pi import pi


class TestIntegerCubeRoot:
    """Tests for integer cube root helper."""

    def test_cube_root_small_values(self):
        """Test cube root for small perfect cubes and nearby values."""
        test_cases = [
            (0, 0),
            (1, 1),
            (7, 1),
            (8, 2),
            (9, 2),
            (26, 2),
            (27, 3),
            (28, 3),
            (63, 3),
            (64, 4),
            (125, 5),
            (216, 6),
            (1000, 10),
        ]

        for x, expected in test_cases:
            actual = _integer_cube_root(x)
            assert actual == expected, f"∛{x}: expected {expected}, got {actual}"
            # Verify it's correct: actual^3 <= x < (actual+1)^3
            assert actual**3 <= x
            assert (actual + 1) ** 3 > x

    def test_cube_root_large_values(self):
        """Test cube root for large values."""
        test_cases = [
            10_000,
            100_000,
            1_000_000,
            10_000_000,
        ]

        for x in test_cases:
            cbrt = _integer_cube_root(x)
            # Verify correctness
            assert cbrt**3 <= x
            assert (cbrt + 1) ** 3 > x

    def test_cube_root_deterministic(self):
        """Test that cube root is deterministic (no floating-point drift)."""
        x = 1_000_000
        result1 = _integer_cube_root(x)
        result2 = _integer_cube_root(x)
        result3 = _integer_cube_root(x)
        assert result1 == result2 == result3


class TestMeisselPi:
    """Tests for _pi_meissel() correctness and performance."""

    def test_meissel_exact_cross_check(self):
        """
        Exact cross-check: _pi_meissel(x) must equal pi(x) for key values.

        Tests specific values that cover edge cases and different algorithm paths.
        """
        test_values = [
            10,
            100,
            1_000,
            10_000,
            100_000,
            1_000_000,
        ]

        for x in test_values:
            expected = pi(x)
            actual = _pi_meissel(x)
            assert (
                actual == expected
            ), f"_pi_meissel({x}) = {actual}, expected {expected} (from pi())"

    def test_meissel_known_values(self):
        """
        Known π(x) values from mathematical references.

        Validates against established prime counting results.
        """
        known_values = [
            (10, 4),  # π(10) = 4: primes are 2, 3, 5, 7
            (100, 25),  # π(100) = 25
            (1_000, 168),  # π(1000) = 168
            (10_000, 1_229),  # π(10000) = 1229
            (100_000, 9_592),  # π(100000) = 9592
        ]

        for x, expected in known_values:
            actual = _pi_meissel(x)
            assert (
                actual == expected
            ), f"_pi_meissel({x}) = {actual}, expected {expected} (known value)"

    def test_meissel_edge_cases(self):
        """
        Edge cases: x < 2, x == 2, x == 3, small primes.

        Validates correct handling of boundary conditions.
        """
        edge_cases = [
            (0, 0),
            (1, 0),
            (2, 1),
            (3, 2),
            (4, 2),
            (5, 3),
            (7, 4),
            (11, 5),
        ]

        for x, expected in edge_cases:
            actual = _pi_meissel(x)
            assert actual == expected, f"_pi_meissel({x}) = {actual}, expected {expected}"

    def test_meissel_determinism(self):
        """
        Determinism: Repeated calls with same x must return same result.

        No randomization, no floating-point ambiguity.
        """
        test_values = [100, 1_000, 10_000, 100_000]

        for x in test_values:
            result1 = _pi_meissel(x)
            result2 = _pi_meissel(x)
            result3 = _pi_meissel(x)

            assert (
                result1 == result2 == result3
            ), f"Determinism violated for x={x}: got {result1}, {result2}, {result3}"

    def test_meissel_randomized_validation(self):
        """
        Randomized validation: 30 uniform values in [10k, 1M].

        Uses seeded random to ensure reproducibility.
        Cross-validates against pi() for each value.
        """
        random.seed(123)  # Deterministic seed
        sample_size = 30
        min_value = 10_000
        max_value = 1_000_000

        test_values = [random.randint(min_value, max_value) for _ in range(sample_size)]

        for x in test_values:
            expected = pi(x)
            actual = _pi_meissel(x)
            assert (
                actual == expected
            ), f"_pi_meissel({x}) = {actual}, expected {expected} (seed=123)"

    def test_meissel_monotonicity(self):
        """
        Monotonicity: π(x) is non-decreasing.

        For all x1 < x2, π(x1) <= π(x2).
        """
        test_values = [1, 10, 100, 1_000, 10_000, 50_000, 100_000, 500_000, 1_000_000]

        prev_x = test_values[0]
        prev_count = _pi_meissel(prev_x)

        for x in test_values[1:]:
            count = _pi_meissel(x)
            assert (
                count >= prev_count
            ), f"Monotonicity violated: π({prev_x}) = {prev_count}, π({x}) = {count}"
            prev_x = x
            prev_count = count

    def test_meissel_large_values(self):
        """
        Large values: Test _pi_meissel for x up to 10M.

        Validates correctness at scales where sublinear behavior matters.
        """
        large_values = [
            2_000_000,
            5_000_000,
            10_000_000,
        ]

        for x in large_values:
            expected = pi(x)
            actual = _pi_meissel(x)
            assert actual == expected, f"_pi_meissel({x}) = {actual}, expected {expected}"


class TestMeisselVsLegendre:
    """Compare Meissel variant with exact Legendre."""

    def test_meissel_equals_segmented_sieve(self):
        """
        Validation net: _pi_meissel(x) == pi(x) for comprehensive test set.

        Tests exact equality (no tolerances) against segmented sieve oracle.
        """
        test_values = [
            100_000,
            200_000,
            500_000,
            1_000_000,
            2_000_000,
            5_000_000,
            10_000_000,
        ]

        for x in test_values:
            expected = pi(x)
            actual = _pi_meissel(x)
            assert (
                actual == expected
            ), f"Mismatch at x={x}: _pi_meissel={actual}, pi={expected}, diff={actual-expected}"

    def test_randomized_comprehensive_validation(self):
        """
        Randomized comprehensive validation in [100k, 10M].

        Tests 20 random values with deterministic seed.
        Ensures correctness across the full supported range.
        """
        random.seed(456)  # Deterministic
        test_values = [random.randint(100_000, 10_000_000) for _ in range(20)]

        for x in test_values:
            expected = pi(x)
            actual = _pi_meissel(x)
            assert (
                actual == expected
            ), f"Mismatch at x={x}: _pi_meissel={actual}, pi={expected} (seed=456)"
