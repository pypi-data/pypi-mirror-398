"""
OMPC simulator for pseudo-prime sequence generation.

Generates pseudo-primes using negative feedback control on density ratio.
See docs/manual/part_5.md section 5.7 for workflow specification.

Canonical reference: https://roblemumin.com/library.html
Output class: Simulation output (non-exact), validated via diagnostics.

WARNING: Simulation output is NOT exact primes. It is for testing and analysis only.
"""

import math
import random

from .config import (
    SIMULATOR_BETA_DECAY,
    SIMULATOR_BETA_INITIAL,
    SIMULATOR_DEFAULT_SEED,
    SIMULATOR_INITIAL_Q,
)
from .gaps import get_empirical_gap_distribution, sample_gap, tilt_gap_distribution


def simulate(
    n_steps: int,
    *,
    seed: int | None = SIMULATOR_DEFAULT_SEED,
    diagnostics: bool = False,
    initial_q: int = SIMULATOR_INITIAL_Q,
    beta_initial: float = SIMULATOR_BETA_INITIAL,
    beta_decay: float = SIMULATOR_BETA_DECAY,
) -> list[int] | tuple[list[int], list[dict]]:
    """
    Generate pseudo-primes using OMPC negative feedback control.

    CRITICAL: This is a SIMULATOR, NOT a prime generator.

    GUARANTEES:
    - Reproducible: Same seed yields same sequence
    - Statistically prime-like: Reproduces expected density and gap distribution
    - Diagnostic access: Optional checkpoints for validation
    - Fast: No primality testing or sieving required

    INPUT CONSTRAINTS:
    - n_steps must be > 0
    - seed must be integer or None (None = non-deterministic)
    - All parameters must match expected types

    PERFORMANCE ENVELOPE:
    - All n_steps: O(n_steps) time, linear scaling
    - Small sequences (< 1,000): milliseconds
    - Large sequences (1,000 - 100,000): seconds
    - Memory: O(n_steps) for output sequence

    DOES NOT GUARANTEE:
    - Exactness: simulate(n)[i] may NOT equal resolve(i)
    - Primality: returned values may not be prime
    - Cryptographic properties: NOT suitable for security applications
    - Truth generation: output is for testing/validation, not authoritative

    WARNING - CRITICAL MISUSE CASE:
    DO NOT use simulate() output as if it were exact primes.
    - simulate() is for testing, validation, and analysis
    - Use resolve() for exact primes
    - Use is_prime() to verify primality
    - Simulation output has no mathematical guarantee of primality

    INTENDED USE CASES:
    ✓ Testing prime-like algorithms
    ✓ Statistical validation of gap distributions
    ✓ Benchmarking and diagnostics
    ✓ Educational demonstrations

    PROHIBITED USE CASES:
    ✗ Cryptographic key generation
    ✗ Security-critical applications
    ✗ Mathematical proofs requiring exact primes
    ✗ Any use case requiring provable primality

    Workflow (Part 5, section 5.7):
    1. Initialize q_1
    2. For each step: compute w(q_n), sample gap with tilted distribution, update q
    3. Optionally record diagnostics

    Args:
        n_steps: Number of pseudo-primes to generate
        seed: Random seed for reproducibility (None = random)
        diagnostics: If True, return diagnostic checkpoints
        initial_q: Starting value (default 2)
        beta_initial: Initial inverse temperature for gap sampling
        beta_decay: Decay factor for beta annealing

    Returns:
        If diagnostics=False: List of n_steps pseudo-primes (NOT exact primes)
        If diagnostics=True: Tuple of (pseudo-primes, diagnostics_list)

    Raises:
        ValueError: If n_steps <= 0

    Examples:
        >>> simulate(10, seed=42)  # Reproducible sequence
        [2, 3, 5, ...]  # Pseudo-primes (NOT exact primes)

        >>> # WRONG: Do not use simulate() for exact primes
        >>> # primes = simulate(100)  # ✗ NOT exact primes

        >>> # CORRECT: Use resolve() for exact primes
        >>> # primes = [resolve(i) for i in range(1, 101)]  # ✓ Exact primes
    """
    if n_steps <= 0:
        raise ValueError(f"n_steps must be > 0, got {n_steps}")

    # Set random seed for reproducibility
    if seed is not None:
        random.seed(seed)

    # Initialize
    sequence = [initial_q]
    diagnostics_log = []

    q_current = initial_q
    beta = beta_initial

    # Prepare gap distribution P0(g) (Part 5 section 5.7 step 3)
    base_distribution = get_empirical_gap_distribution(max_gap=200)

    # Generate sequence
    for n in range(1, n_steps):
        # Compute density ratio w(q_n) = (q_n / log q_n) / n (Part 5 section 5.7 step 4)
        # This measures how close we are to the expected prime density
        if q_current >= 3:
            log_q = math.log(q_current)
            w = (q_current / log_q) / n
        else:
            w = 1.0  # Default for small q

        # Sample gap using tilted distribution per Part 5 section 5.7
        # log P(g|w) = log P0(g) + beta*(1-w)*log g + C
        tilted_dist = tilt_gap_distribution(base_distribution, w, beta)
        gap = sample_gap(tilted_dist)

        # Update q
        q_current = q_current + gap
        sequence.append(q_current)

        # Decay beta (annealing)
        beta *= beta_decay

        # Record diagnostics if requested
        if diagnostics and n % 10 == 0:  # Sample sparsely
            diagnostics_log.append(
                {
                    "step": n,
                    "q": q_current,
                    "w": w,
                    "beta": beta,
                    "gap": gap,
                }
            )

    if diagnostics:
        return sequence, diagnostics_log
    return sequence
