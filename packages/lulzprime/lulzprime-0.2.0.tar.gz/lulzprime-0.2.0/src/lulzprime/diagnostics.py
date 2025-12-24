"""
Diagnostics, verification, and self-checks.

Provides observational tools for correctness validation and performance monitoring.
See docs/manual/part_7.md for verification requirements.

Canonical reference: https://roblemumin.com/library.html

IMPORTANT: Diagnostics must observe only. They must never alter computational results.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


def verify_resolution(result: int, index: int, pi_func: Callable, is_prime_func: Callable) -> bool:
    """
    Verify that result is the exact p_index (Tier A verification).

    From Part 7, section 7.3:
    - Verify pi(result) == index
    - Verify is_prime(result) == True

    Args:
        result: Claimed value of p_index
        index: Prime index
        pi_func: Prime counting function π(x)
        is_prime_func: Primality testing function

    Returns:
        True if verification passes

    Raises:
        AssertionError: If verification fails (hard error)
    """
    # Check primality
    if not is_prime_func(result):
        raise AssertionError(f"Resolution verification failed: result {result} is not prime")

    # Check index
    pi_result = pi_func(result)
    if pi_result != index:
        raise AssertionError(
            f"Resolution verification failed: pi({result}) = {pi_result} != {index}"
        )

    return True


def verify_range(primes: list[int], is_prime_func: Callable) -> bool:
    """
    Verify that a range result contains only primes in correct order (Tier B).

    From Part 7, section 7.3:
    - Each value must be prime
    - Ordering must be strictly increasing
    - No duplicates

    Args:
        primes: List of claimed primes
        is_prime_func: Primality testing function

    Returns:
        True if verification passes

    Raises:
        AssertionError: If verification fails
    """
    if not primes:
        return True

    # Check all are prime
    for p in primes:
        if not is_prime_func(p):
            raise AssertionError(f"Range verification failed: {p} is not prime")

    # Check strictly increasing
    for i in range(1, len(primes)):
        if primes[i] <= primes[i - 1]:
            raise AssertionError(f"Range verification failed: not strictly increasing at index {i}")

    return True


def check_forecast_quality(
    index: int, forecast_value: int, pi_func: Callable, epsilon: float = 0.1
) -> dict[str, Any]:
    """
    Check forecast quality (Tier C sanity check).

    From Part 7, section 7.3:
    abs(pi(forecast(n)) - n) / n < ε (configurable, non-fatal)

    Args:
        index: Prime index
        forecast_value: Forecasted value
        pi_func: Prime counting function
        epsilon: Relative error threshold

    Returns:
        Dictionary with diagnostic info:
        - 'passed': bool
        - 'relative_error': float
        - 'pi_forecast': int
    """
    pi_forecast = pi_func(forecast_value)
    relative_error = abs(pi_forecast - index) / index

    return {
        "passed": relative_error < epsilon,
        "relative_error": relative_error,
        "pi_forecast": pi_forecast,
        "threshold": epsilon,
    }


def simulator_diagnostics(sequence: list[int], pi_func: Callable) -> dict[str, Any]:
    """
    Compute diagnostics for OMPC simulator output.

    From Part 7, section 7.4:
    - Density alignment: track pi(q_n) / n
    - Convergence: verify pi(q_n) / n → 1 as n grows
    - Drift detection

    Args:
        sequence: List of pseudo-primes from simulator
        pi_func: Prime counting function

    Returns:
        Dictionary with diagnostic metrics
    """

    if not sequence:
        return {"error": "empty sequence"}

    n = len(sequence)
    q_final = sequence[-1]

    # Compute density ratio at final point
    pi_final = pi_func(q_final)
    density_ratio = pi_final / n if n > 0 else 0.0

    # Check several points for convergence trend
    checkpoints = []
    for i in [n // 4, n // 2, 3 * n // 4, n - 1]:
        if i > 0 and i < len(sequence):
            q_i = sequence[i]
            pi_i = pi_func(q_i)
            ratio_i = pi_i / (i + 1)
            checkpoints.append(
                {
                    "step": i + 1,
                    "q": q_i,
                    "pi": pi_i,
                    "density_ratio": ratio_i,
                }
            )

    # Compute drift (deviation from expected ratio of 1.0)
    drift = abs(density_ratio - 1.0)

    return {
        "n_steps": n,
        "q_final": q_final,
        "pi_final": pi_final,
        "density_ratio": density_ratio,
        "drift": drift,
        "convergence_acceptable": drift < 0.15,  # Threshold from paper
        "checkpoints": checkpoints,
    }


@dataclass
class ResolveStats:
    """
    Statistics collector for resolve() internal operations.

    Tracks performance-relevant metrics during resolution without altering results.
    Disabled by default - must be explicitly threaded via dependency injection.

    Attributes:
        pi_calls: Number of π(x) function calls during resolution
        binary_search_iterations: Number of binary search iterations
        correction_backward_steps: Number of backward correction steps
        correction_forward_steps: Number of forward correction steps
        forecast_value: Initial forecast estimate
        final_result: Final resolved prime value
    """

    pi_calls: int = 0
    binary_search_iterations: int = 0
    correction_backward_steps: int = 0
    correction_forward_steps: int = 0
    forecast_value: int = 0
    final_result: int = 0

    def increment_pi_calls(self) -> None:
        """Record a π(x) function call."""
        self.pi_calls += 1

    def increment_binary_iterations(self) -> None:
        """Record a binary search iteration."""
        self.binary_search_iterations += 1

    def increment_backward_steps(self) -> None:
        """Record a backward correction step."""
        self.correction_backward_steps += 1

    def increment_forward_steps(self) -> None:
        """Record a forward correction step."""
        self.correction_forward_steps += 1

    def set_forecast(self, value: int) -> None:
        """Record forecast value."""
        self.forecast_value = value

    def set_result(self, value: int) -> None:
        """Record final result."""
        self.final_result = value

    def to_dict(self) -> dict[str, Any]:
        """Convert stats to dictionary for reporting."""
        return {
            "pi_calls": self.pi_calls,
            "binary_search_iterations": self.binary_search_iterations,
            "correction_backward_steps": self.correction_backward_steps,
            "correction_forward_steps": self.correction_forward_steps,
            "forecast_value": self.forecast_value,
            "final_result": self.final_result,
        }


@dataclass
class MeisselStats:
    """
    Diagnostic statistics for Meissel π(x) backend.

    Tracks performance and resource usage metrics for Meissel-Lehmer algorithm.
    Opt-in only - used in experiments and benchmarks, not production resolve().

    Attributes:
        phi_calls: Number of φ(x, a) function calls
        phi_cache_size: Peak size of φ memoization cache
        pi_cache_size: Peak size of P2 π cache
        recursion_depth_max: Maximum recursion depth reached
        recursion_guard_trips: Number of times recursion guard triggered
    """

    phi_calls: int = 0
    phi_cache_size: int = 0
    pi_cache_size: int = 0
    recursion_depth_max: int = 0
    recursion_guard_trips: int = 0

    def increment_phi_calls(self) -> None:
        """Record a φ(x, a) function call."""
        self.phi_calls += 1

    def update_phi_cache_size(self, size: int) -> None:
        """Update peak φ cache size."""
        self.phi_cache_size = max(self.phi_cache_size, size)

    def update_pi_cache_size(self, size: int) -> None:
        """Update peak P2 π cache size."""
        self.pi_cache_size = max(self.pi_cache_size, size)

    def update_recursion_depth(self, depth: int) -> None:
        """Update maximum recursion depth."""
        self.recursion_depth_max = max(self.recursion_depth_max, depth)

    def increment_recursion_guard_trips(self) -> None:
        """Record a recursion guard trip."""
        self.recursion_guard_trips += 1

    def to_dict(self) -> dict[str, Any]:
        """Convert stats to dictionary for reporting."""
        return {
            "phi_calls": self.phi_calls,
            "phi_cache_size": self.phi_cache_size,
            "pi_cache_size": self.pi_cache_size,
            "recursion_depth_max": self.recursion_depth_max,
            "recursion_guard_trips": self.recursion_guard_trips,
        }
