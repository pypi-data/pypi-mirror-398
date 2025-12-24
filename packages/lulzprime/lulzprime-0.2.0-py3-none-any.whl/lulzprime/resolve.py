"""
User-facing prime resolution functions.

Provides the public API for prime resolution and navigation.
See docs/manual/part_4.md for API contracts and part_5.md for workflows.

Canonical reference: https://roblemumin.com/library.html
"""

from .lookup import resolve_internal
from .primality import next_prime as _next_prime
from .primality import prev_prime as _prev_prime
from .utils import validate_index, validate_range


def resolve(index: int) -> int:
    """
    Return the exact nth prime p_index.

    Uses forecast + π(x) refinement + primality-confirmed correction.

    GUARANTEES:
    - Tier A (Exact by construction): Always returns the exact p_index
    - Deterministic: Same index always yields same result
    - No hidden network access or precomputation

    INPUT CONSTRAINTS:
    - index must be >= 1 (1-based indexing: index=1 returns p_1 = 2)
    - index must be an integer
    - Practical limit: indices ≤ ~250,000 complete within minutes
    - Indices > 500,000 may exceed reasonable runtime (30+ minutes)

    PERFORMANCE ENVELOPE:
    - Small indices (< 1,000): milliseconds
    - Medium indices (1,000 - 100,000): seconds
    - Large indices (100,000 - 250,000): minutes
    - Stress indices (500,000+): impractical with current implementation
    - See docs/benchmark_policy.md for measured performance data

    DOES NOT GUARANTEE:
    - Bounded runtime for arbitrary large indices
    - Cryptographic properties (not suitable for security applications)
    - Sublinear time complexity (current: O(x log log x) where x ≈ p_index)

    Args:
        index: Prime index (1-based, so index=1 returns p_1 = 2)

    Returns:
        The exact value of p_index

    Raises:
        ValueError: If index < 1
        TypeError: If index is not an integer

    Examples:
        >>> resolve(1)
        2
        >>> resolve(10)
        29
        >>> resolve(100)
        541
    """
    validate_index(index)
    return resolve_internal(index)


def between(x: int, y: int) -> list[int]:
    """
    Return all primes in the range [x, y].

    Uses localized primality testing, not full sieving.

    GUARANTEES:
    - Tier B (Verified): All returned values are confirmed primes
    - Deterministic: Same range always yields same list
    - Complete: All primes in [x, y] are returned, none are skipped

    INPUT CONSTRAINTS:
    - x <= y (range must be valid)
    - y >= 2 (no primes below 2)
    - x, y must be integers
    - Practical limit: ranges with < ~10,000 primes complete quickly
    - Large dense ranges may take longer (depends on prime density)

    PERFORMANCE ENVELOPE:
    - Small ranges (< 100 candidates): milliseconds
    - Medium ranges (100 - 10,000 candidates): seconds
    - Large ranges: linear in number of candidates tested
    - Dense prime regions (small numbers) faster than sparse regions

    DOES NOT GUARANTEE:
    - Sublinear complexity in range size
    - Bounded runtime for arbitrarily large ranges
    - Cryptographic randomness of prime distribution

    Args:
        x: Lower bound (inclusive)
        y: Upper bound (inclusive)

    Returns:
        List of all primes p with x <= p <= y, in ascending order

    Raises:
        ValueError: If x > y or y < 2
        TypeError: If x or y are not integers

    Examples:
        >>> between(10, 20)
        [11, 13, 17, 19]
        >>> between(2, 10)
        [2, 3, 5, 7]
    """
    x_norm, y_norm = validate_range(x, y)

    primes = []
    p = _next_prime(x_norm)

    while p <= y_norm:
        primes.append(p)
        p = _next_prime(p + 1)

    return primes


def next_prime(n: int) -> int:
    """
    Return the smallest prime >= n.

    GUARANTEES:
    - Tier B (Verified): Returned value is confirmed prime
    - Deterministic: Same n always yields same result
    - Minimal: Returns the smallest prime >= n, not a larger one

    INPUT CONSTRAINTS:
    - n must be an integer
    - No upper bound enforced, but performance degrades for large n
    - Practical limit: n < 10^15 completes quickly (deterministic primality test)

    PERFORMANCE ENVELOPE:
    - Small n (< 1,000): microseconds
    - Medium n (1,000 - 1,000,000): milliseconds
    - Large n: depends on gap to next prime (average gap ~log n)
    - Worst case: linear search through non-prime candidates

    DOES NOT GUARANTEE:
    - Bounded runtime (depends on prime gap)
    - Cryptographic properties

    Args:
        n: Starting point for search

    Returns:
        First prime p with p >= n

    Examples:
        >>> next_prime(10)
        11
        >>> next_prime(11)
        11
    """
    return _next_prime(n)


def prev_prime(n: int) -> int:
    """
    Return the largest prime <= n.

    GUARANTEES:
    - Tier B (Verified): Returned value is confirmed prime
    - Deterministic: Same n always yields same result
    - Maximal: Returns the largest prime <= n, not a smaller one

    INPUT CONSTRAINTS:
    - n must be >= 2 (no primes exist below 2)
    - n must be an integer
    - Practical limit: n < 10^15 completes quickly (deterministic primality test)

    PERFORMANCE ENVELOPE:
    - Small n (< 1,000): microseconds
    - Medium n (1,000 - 1,000,000): milliseconds
    - Large n: depends on gap to previous prime (average gap ~log n)
    - Worst case: linear search through non-prime candidates

    DOES NOT GUARANTEE:
    - Bounded runtime (depends on prime gap)
    - Cryptographic properties

    Args:
        n: Starting point for search

    Returns:
        Largest prime p with p <= n

    Raises:
        ValueError: If n < 2 (no primes below 2)

    Examples:
        >>> prev_prime(10)
        7
        >>> prev_prime(11)
        11
    """
    return _prev_prime(n)
