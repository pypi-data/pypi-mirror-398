"""
Analytic forecasting for prime locations.

Provides refined Prime Number Theorem approximations to estimate p_n.
See docs/manual/part_5.md section 5.2 for workflow specification.

Canonical reference: https://roblemumin.com/library.html
Output class: Tier C (Estimate only)
"""

from .config import FORECAST_SMALL_THRESHOLD, SMALL_PRIMES
from .utils import log_log_n, log_n, validate_index


def forecast(index: int) -> int:
    """
    Return an analytic estimate for the nth prime p_index.

    This provides a cheap O(1) jump point for navigation. NOT EXACT.

    GUARANTEES:
    - Tier C (Estimate): Returns approximate value, NOT exact prime
    - Deterministic: Same index always yields same estimate
    - Fast: O(1) computation, no iteration or sieving

    INPUT CONSTRAINTS:
    - index must be >= 1 (1-based indexing)
    - index must be an integer
    - No practical upper bound (formula works for arbitrarily large indices)

    PERFORMANCE ENVELOPE:
    - All indices: O(1) time, microseconds
    - Uses refined PNT approximation: n * (log n + log log n - 1)
    - Small indices (< 50): exact via hardcoded table
    - Large indices: approximate within ~1% typically

    DOES NOT GUARANTEE:
    - Exactness: forecast(index) may NOT equal resolve(index)
    - Primality: returned value may not be prime
    - Bounded error: relative error varies with index
    - Use resolve(index) for exact primes, not forecast(index)

    WARNING:
    This is an ESTIMATE for navigation, not a truth source.
    Do not use forecast() results as if they were exact primes.

    Args:
        index: Prime index (1-based, so index=1 gives p_1 = 2)

    Returns:
        Estimated value of p_index (integer, may not be exact or prime)

    Raises:
        ValueError: If index < 1
        TypeError: If index is not an integer

    Examples:
        >>> forecast(1)  # Estimate for p_1
        2
        >>> forecast(10)  # Estimate for p_10 (actual = 29)
        28  # Approximate, not exact
    """
    validate_index(index)

    # For small indices, use hardcoded values for accuracy
    if index <= len(SMALL_PRIMES) and index < FORECAST_SMALL_THRESHOLD:
        return SMALL_PRIMES[index - 1]

    # For larger indices, use refined PNT approximation
    # p_n ≈ n * (log n + log log n - 1)
    n = index
    estimate = n * (log_n(n) + log_log_n(n) - 1.0)

    # Return as integer (truncated)
    return int(estimate)
