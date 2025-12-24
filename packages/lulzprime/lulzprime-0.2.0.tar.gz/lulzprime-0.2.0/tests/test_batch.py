"""
Tests for batch API functions.

Validates determinism, order preservation, correctness, and input validation
for resolve_many() and between_many().

See docs/api_contract.md for guarantee specifications.
"""

import pytest

import lulzprime
from lulzprime.batch import between_many, resolve_many


class TestResolveManyCorrectness:
    """Test that resolve_many returns exact results matching resolve()."""

    def test_small_batch_correctness(self):
        """Verify resolve_many matches individual resolve calls."""
        indices = [1, 10, 100]
        expected = [lulzprime.resolve(i) for i in indices]
        result = resolve_many(indices)
        assert result == expected

    def test_medium_batch_correctness(self):
        """Verify correctness for medium batch (100 indices)."""
        indices = list(range(1, 101))  # First 100 primes
        expected = [lulzprime.resolve(i) for i in indices]
        result = resolve_many(indices)
        assert result == expected

    def test_unsorted_batch_correctness(self):
        """Verify correctness when indices are not sorted."""
        indices = [100, 1, 50, 25, 75]
        expected = [lulzprime.resolve(i) for i in indices]
        result = resolve_many(indices)
        assert result == expected


class TestResolveManyOrderPreservation:
    """Test that resolve_many preserves input order."""

    def test_order_preserved_sorted(self):
        """Results match input order for sorted indices."""
        indices = [1, 2, 3, 4, 5]
        result = resolve_many(indices)
        expected = [2, 3, 5, 7, 11]
        assert result == expected

    def test_order_preserved_reverse(self):
        """Results match input order for reverse-sorted indices."""
        indices = [5, 4, 3, 2, 1]
        result = resolve_many(indices)
        expected = [11, 7, 5, 3, 2]
        assert result == expected

    def test_order_preserved_random(self):
        """Results match input order for randomly ordered indices."""
        indices = [10, 1, 5, 3, 7]
        result = resolve_many(indices)
        # Verify order matches by comparing with individual calls
        expected = [lulzprime.resolve(i) for i in indices]
        assert result == expected


class TestResolveManyDeterminism:
    """Test that resolve_many is deterministic."""

    def test_determinism_same_batch(self):
        """Same indices always yield same results."""
        indices = [1, 10, 100, 50, 25]
        result1 = resolve_many(indices)
        result2 = resolve_many(indices)
        assert result1 == result2

    def test_determinism_different_order_same_indices(self):
        """Different ordering of same indices yields different result order."""
        indices1 = [1, 2, 3]
        indices2 = [3, 2, 1]

        result1 = resolve_many(indices1)
        result2 = resolve_many(indices2)

        # Results should match their respective input orders
        assert result1 == [2, 3, 5]
        assert result2 == [5, 3, 2]

        # Same set of values, different order
        assert set(result1) == set(result2)
        assert result1 != result2


class TestResolveManyDuplicates:
    """Test that resolve_many handles duplicate indices correctly."""

    def test_duplicates_allowed(self):
        """Duplicates in input produce duplicates in output."""
        indices = [5, 5, 5]
        result = resolve_many(indices)
        assert result == [11, 11, 11]

    def test_duplicates_order_preserved(self):
        """Duplicates maintain their positions."""
        indices = [1, 10, 1, 10, 1]
        result = resolve_many(indices)
        assert result == [2, 29, 2, 29, 2]


class TestResolveManyInputValidation:
    """Test input validation for resolve_many."""

    def test_negative_index_rejected(self):
        """Negative indices raise ValueError."""
        with pytest.raises(ValueError, match="Invalid index at position 1"):
            resolve_many([1, -5, 10])

    def test_zero_index_rejected(self):
        """Zero index raises ValueError."""
        with pytest.raises(ValueError, match="Invalid index at position 0"):
            resolve_many([0, 1, 2])

    def test_non_integer_rejected(self):
        """Non-integer indices raise TypeError."""
        with pytest.raises(TypeError, match="Invalid index at position 1"):
            resolve_many([1, "10", 100])

    def test_float_rejected(self):
        """Float indices raise TypeError."""
        with pytest.raises(TypeError, match="Invalid index at position 0"):
            resolve_many([1.5, 10])

    def test_empty_batch(self):
        """Empty batch returns empty list."""
        result = resolve_many([])
        assert result == []

    def test_single_element(self):
        """Single-element batch works correctly."""
        result = resolve_many([42])
        assert result == [lulzprime.resolve(42)]


class TestResolveManyPerformance:
    """Test batch performance characteristics (no timing, just scaling)."""

    def test_small_batch_completes(self):
        """Small batch (10 indices) completes successfully."""
        indices = list(range(1, 11))
        result = resolve_many(indices)
        assert len(result) == 10

    def test_medium_batch_completes(self):
        """Medium batch (100 indices) completes successfully."""
        indices = list(range(1, 101))
        result = resolve_many(indices)
        assert len(result) == 100

    def test_sparse_indices_completes(self):
        """Sparse indices (non-sequential) complete successfully."""
        indices = [1, 100, 200, 300, 400, 500]
        result = resolve_many(indices)
        assert len(result) == 6
        # Verify each result is correct
        for i, index in enumerate(indices):
            assert result[i] == lulzprime.resolve(index)


class TestBetweenManyCorrectness:
    """Test that between_many returns correct results."""

    def test_small_batch_correctness(self):
        """Verify between_many matches individual between calls."""
        ranges = [(10, 20), (100, 110)]
        expected = [lulzprime.between(x, y) for x, y in ranges]
        result = between_many(ranges)
        assert result == expected

    def test_single_range(self):
        """Single range works correctly."""
        ranges = [(2, 10)]
        result = between_many(ranges)
        assert result == [[2, 3, 5, 7]]

    def test_multiple_ranges(self):
        """Multiple ranges return correct results in order."""
        ranges = [(2, 5), (10, 15), (20, 25)]
        result = between_many(ranges)
        expected = [[2, 3, 5], [11, 13], [23]]
        assert result == expected


class TestBetweenManyOrderPreservation:
    """Test that between_many preserves input order."""

    def test_order_preserved(self):
        """Results match input range order."""
        ranges = [(100, 110), (10, 20), (2, 10)]
        result = between_many(ranges)
        expected = [
            lulzprime.between(100, 110),
            lulzprime.between(10, 20),
            lulzprime.between(2, 10),
        ]
        assert result == expected


class TestBetweenManyDeterminism:
    """Test that between_many is deterministic."""

    def test_determinism(self):
        """Same ranges always yield same results."""
        ranges = [(10, 20), (100, 110)]
        result1 = between_many(ranges)
        result2 = between_many(ranges)
        assert result1 == result2


class TestBetweenManyInputValidation:
    """Test input validation for between_many."""

    def test_invalid_range_x_greater_than_y(self):
        """Range with x > y raises ValueError."""
        with pytest.raises(ValueError, match="Invalid range at position 0"):
            between_many([(20, 10)])

    def test_invalid_range_y_less_than_2(self):
        """Range with y < 2 raises ValueError."""
        with pytest.raises(ValueError, match="Invalid range at position 0"):
            between_many([(0, 1)])

    def test_non_tuple_rejected(self):
        """Non-tuple range raises TypeError."""
        with pytest.raises(TypeError, match="Range at position 0 must be a tuple"):
            between_many([[10, 20]])

    def test_wrong_length_tuple_rejected(self):
        """Tuple with wrong length raises ValueError."""
        with pytest.raises(ValueError, match="Range at position 0 must be a 2-tuple"):
            between_many([(10, 20, 30)])

    def test_empty_batch(self):
        """Empty batch returns empty list."""
        result = between_many([])
        assert result == []

    def test_multiple_ranges_one_invalid(self):
        """Invalid range in batch raises error with position."""
        with pytest.raises(ValueError, match="Invalid range at position 1"):
            between_many([(2, 10), (20, 10), (100, 110)])


class TestBetweenManyEdgeCases:
    """Test edge cases for between_many."""

    def test_overlapping_ranges(self):
        """Overlapping ranges are handled independently."""
        ranges = [(10, 20), (15, 25)]
        result = between_many(ranges)
        expected = [[11, 13, 17, 19], [17, 19, 23]]
        assert result == expected

    def test_empty_range_results(self):
        """Range with no primes returns empty list."""
        ranges = [(24, 28)]  # No primes in this range
        result = between_many(ranges)
        assert result == [[]]

    def test_single_prime_ranges(self):
        """Ranges with single prime work correctly."""
        ranges = [(23, 23), (29, 29)]
        result = between_many(ranges)
        assert result == [[23], [29]]


class TestResolveManyNoGlobalMutation:
    """Test that resolve_many does not mutate global state."""

    def test_no_global_pi_mutation(self):
        """Verify resolve_many does not mutate the global pi() function."""
        from lulzprime import pi as pi_module

        # Get identity of original pi function
        original_pi = pi_module.pi
        original_id = id(original_pi)

        # Call resolve_many
        indices = [1, 10, 100, 50, 25]
        result = resolve_many(indices)

        # Verify pi() is unchanged
        assert pi_module.pi is original_pi, "Global pi() function was mutated"
        assert id(pi_module.pi) == original_id, "Global pi() identity changed"

        # Verify results are correct despite no mutation
        expected = [lulzprime.resolve(i) for i in indices]
        assert result == expected

    def test_consecutive_calls_no_state(self):
        """Verify consecutive resolve_many calls don't interfere."""
        from lulzprime import pi as pi_module

        # Get original pi
        original_pi = pi_module.pi

        # First call
        indices1 = [1, 2, 3, 4, 5]
        result1 = resolve_many(indices1)

        # Verify pi unchanged after first call
        assert pi_module.pi is original_pi, "pi() changed after first call"

        # Second call with different indices
        indices2 = [10, 20, 30]
        result2 = resolve_many(indices2)

        # Verify pi unchanged after second call
        assert pi_module.pi is original_pi, "pi() changed after second call"

        # Verify both results are correct
        expected1 = [2, 3, 5, 7, 11]
        expected2 = [29, 71, 113]
        assert result1 == expected1
        assert result2 == expected2

    def test_sentinel_wrapper_not_leaked(self):
        """Verify no internal cached wrappers leak to global scope."""
        from lulzprime import pi as pi_module

        # Get original pi
        original_pi = pi_module.pi
        original_name = original_pi.__name__

        # Call resolve_many
        resolve_many([1, 10, 100])

        # Verify pi is still the original function, not a wrapper
        assert pi_module.pi is original_pi
        assert pi_module.pi.__name__ == original_name
        assert "cached" not in pi_module.pi.__name__.lower()
