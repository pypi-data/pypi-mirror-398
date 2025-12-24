"""
Jump-adjust pipelines for prime resolution.

Provides the internal machinery for resolving p_n using forecast + π(x) refinement.
See docs/manual/part_5.md section 5.3 for canonical workflow.

Canonical reference: https://roblemumin.com/library.html
"""

from collections.abc import Callable

from .diagnostics import ResolveStats
from .forecast import forecast
from .pi import pi
from .primality import is_prime, next_prime, prev_prime


def resolve_internal(index: int) -> int:
    """
    Internal resolution pipeline: forecast → bracket → π(x) refinement → correction.

    This implements the canonical chain from Part 5, section 5.3:
    1. Get analytic forecast
    2. Bracket the target
    3. Binary search using π(x) to find minimal x where π(x) >= index
    4. Deterministic correction to exact prime

    Args:
        index: Prime index (1-based)

    Returns:
        Exact p_index

    Note: This is an internal function. Public API is in resolve.py.
    """
    # Use default pi function
    return resolve_internal_with_pi(index, pi)


def resolve_internal_with_pi(
    index: int, pi_fn: Callable[[int], int], stats: ResolveStats | None = None
) -> int:
    """
    Internal resolution pipeline with injected π(x) function.

    This variant accepts a π(x) function as a parameter, enabling
    batch operations to inject a cached version without global state mutation.

    Same workflow as resolve_internal(), but uses pi_fn instead of global pi.

    Args:
        index: Prime index (1-based)
        pi_fn: Prime counting function π(x) to use
        stats: Optional stats collector for instrumentation (default: None/disabled)

    Returns:
        Exact p_index

    Note: This is an internal function for dependency injection.
          Public API should use resolve() or resolve_many().
    """
    # Step 1: Get forecast
    guess = forecast(index)
    if stats:
        stats.set_forecast(guess)

    # Wrap pi_fn to count calls if stats is enabled
    counted_pi_fn: Callable[[int], int]
    if stats:

        def counted_pi_fn(x: int) -> int:
            stats.increment_pi_calls()
            return pi_fn(x)

    else:
        counted_pi_fn = pi_fn

    # Step 2-3: Bracket and refine using binary search with π(x)
    # Find minimal x where π(x) >= index
    x = _binary_search_pi(index, guess, counted_pi_fn, stats)

    # Step 4: Deterministic correction (Part 5, section 5.3, step 8)
    # If x is not prime, step to previous prime
    if not is_prime(x):
        x = prev_prime(x)

    # While pi(x) > index, step backward prime-by-prime
    while counted_pi_fn(x) > index:
        if stats:
            stats.increment_backward_steps()
        x = prev_prime(x - 1)

    # While pi(x) < index, step forward prime-by-prime
    # Note: Due to binary search finding minimal x where pi(x) >= index,
    # this forward step is typically a no-op, but required for Part 5 compliance
    while counted_pi_fn(x) < index:
        if stats:
            stats.increment_forward_steps()
        x = next_prime(x + 1)

    # Verification (should always pass if implementation is correct)
    if counted_pi_fn(x) != index:
        raise RuntimeError(
            f"Resolution failed: pi({x}) = {counted_pi_fn(x)} != {index}. "
            "This indicates a bug in the resolution pipeline."
        )

    if stats:
        stats.set_result(x)

    return x


def _binary_search_pi(
    target_index: int,
    guess: int,
    pi_fn: Callable[[int], int] = pi,
    stats: ResolveStats | None = None,
) -> int:
    """
    Binary search to find minimal x where π(x) >= target_index.

    Args:
        target_index: Target prime index
        guess: Initial forecast estimate
        pi_fn: Prime counting function to use (default: global pi)
        stats: Optional stats collector for instrumentation (default: None)

    Returns:
        Minimal x where π(x) >= target_index
    """
    # Establish bounds
    # Since forecast() is highly accurate (typically <1% error), use tighter bounds
    # to reduce binary search iterations. This cuts search space by ~2x.
    # Conservative bounds: 5% margin on each side (safer than analytic formula)
    lo = max(2, int(guess * 0.95))  # 5% below forecast
    hi = int(guess * 1.05)  # 5% above forecast

    # Adjust if initial bounds are wrong
    if pi_fn(lo) > target_index:
        # Widen lo downward
        lo = 2

    if pi_fn(hi) < target_index:
        # Widen hi upward (double until we exceed)
        while pi_fn(hi) < target_index:
            hi *= 2

    # Binary search for minimal x where π(x) >= target_index
    while lo < hi:
        if stats:
            stats.increment_binary_iterations()
        mid = (lo + hi) // 2
        if pi_fn(mid) < target_index:
            lo = mid + 1
        else:
            hi = mid

    return lo
