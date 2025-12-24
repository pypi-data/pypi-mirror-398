"""
Primality testing utilities.

Provides deterministic and probabilistic primality tests.
See docs/manual/part_5.md section 5.6 for workflow specification.

Canonical reference: https://roblemumin.com/library.html
Output class: Tier B (Verified within stated range)
"""

from .config import MILLER_RABIN_BASES_64BIT, SMALL_PRIMES


def is_prime(n: int) -> bool:
    """
    Test whether n is prime.

    Uses deterministic Miller-Rabin for 64-bit range with fixed bases.

    GUARANTEES:
    - Tier B (Verified): Deterministic and correct for n < 2^64
    - No false positives: If returns True, n is guaranteed prime
    - No false negatives: If n is prime and n < 2^64, returns True
    - Fast: Optimized with small prime divisibility checks

    INPUT CONSTRAINTS:
    - n must be an integer
    - n must be >= 0
    - Deterministic guarantee valid for n < 2^64 (~1.8 × 10^19)
    - For n >= 2^64: falls back to probabilistic test (not currently supported)

    PERFORMANCE ENVELOPE:
    - Small n (< 1,000): microseconds (divisibility checks)
    - Medium n (1,000 - 10^6): microseconds (Miller-Rabin)
    - Large n (10^6 - 2^64): milliseconds (Miller-Rabin with fixed bases)
    - All tests deterministic, no randomness

    DOES NOT GUARANTEE:
    - Cryptographic security (not a crypto primitive)
    - Constant time execution (timing may leak information about n)
    - Suitability for security-critical applications

    WARNING:
    Not suitable for cryptographic applications. Use established
    cryptographic libraries for security-sensitive primality testing.

    Args:
        n: Integer to test for primality

    Returns:
        True if n is prime, False otherwise

    Raises:
        ValueError: If n < 0
        TypeError: If n is not an integer

    Examples:
        >>> is_prime(2)
        True
        >>> is_prime(4)
        False
        >>> is_prime(17)
        True
    """
    if not isinstance(n, int):
        raise TypeError(f"n must be an integer, got {type(n).__name__}")
    if n < 0:
        raise ValueError(f"n must be non-negative, got {n}")

    # Handle small cases
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False

    # Check against small primes for quick rejection
    if n in SMALL_PRIMES:
        return True
    for p in SMALL_PRIMES:
        if n % p == 0:
            return False

    # For larger n, use Miller-Rabin with deterministic bases
    return _miller_rabin_deterministic(n, MILLER_RABIN_BASES_64BIT)


def _miller_rabin_deterministic(n: int, bases: list[int]) -> bool:
    """
    Deterministic Miller-Rabin primality test with fixed bases.

    Args:
        n: Odd integer > 2 to test
        bases: List of witness bases to test

    Returns:
        True if n passes all tests (is probably prime), False if composite
    """
    # Write n - 1 as 2^r * d
    r, d = 0, n - 1
    while d % 2 == 0:
        r += 1
        d //= 2

    # Test each base
    for a in bases:
        if a >= n:
            continue

        # Compute a^d mod n
        x = pow(a, d, n)

        if x == 1 or x == n - 1:
            continue

        # Square x repeatedly r-1 times
        composite = True
        for _ in range(r - 1):
            x = (x * x) % n
            if x == n - 1:
                composite = False
                break

        if composite:
            return False

    return True


def next_prime(n: int) -> int:
    """
    Return the smallest prime >= n.

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
    if n <= 2:
        return 2

    # Start at n if odd, otherwise n+1
    candidate = n if n % 2 == 1 else n + 1

    # Search forward by 2s (skip even numbers)
    while not is_prime(candidate):
        candidate += 2

    return candidate


def prev_prime(n: int) -> int:
    """
    Return the largest prime <= n.

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
    if n < 2:
        raise ValueError(f"No primes exist below 2, got n={n}")
    if n == 2:
        return 2

    # Start at n if odd, otherwise n-1
    candidate = n if n % 2 == 1 else n - 1

    # Search backward by 2s (skip even numbers)
    while candidate >= 2:
        if is_prime(candidate):
            return candidate
        candidate -= 2

    # Should not reach here given n >= 2
    raise RuntimeError(f"Failed to find prime <= {n}")
