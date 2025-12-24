"""
Analytic forecasting for prime locations.

Provides refined Prime Number Theorem approximations to estimate p_n.
See docs/manual/part_5.md section 5.2 for workflow specification.

Canonical reference: https://roblemumin.com/library.html
Output class: Tier C (Estimate only)
"""

from .config import FORECAST_SMALL_THRESHOLD, SMALL_PRIMES
from .utils import log_log_n, log_n, validate_index


def forecast(index: int, refinement_level: int = 1) -> int:
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
    - refinement_level must be 1, 2, or 3 (higher levels reserved for future)
    - No practical upper bound (formula works for arbitrarily large indices)

    PERFORMANCE ENVELOPE:
    - All indices: O(1) time, microseconds
    - refinement_level=1: Base PNT → <0.3% error for n ≥ 10^6
    - refinement_level=2: Higher-order PNT → <0.2% error for n ≥ 10^8
    - refinement_level=3: Reserved for future (additional higher-order terms)
    - Small indices (< 50): exact via hardcoded table

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
        refinement_level: Level of PNT refinement (1=base, 2=higher-order, 3=reserved)

    Returns:
        Estimated value of p_index (integer, may not be exact or prime)

    Raises:
        ValueError: If index < 1 or refinement_level not in {1, 2, 3}
        TypeError: If index is not an integer

    Examples:
        >>> forecast(1)  # Estimate for p_1
        2
        >>> forecast(10)  # Estimate for p_10 (actual = 29)
        28  # Approximate, not exact
        >>> forecast(1000000, refinement_level=1)  # Level 1: ~0.29% error
        15441302
        >>> forecast(1000000, refinement_level=2)  # Level 2: ~0.039% error
        15479821
    """
    validate_index(index)

    # Validate refinement_level
    if refinement_level not in {1, 2, 3}:
        raise ValueError(
            f"refinement_level must be 1, 2, or 3, got {refinement_level}"
        )

    # For small indices, use hardcoded values for accuracy
    if index <= len(SMALL_PRIMES) and index < FORECAST_SMALL_THRESHOLD:
        return SMALL_PRIMES[index - 1]

    # For larger indices, use refined PNT approximation
    # Base formula: p_n ≈ n * (log n + log log n - 1)
    n = index
    ln = log_n(n)
    lln = log_log_n(n)

    # Level 1: Base PNT approximation
    estimate = n * (ln + lln - 1.0)

    # Level 2: Add higher-order term (log log n - 2) / log n
    if refinement_level >= 2:
        estimate += n * (lln - 2.0) / ln

    # Level 3: Add next higher-order term (reserved for future)
    if refinement_level >= 3:
        estimate += n * (lln**2 - 6.0 * lln + 11.0) / (2.0 * ln**2)

    # Round to nearest integer (v0.2.0 refinement for improved accuracy)
    return int(estimate + 0.5)
