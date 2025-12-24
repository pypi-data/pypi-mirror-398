"""
Batch-friendly API layer for efficient multi-resolution operations.

Provides batch variants of core functions that optimize repeated calls
by sorting internally and caching π(x) computations within one batch.

See docs/api_contract.md for guarantee tiers and performance characteristics.

Canonical reference: https://roblemumin.com/library.html
"""

from collections.abc import Iterable

from .lookup import resolve_internal_with_pi
from .pi import pi as default_pi
from .resolve import between as _between
from .utils import validate_index


def resolve_many(indices: Iterable[int]) -> list[int]:
    """
    Return exact primes for multiple indices efficiently.

    Optimizes batch resolution by sorting indices internally to reduce
    repeated π(x) work, then returns results in original input order.

    GUARANTEES:
    - Tier A (Exact): Each result is exact p_index, same as resolve()
    - Deterministic: Same indices always yield same results in same order
    - Order preservation: Results match input order exactly
    - No global state: π(x) cache exists only during this call

    INPUT CONSTRAINTS:
    - Each index must be >= 1 (1-based indexing)
    - Each index must be an integer
    - Duplicates allowed (will compute each independently)
    - Practical limit per batch: ~100 indices (to stay within benchmark caps)
    - Each index subject to same limits as resolve() (≤ ~250k practical)

    PERFORMANCE ENVELOPE:
    - Small batches (< 10): seconds (similar to loop)
    - Medium batches (10-100): faster than loop (π(x) caching benefit)
    - Large batches (100+): may exceed benchmark time caps
    - Speedup depends on index locality (sorted indices share π(x) work)

    DOES NOT GUARANTEE:
    - Bounded runtime for arbitrary large batches
    - Parallelization (single-threaded execution)
    - Memory efficiency beyond O(batch_size) for results

    OPTIMIZATION STRATEGY:
    - Internally sorts indices to minimize π(x) recomputation
    - Caches π(x) results within this single batch execution
    - No persistent global cache (cache discarded after return)

    Args:
        indices: Iterable of prime indices (1-based)

    Returns:
        List of exact primes, in same order as input indices

    Raises:
        ValueError: If any index < 1
        TypeError: If any index is not an integer

    Examples:
        >>> resolve_many([1, 10, 100])
        [2, 29, 541]

        >>> resolve_many([100, 1, 10])  # Order preserved
        [541, 2, 29]

        >>> resolve_many([5, 5, 5])  # Duplicates allowed
        [11, 11, 11]
    """
    # Convert to list and validate
    indices_list = list(indices)

    # Validate all indices before processing
    for i, index in enumerate(indices_list):
        try:
            validate_index(index)
        except (ValueError, TypeError) as e:
            raise type(e)(f"Invalid index at position {i}: {e}") from None

    # Empty batch edge case
    if not indices_list:
        return []

    # Create (original_position, index) pairs to preserve order
    indexed_pairs = list(enumerate(indices_list))

    # Sort by index to optimize π(x) reuse
    sorted_pairs = sorted(indexed_pairs, key=lambda p: p[1])

    # Resolve in sorted order with π(x) caching
    results_with_pos = []
    pi_cache = {}  # Simple dict cache for π(x) within this batch

    # Create cached pi function (local closure, no global state)
    def cached_pi(x: int) -> int:
        """Local cached wrapper for π(x) within this batch."""
        if x not in pi_cache:
            pi_cache[x] = default_pi(x)
        return pi_cache[x]

    for original_pos, index in sorted_pairs:
        # Resolve using dependency injection (no global patching)
        result = resolve_internal_with_pi(index, cached_pi)
        results_with_pos.append((original_pos, result))

    # Restore original order
    results_with_pos.sort(key=lambda p: p[0])
    results = [result for _, result in results_with_pos]

    return results


def between_many(ranges: Iterable[tuple[int, int]]) -> list[list[int]]:
    """
    Return primes in multiple ranges efficiently.

    Calls between(x, y) for each range with input validation.

    GUARANTEES:
    - Tier B (Verified): All returned primes are verified
    - Deterministic: Same ranges always yield same results
    - Order preservation: Results match input range order
    - Completeness: All primes in each range returned

    INPUT CONSTRAINTS:
    - Each range must be (x, y) tuple with x <= y
    - y must be >= 2 for each range
    - Practical limit: ranges with < ~10,000 primes each
    - Batch size: reasonable number of ranges (< 100)

    PERFORMANCE ENVELOPE:
    - Small batches: linear in total primes returned
    - No cross-range optimization (each range independent)

    Args:
        ranges: Iterable of (x, y) tuples defining ranges [x, y]

    Returns:
        List of prime lists, one per input range, in input order

    Raises:
        ValueError: If any range invalid (x > y or y < 2)
        TypeError: If range not a tuple of two integers

    Examples:
        >>> between_many([(10, 20), (100, 110)])
        [[11, 13, 17, 19], [101, 103, 107, 109]]

        >>> between_many([(2, 5)])
        [[2, 3, 5]]
    """
    # Convert to list and validate
    ranges_list = list(ranges)

    # Validate all ranges before processing
    results = []
    for i, range_tuple in enumerate(ranges_list):
        # Validate tuple structure
        if not isinstance(range_tuple, tuple):
            raise TypeError(
                f"Range at position {i} must be a tuple, got {type(range_tuple).__name__}"
            )
        if len(range_tuple) != 2:
            raise ValueError(
                f"Range at position {i} must be a 2-tuple (x, y), got length {len(range_tuple)}"
            )

        x, y = range_tuple

        # Validate range via between's validation
        try:
            primes = _between(x, y)
            results.append(primes)
        except (ValueError, TypeError) as e:
            raise type(e)(f"Invalid range at position {i}: {e}") from None

    return results
