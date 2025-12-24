"""
Comprehensive validation tests for φ(x, a) function using brute-force oracle.

These tests are designed to catch caching bugs, indexing errors, and edge cases
that commonly break recursive implementations.
"""

import random

from lulzprime.lehmer import _simple_sieve, phi, phi_bruteforce, pi_small


class TestPhiValidation:
    """Validation tests for φ(x, a) against brute-force oracle."""

    def test_phi_vs_bruteforce_small_values(self):
        """Test φ against oracle for small (x, a) combinations."""
        primes = _simple_sieve(100)
        test_cases = [
            (10, 0),  # a=0: should return x
            (10, 1),  # First prime: 2
            (10, 2),  # First 2 primes: 2, 3
            (20, 2),  # Larger x
            (20, 3),  # First 3 primes: 2, 3, 5
            (30, 3),
            (50, 4),  # First 4 primes: 2, 3, 5, 7
            (100, 5),  # First 5 primes
        ]

        for x, a in test_cases:
            expected = phi_bruteforce(x, a, primes)
            actual = phi(x, a, primes, {})
            assert actual == expected, f"φ({x}, {a}): expected {expected}, got {actual}"

    def test_phi_vs_bruteforce_reported_failure(self):
        """
        Test the specific case that was reported failing: φ(10000, 25).

        This test documents the bug and will pass once φ is fixed.
        """
        primes = _simple_sieve(100)  # Need at least 25 primes
        x, a = 10_000, 25

        expected = phi_bruteforce(x, a, primes)
        actual = phi(x, a, primes, {})

        assert (
            actual == expected
        ), f"φ({x}, {a}): expected {expected}, got {actual} (difference: {actual - expected})"

    def test_phi_edge_case_a_equals_zero(self):
        """φ(x, 0) should return x for any x >= 0."""
        primes = _simple_sieve(10)
        test_values = [0, 1, 2, 10, 100, 1000]

        for x in test_values:
            expected = x
            actual = phi(x, 0, primes, {})
            assert actual == expected, f"φ({x}, 0) should be {x}, got {actual}"

    def test_phi_edge_case_x_equals_zero(self):
        """φ(0, a) should return 0 for any a >= 0."""
        primes = _simple_sieve(20)
        test_a_values = [0, 1, 2, 5]

        for a in test_a_values:
            expected = 0
            actual = phi(0, a, primes, {})
            assert actual == expected, f"φ(0, {a}) should be 0, got {actual}"

    def test_phi_edge_case_x_equals_one(self):
        """
        φ(1, a) should return 1 for any a >= 0.

        The number 1 is not divisible by any prime, so it's always counted.
        """
        primes = _simple_sieve(20)
        test_a_values = [0, 1, 2, 5, 8]

        for a in test_a_values:
            expected = 1
            actual = phi(1, a, primes, {})
            assert actual == expected, f"φ(1, {a}) should be 1, got {actual}"

    def test_phi_edge_case_x_equals_two(self):
        """
        φ(2, a) tests boundary with first prime.

        - φ(2, 0) = 2 (no exclusions)
        - φ(2, 1) = 1 (exclude 2, only 1 remains)
        - φ(2, a) = 1 for a >= 1 (2 is excluded, only 1 remains)
        """
        primes = _simple_sieve(20)

        assert phi(2, 0, primes, {}) == 2
        assert phi(2, 1, primes, {}) == 1
        assert phi(2, 2, primes, {}) == 1
        assert phi(2, 5, primes, {}) == 1

    def test_phi_edge_case_p_a_greater_than_x(self):
        """
        When p_a > x, all first a primes are > x, so φ(x, a) should behave like φ(x, smaller_a).

        Specifically, if all primes in [p_1, ..., p_a] are > x, then none affect the count,
        so φ(x, a) should count all integers in [1, x] not divisible by any prime <= x.

        For small x with large a, this should give consistent results.
        """
        primes = _simple_sieve(100)

        # x=5, a=3: first 3 primes are [2,3,5]
        # p_3 = 5, so we're excluding {2,3,5}
        # Numbers in [1,5] not divisible by {2,3,5}: just {1}
        expected_5_3 = phi_bruteforce(5, 3, primes)
        actual_5_3 = phi(5, 3, primes, {})
        assert actual_5_3 == expected_5_3

        # x=3, a=3: first 3 primes are [2,3,5]
        # But p_3=5 > 3, so only {2,3} actually divide anything in [1,3]
        # Numbers in [1,3] not divisible by {2,3}: just {1}
        expected_3_3 = phi_bruteforce(3, 3, primes)
        actual_3_3 = phi(3, 3, primes, {})
        assert actual_3_3 == expected_3_3

        # x=2, a=5: first 5 primes are [2,3,5,7,11]
        # Only 2 divides anything in [1,2]
        # Numbers in [1,2] not divisible by {2,3,5,7,11}: just {1}
        expected_2_5 = phi_bruteforce(2, 5, primes)
        actual_2_5 = phi(2, 5, primes, {})
        assert actual_2_5 == expected_2_5

    def test_phi_below_and_above_prime_squares(self):
        """
        Test φ around prime squares to catch off-by-one errors.

        - p_1 = 2, p_1^2 = 4
        - p_2 = 3, p_2^2 = 9
        - p_3 = 5, p_3^2 = 25
        """
        primes = _simple_sieve(30)

        test_cases = [
            (3, 1),  # Just below 2^2
            (4, 1),  # At 2^2
            (5, 1),  # Just above 2^2
            (8, 2),  # Just below 3^2
            (9, 2),  # At 3^2
            (10, 2),  # Just above 3^2
            (24, 3),  # Just below 5^2
            (25, 3),  # At 5^2
            (26, 3),  # Just above 5^2
        ]

        for x, a in test_cases:
            expected = phi_bruteforce(x, a, primes)
            actual = phi(x, a, primes, {})
            assert actual == expected, f"φ({x}, {a}): expected {expected}, got {actual}"

    def test_phi_medium_values(self):
        """Test φ for medium-sized values to stress memoization."""
        primes = _simple_sieve(200)

        test_cases = [
            (100, 10),
            (200, 15),
            (500, 20),
            (1000, 25),
            (5000, 30),  # This should be fast enough with memoization
        ]

        for x, a in test_cases:
            expected = phi_bruteforce(x, a, primes)
            actual = phi(x, a, primes, {})
            assert actual == expected, f"φ({x}, {a}): expected {expected}, got {actual}"

    def test_phi_memoization_consistency(self):
        """
        Test that φ gives consistent results with same memo vs separate memos.

        This catches bugs where memo state leaks between calls.
        """
        primes = _simple_sieve(100)
        x, a = 100, 10

        # Call 1: Fresh memo
        memo1 = {}
        result1 = phi(x, a, primes, memo1)

        # Call 2: Fresh memo (should get same result)
        memo2 = {}
        result2 = phi(x, a, primes, memo2)

        # Call 3: Reuse memo1 (should still get same result)
        result3 = phi(x, a, primes, memo1)

        assert (
            result1 == result2 == result3
        ), f"Inconsistent results: {result1}, {result2}, {result3}"

        # Verify against oracle
        expected = phi_bruteforce(x, a, primes)
        assert result1 == expected

    def test_phi_various_a_same_x(self):
        """
        Test φ(x, a) for same x with varying a.

        φ(x, a) should be monotonically non-increasing as a increases
        (more primes excluded means fewer numbers remain).
        """
        primes = _simple_sieve(50)
        x = 100

        prev_result = x  # φ(100, 0) = 100
        for a in range(1, 10):
            result = phi(x, a, primes, {})
            expected = phi_bruteforce(x, a, primes)

            assert result == expected, f"φ({x}, {a}): expected {expected}, got {result}"
            assert (
                result <= prev_result
            ), f"φ({x}, {a}) = {result} should be <= φ({x}, {a-1}) = {prev_result}"

            prev_result = result

    def test_phi_stress_with_large_a_small_x(self):
        """
        Stress test: large a with small x.

        When a is large relative to x, many primes won't affect the count.
        """
        primes = _simple_sieve(200)

        test_cases = [
            (10, 10),
            (20, 15),
            (50, 20),
            (100, 25),
        ]

        for x, a in test_cases:
            expected = phi_bruteforce(x, a, primes)
            actual = phi(x, a, primes, {})
            assert actual == expected, f"φ({x}, {a}): expected {expected}, got {actual}"

    def test_phi_randomized_comprehensive(self):
        """
        Randomized comprehensive test for φ(x, a) with x ≤ 20,000 and a ≤ π(√x).

        Tests 50 random (x, a) pairs with deterministic seed for reproducibility.
        This validates φ correctness across a wide range of realistic inputs.
        """
        random.seed(42)  # Deterministic for reproducibility

        # Generate test cases
        test_cases = []
        for _ in range(50):
            x = random.randint(100, 20_000)
            sqrt_x = int(x**0.5)
            max_a = pi_small(sqrt_x)  # a ≤ π(√x) is realistic for Meissel
            a = random.randint(1, max_a) if max_a > 0 else 0
            test_cases.append((x, a))

        # Generate primes once (enough for all test cases)
        max_x = max(x for x, _ in test_cases)
        sqrt_max = int(max_x**0.5) + 1
        primes = _simple_sieve(sqrt_max)

        # Validate each test case
        for x, a in test_cases:
            expected = phi_bruteforce(x, a, primes)
            actual = phi(x, a, primes, {})
            assert actual == expected, f"φ({x}, {a}): expected {expected}, got {actual} (seed=42)"

    def test_phi_monotonicity_in_x(self):
        """
        Monotonicity test: φ(x, a) is non-decreasing in x for fixed a.

        For fixed a, as x increases, φ(x, a) should increase or stay the same.
        """
        primes = _simple_sieve(100)
        a = 5  # First 5 primes

        x_values = [10, 20, 50, 100, 200, 500, 1000]

        prev_phi = 0
        for x in x_values:
            phi_val = phi(x, a, primes, {})
            assert phi_val >= prev_phi, (
                f"Monotonicity violated: φ({x_values[x_values.index(x)-1]}, {a}) = {prev_phi}, "
                f"φ({x}, {a}) = {phi_val}"
            )
            prev_phi = phi_val

    def test_phi_monotonicity_in_a(self):
        """
        Monotonicity test: φ(x, a) is non-increasing in a for fixed x.

        For fixed x, as a increases (more primes excluded), φ(x, a) should decrease or stay the same.
        """
        primes = _simple_sieve(50)
        x = 1000

        prev_phi = x  # φ(x, 0) = x
        for a in range(1, 15):
            phi_val = phi(x, a, primes, {})
            assert (
                phi_val <= prev_phi
            ), f"Monotonicity violated: φ({x}, {a-1}) = {prev_phi}, φ({x}, {a}) = {phi_val}"
            prev_phi = phi_val

    def test_phi_recursion_invariant(self):
        """
        Recursion invariant test: φ(x, a) = φ(x, a-1) - φ(⌊x/p_a⌋, a-1).

        This is the fundamental recursive formula that φ must satisfy.
        Validates that the implementation correctly applies the recurrence.
        """
        primes = _simple_sieve(100)

        test_cases = [
            (100, 4),
            (500, 6),
            (1000, 8),
            (5000, 10),
        ]

        for x, a in test_cases:
            # Direct computation via phi()
            phi_xa = phi(x, a, primes, {})

            # Manual computation via recursion formula
            p_a = primes[a - 1]
            phi_xa_minus_1 = phi(x, a - 1, primes, {})
            phi_x_div_pa = phi(x // p_a, a - 1, primes, {})
            expected = phi_xa_minus_1 - phi_x_div_pa

            assert phi_xa == expected, (
                f"Recursion invariant violated for φ({x}, {a}): "
                f"got {phi_xa}, expected {expected} from formula"
            )
