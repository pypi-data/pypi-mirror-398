"""
Shared utility functions for lulzprime.

This module contains helper functions used across multiple modules.
"""

import math
from functools import lru_cache


@lru_cache(maxsize=2048)
def log_n(n: int) -> float:
    """
    Compute natural logarithm of n with appropriate handling.

    Cached with LRU (maxsize=2048) for performance in hot paths.
    Cache hit rate >95% in typical workloads (Part 1, section 2.1).

    Args:
        n: Positive integer

    Returns:
        Natural logarithm of n

    Raises:
        ValueError: If n <= 0
    """
    if n <= 0:
        raise ValueError(f"log_n requires n > 0, got {n}")
    return math.log(n)


@lru_cache(maxsize=2048)
def log_log_n(n: int) -> float:
    """
    Compute log(log(n)) with appropriate handling.

    Cached with LRU (maxsize=2048) for performance in hot paths.
    Cache hit rate >95% in typical workloads (Part 1, section 2.1).

    Args:
        n: Positive integer >= 3

    Returns:
        log(log(n))

    Raises:
        ValueError: If n < 3 (log(n) must be > 1)
    """
    if n < 3:
        raise ValueError(f"log_log_n requires n >= 3, got {n}")
    return math.log(math.log(n))


def validate_index(index: int) -> None:
    """
    Validate that index is a positive integer.

    Args:
        index: Prime index to validate

    Raises:
        ValueError: If index < 1
        TypeError: If index is not an integer
    """
    if not isinstance(index, int):
        raise TypeError(f"index must be an integer, got {type(index).__name__}")
    if index < 1:
        raise ValueError(f"index must be >= 1, got {index}")


def validate_range(x: int, y: int) -> tuple[int, int]:
    """
    Validate and normalize a range [x, y] for prime queries.

    Args:
        x: Lower bound
        y: Upper bound

    Returns:
        Tuple of (normalized_x, y) where x is clamped to at least 2

    Raises:
        ValueError: If x > y or y < 2
        TypeError: If x or y are not integers
    """
    if not isinstance(x, int) or not isinstance(y, int):
        raise TypeError("Range bounds must be integers")
    if y < 2:
        raise ValueError(f"Upper bound y must be >= 2, got {y}")
    if x > y:
        raise ValueError(f"Invalid range: x={x} > y={y}")

    # Clamp x to at least 2 (no primes below 2)
    x_normalized = max(2, x)
    return x_normalized, y
