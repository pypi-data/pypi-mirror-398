"""
Type definitions and protocols for lulzprime.

This module defines internal interfaces and type aliases used across the library.
"""

from typing import Protocol


class PrimeCounter(Protocol):
    """
    Protocol for π(x) (prime counting function) backends.

    Must be monotone and correct for tested ranges.
    See docs/manual/part_4.md section 4.7.
    """

    def pi(self, x: int) -> int:
        """
        Return the exact count of primes <= x.

        Args:
            x: Upper bound for counting

        Returns:
            Number of primes p with p <= x
        """
        ...


class PrimalityTester(Protocol):
    """
    Protocol for primality testing backends.

    Must state guarantee scope (deterministic range or probabilistic).
    See docs/manual/part_4.md section 4.7.
    """

    def is_prime(self, n: int) -> bool:
        """
        Test whether n is prime.

        Args:
            n: Integer to test

        Returns:
            True if n is prime, False otherwise
        """
        ...
