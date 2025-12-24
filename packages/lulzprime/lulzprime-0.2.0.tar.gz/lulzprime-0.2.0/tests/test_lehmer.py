"""
Tests for Lehmer-style sublinear π(x) implementation.

Validates correctness of lehmer_pi() against proven segmented sieve backend.
All tests must complete within a few seconds per benchmark policy.

See docs/adr/0005-lehmer-pi.md for algorithm details.
"""

import random

from lulzprime.lehmer import _simple_sieve, lehmer_pi, phi, pi_small
from lulzprime.pi import pi


class TestLehmerPi:
    """Tests for lehmer_pi() correctness and determinism."""

    def test_lehmer_exact_cross_check(self):
        """
        Exact cross-check: lehmer_pi(x) must equal pi(x) for key values.

        Tests specific values that cover edge cases and different algorithm paths.
        """
        test_values = [
            10,
            100,
            1_000,
            10_000,
            100_000,
            1_000_000,
            2_000_000,
        ]

        for x in test_values:
            expected = pi(x)
            actual = lehmer_pi(x)
            assert actual == expected, f"lehmer_pi({x}) = {actual}, expected {expected} (from pi())"

    def test_lehmer_random_sample(self):
        """
        Random sample validation: 25 uniform values in [1, 200_000].

        Uses seeded random to ensure reproducibility.
        Cross-validates against pi() for each value.
        """
        random.seed(42)  # Deterministic seed for reproducibility
        sample_size = 25
        max_value = 200_000

        test_values = [random.randint(1, max_value) for _ in range(sample_size)]

        for x in test_values:
            expected = pi(x)
            actual = lehmer_pi(x)
            assert actual == expected, f"lehmer_pi({x}) = {actual}, expected {expected} (seed=42)"

    def test_lehmer_edge_cases(self):
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
            actual = lehmer_pi(x)
            assert actual == expected, f"lehmer_pi({x}) = {actual}, expected {expected}"

    def test_lehmer_monotonicity(self):
        """
        Monotonicity: π(x) is non-decreasing.

        For all x1 < x2, π(x1) <= π(x2).
        """
        test_values = [1, 10, 100, 1_000, 10_000, 50_000, 100_000]

        prev_x = test_values[0]
        prev_count = lehmer_pi(prev_x)

        for x in test_values[1:]:
            count = lehmer_pi(x)
            assert (
                count >= prev_count
            ), f"Monotonicity violated: π({prev_x}) = {prev_count}, π({x}) = {count}"
            prev_x = x
            prev_count = count

    def test_lehmer_determinism(self):
        """
        Determinism: Repeated calls with same x must return same result.

        No randomization, no floating-point ambiguity.
        """
        test_values = [100, 1_000, 10_000, 100_000]

        for x in test_values:
            result1 = lehmer_pi(x)
            result2 = lehmer_pi(x)
            result3 = lehmer_pi(x)

            assert (
                result1 == result2 == result3
            ), f"Determinism violated for x={x}: got {result1}, {result2}, {result3}"

    def test_lehmer_known_values(self):
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
            actual = lehmer_pi(x)
            assert (
                actual == expected
            ), f"lehmer_pi({x}) = {actual}, expected {expected} (known value)"


class TestPiSmall:
    """Tests for pi_small() helper function."""

    def test_pi_small_correctness(self):
        """
        pi_small() should match pi() for small values.

        This is the helper used internally by lehmer_pi for π(x^(1/4)), etc.
        """
        test_values = [10, 100, 1_000, 10_000, 100_000]

        for x in test_values:
            expected = pi(x)
            actual = pi_small(x)
            assert actual == expected, f"pi_small({x}) = {actual}, expected {expected}"

    def test_pi_small_edge_cases(self):
        """Edge cases for pi_small()."""
        assert pi_small(0) == 0
        assert pi_small(1) == 0
        assert pi_small(2) == 1
        assert pi_small(3) == 2


class TestPhiFunction:
    """Tests for φ(x, a) function."""

    def test_phi_base_cases(self):
        """
        Base cases for φ(x, a).

        - φ(x, 0) = x (no primes to exclude)
        - φ(0, a) = 0 (no integers in [1, 0])
        - φ(1, a) = 1 for any a >= 0 (1 is not divisible by any prime)
        """
        primes = _simple_sieve(100)

        # φ(x, 0) = x
        assert phi(10, 0, primes) == 10
        assert phi(100, 0, primes) == 100

        # φ(0, a) = 0 for any a
        assert phi(0, 5, primes) == 0

        # φ(1, a) = 1 for any a (1 is coprime to all primes)
        assert phi(1, 5, primes) == 1
        assert phi(1, 1, primes) == 1

    def test_phi_known_values(self):
        """
        Known φ(x, a) values.

        - φ(10, 1) = 5: integers <= 10 not divisible by 2 are {1,3,5,7,9}
        - φ(10, 2) = 3: integers <= 10 not divisible by {2,3} are {1,5,7}
        """
        primes = _simple_sieve(100)

        # φ(10, 1): exclude multiples of 2
        # Remaining: 1, 3, 5, 7, 9 → count = 5
        assert phi(10, 1, primes) == 5

        # φ(10, 2): exclude multiples of 2 and 3
        # Remaining: 1, 5, 7 → count = 3
        assert phi(10, 2, primes) == 3

        # φ(100, 3): exclude multiples of 2, 3, 5
        # This is trickier to compute by hand, but we can verify consistency
        result = phi(100, 3, primes)
        assert result > 0  # Sanity check
        assert result < 100  # Must be less than x

    def test_phi_recursive_consistency(self):
        """
        Recursive formula consistency.

        φ(x, a) = φ(x, a-1) - φ(⌊x/p_a⌋, a-1)

        Verify this holds for a few cases.
        """
        primes = _simple_sieve(100)
        x = 100
        a = 4  # First 4 primes: 2, 3, 5, 7

        # Compute via function
        phi_xa = phi(x, a, primes)

        # Compute via recursive formula manually
        phi_xa_minus_1 = phi(x, a - 1, primes)
        p_a = primes[a - 1]  # 4th prime (0-indexed) = primes[3] = 7
        phi_x_div_pa = phi(x // p_a, a - 1, primes)

        expected = phi_xa_minus_1 - phi_x_div_pa

        assert (
            phi_xa == expected
        ), f"φ({x}, {a}) recursive formula failed: got {phi_xa}, expected {expected}"


class TestSimpleSieve:
    """Tests for _simple_sieve() helper."""

    def test_simple_sieve_small_values(self):
        """Validate _simple_sieve for small limits."""
        assert _simple_sieve(0) == []
        assert _simple_sieve(1) == []
        assert _simple_sieve(2) == [2]
        assert _simple_sieve(10) == [2, 3, 5, 7]
        assert _simple_sieve(20) == [2, 3, 5, 7, 11, 13, 17, 19]

    def test_simple_sieve_count_matches_pi(self):
        """Count from _simple_sieve should match pi()."""
        test_values = [10, 100, 1_000]

        for limit in test_values:
            primes = _simple_sieve(limit)
            expected_count = pi(limit)
            assert (
                len(primes) == expected_count
            ), f"len(_simple_sieve({limit})) = {len(primes)}, expected {expected_count}"
