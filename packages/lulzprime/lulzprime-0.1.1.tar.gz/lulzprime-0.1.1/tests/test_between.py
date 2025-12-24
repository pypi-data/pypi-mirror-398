"""
Tests for between() range resolution function.

Verifies workflow from docs/manual/part_5.md section 5.4.
"""

import lulzprime


class TestBetween:
    """Test between() range resolution."""

    def test_between_small_range(self):
        """Test between() on small ranges."""
        result = lulzprime.between(2, 10)
        expected = [2, 3, 5, 7]
        assert result == expected

        result = lulzprime.between(10, 30)
        expected = [11, 13, 17, 19, 23, 29]
        assert result == expected

    def test_between_single_prime(self):
        """Test range containing single prime."""
        result = lulzprime.between(7, 7)
        assert result == [7]

        result = lulzprime.between(8, 10)
        assert result == []  # No primes in [8, 10]

    def test_between_no_primes(self):
        """Test range with no primes."""
        result = lulzprime.between(24, 28)
        assert result == []  # No primes between 24 and 28

    def test_between_large_range(self):
        """Test between() on larger range."""
        result = lulzprime.between(100, 150)

        # Verify all are prime
        for p in result:
            assert lulzprime.is_prime(p)

        # Verify strictly increasing
        for i in range(1, len(result)):
            assert result[i] > result[i - 1]

        # Verify completeness (no missing primes)
        # Check count matches difference in pi values
        from lulzprime.pi import pi

        expected_count = pi(150) - pi(99)
        assert len(result) == expected_count

    def test_between_ordering(self):
        """Test that results are in strictly increasing order."""
        result = lulzprime.between(2, 100)

        # Check ordering
        for i in range(1, len(result)):
            assert result[i] > result[i - 1], f"Not strictly increasing at index {i}"

        # Check no duplicates
        assert len(result) == len(set(result)), "Contains duplicates"

    def test_between_bounds_inclusive(self):
        """Test that bounds are inclusive."""
        # Lower bound inclusive
        result = lulzprime.between(11, 20)
        assert 11 in result

        # Upper bound inclusive
        result = lulzprime.between(10, 13)
        assert 13 in result
