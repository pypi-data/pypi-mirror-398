"""
Tests for primality testing functions.

Verifies implementation from docs/manual/part_5.md section 5.6.
"""

import pytest

import lulzprime


class TestIsPrime:
    """Test is_prime() function."""

    def test_is_prime_small_primes(self):
        """Test is_prime() on small known primes."""
        primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]
        for p in primes:
            assert lulzprime.is_prime(p), f"{p} should be prime"

    def test_is_prime_small_composites(self):
        """Test is_prime() on small composites."""
        composites = [4, 6, 8, 9, 10, 12, 14, 15, 16, 18, 20, 21, 22, 24, 25]
        for n in composites:
            assert not lulzprime.is_prime(n), f"{n} should not be prime"

    def test_is_prime_edge_cases(self):
        """Test edge cases for is_prime()."""
        assert not lulzprime.is_prime(0)
        assert not lulzprime.is_prime(1)
        assert lulzprime.is_prime(2)

    def test_is_prime_large_primes(self):
        """Test is_prime() on larger known primes."""
        large_primes = [97, 541, 7919, 15485863, 32452843, 49979687, 67867967, 86028121]
        for p in large_primes:
            assert lulzprime.is_prime(p), f"{p} should be prime"

    def test_is_prime_large_composites(self):
        """Test is_prime() on larger composites."""
        composites = [100, 1000, 10000, 15485864, 32452844]
        for n in composites:
            assert not lulzprime.is_prime(n), f"{n} should not be prime"


class TestNextPrime:
    """Test next_prime() function."""

    def test_next_prime_basic(self):
        """Test next_prime() basic cases."""
        assert lulzprime.next_prime(1) == 2
        assert lulzprime.next_prime(2) == 2
        assert lulzprime.next_prime(3) == 3
        assert lulzprime.next_prime(4) == 5
        assert lulzprime.next_prime(10) == 11
        assert lulzprime.next_prime(14) == 17

    def test_next_prime_on_prime(self):
        """Test next_prime() when n is already prime."""
        primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
        for p in primes:
            assert lulzprime.next_prime(p) == p


class TestPrevPrime:
    """Test prev_prime() function."""

    def test_prev_prime_basic(self):
        """Test prev_prime() basic cases."""
        assert lulzprime.prev_prime(2) == 2
        assert lulzprime.prev_prime(3) == 3
        assert lulzprime.prev_prime(4) == 3
        assert lulzprime.prev_prime(10) == 7
        assert lulzprime.prev_prime(20) == 19

    def test_prev_prime_on_prime(self):
        """Test prev_prime() when n is already prime."""
        primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
        for p in primes:
            assert lulzprime.prev_prime(p) == p

    def test_prev_prime_invalid_input(self):
        """Test prev_prime() with invalid input."""
        with pytest.raises(ValueError):
            lulzprime.prev_prime(1)

        with pytest.raises(ValueError):
            lulzprime.prev_prime(0)
