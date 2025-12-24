"""
lulzprime – Prime resolution and navigation library based on OMPC.

Canonical reference: https://roblemumin.com/library.html

This library provides efficient prime number resolution using analytic
forecasting + exact correction, without requiring full enumeration or sieving.

Public API (as defined in docs/manual/part_4.md and docs/api_contract.md):
- resolve(index) -> int: Returns the exact p_index
- forecast(index) -> int: Returns an analytic estimate for p_index
- between(x, y) -> list[int]: Returns all primes in [x, y]
- next_prime(n) -> int: Returns smallest prime >= n
- prev_prime(n) -> int: Returns largest prime <= n
- is_prime(n) -> bool: Primality predicate
- simulate(...) -> list[int]: OMPC simulator (optional mode)

Batch API (efficient multi-resolution):
- resolve_many(indices) -> list[int]: Batch resolve with π(x) caching
- between_many(ranges) -> list[list[int]]: Batch range queries
"""

__version__ = "0.2.0"

# Public API exports
from .batch import between_many, resolve_many
from .forecast import forecast
from .primality import is_prime
from .resolve import between, next_prime, prev_prime, resolve
from .simulator import simulate, simulation_to_json, simulation_to_json_string

__all__ = [
    "resolve",
    "forecast",
    "between",
    "next_prime",
    "prev_prime",
    "is_prime",
    "simulate",
    "resolve_many",
    "between_many",
    "simulation_to_json",
    "simulation_to_json_string",
]
