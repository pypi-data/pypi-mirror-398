"""
OMPC simulator for pseudo-prime sequence generation.

Generates pseudo-primes using negative feedback control on density ratio.
See docs/manual/part_5.md section 5.7 for workflow specification.

Canonical reference: https://roblemumin.com/library.html
Output class: Simulation output (non-exact), validated via diagnostics.

WARNING: Simulation output is NOT exact primes. It is for testing and analysis only.
"""

import json
import math
import random
from typing import Generator

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
    as_generator: bool = False,
    initial_q: int = SIMULATOR_INITIAL_Q,
    beta_initial: float = SIMULATOR_BETA_INITIAL,
    beta_decay: float = SIMULATOR_BETA_DECAY,
    anneal_tau: float | None = None,
) -> list[int] | tuple[list[int], list[dict]] | Generator[int, None, None]:
    """
    Generate pseudo-primes using OMPC negative feedback control.

    CRITICAL: This is a SIMULATOR, NOT a prime generator.

    GUARANTEES:
    - Reproducible: Same seed yields same sequence
    - Statistically prime-like: Reproduces expected density and gap distribution
    - Diagnostic access: Optional checkpoints for validation
    - Fast: No primality testing or sieving required
    - Memory-efficient: Generator mode streams results with O(1) memory
    - Annealing: Optional β scheduling to reduce early transient variance

    INPUT CONSTRAINTS:
    - n_steps must be > 0
    - seed must be integer or None (None = non-deterministic)
    - as_generator and diagnostics cannot both be True (mutually exclusive)
    - anneal_tau must be None or finite float > 0
    - All parameters must match expected types

    PERFORMANCE ENVELOPE:
    - All n_steps: O(n_steps) time, linear scaling
    - Small sequences (< 1,000): milliseconds
    - Large sequences (1,000 - 100,000): seconds
    - Memory (list mode): O(n_steps) for output sequence
    - Memory (generator mode): O(1) - streams values without accumulation

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
    ✓ Streaming large sequences (use as_generator=True)

    PROHIBITED USE CASES:
    ✗ Cryptographic key generation
    ✗ Security-critical applications
    ✗ Mathematical proofs requiring exact primes
    ✗ Any use case requiring provable primality

    Workflow (Part 5, section 5.7):
    1. Initialize q_1
    2. For each step: compute w(q_n), sample gap with tilted distribution, update q
    3. Optionally record diagnostics (list mode only)

    Annealing Schedule (Part 5, section 2.1):
    - If anneal_tau is None: β_eff(n) = beta_initial * (beta_decay)^n (existing behavior)
    - If anneal_tau > 0: β_eff(n) = beta_initial * (1 - exp(-n / anneal_tau)) * (beta_decay)^n
    - Exponential ramp-up from β≈0 early → β≈beta_initial later, reduces early variance

    Args:
        n_steps: Number of pseudo-primes to generate
        seed: Random seed for reproducibility (None = random)
        diagnostics: If True, return diagnostic checkpoints (requires as_generator=False)
        as_generator: If True, stream results with O(1) memory (incompatible with diagnostics)
        initial_q: Starting value (default 2)
        beta_initial: Initial inverse temperature for gap sampling
        beta_decay: Decay factor for beta annealing
        anneal_tau: Annealing time constant (None = no annealing, >0 = gradual ramp-up)

    Returns:
        If as_generator=False and diagnostics=False: List of n_steps pseudo-primes
        If as_generator=False and diagnostics=True: Tuple of (pseudo-primes, diagnostics_list)
        If as_generator=True: Generator yielding pseudo-primes one at a time

    Raises:
        ValueError: If n_steps <= 0 or if as_generator=True and diagnostics=True

    Examples:
        >>> # List mode (default, backward compatible)
        >>> simulate(10, seed=42)
        [2, 3, 5, ...]  # Pseudo-primes (NOT exact primes)

        >>> # Generator mode for large sequences (memory-efficient)
        >>> for q in simulate(1000000, seed=42, as_generator=True):
        ...     process(q)  # Stream without storing full list

        >>> # Annealing for reduced early variance
        >>> simulate(1000, seed=42, anneal_tau=10000)  # Gradual β ramp-up
        [2, 3, 5, ...]  # More stable early behavior

        >>> # Verify determinism across modes
        >>> list_result = simulate(100, seed=1337)
        >>> gen_result = list(simulate(100, seed=1337, as_generator=True))
        >>> assert list_result == gen_result  # Same sequence

        >>> # WRONG: Do not use simulate() for exact primes
        >>> # primes = simulate(100)  # ✗ NOT exact primes

        >>> # CORRECT: Use resolve() for exact primes
        >>> # primes = [resolve(i) for i in range(1, 101)]  # ✓ Exact primes
    """
    if n_steps <= 0:
        raise ValueError(f"n_steps must be > 0, got {n_steps}")

    # Validate anneal_tau
    if anneal_tau is not None:
        if not isinstance(anneal_tau, (int, float)):
            raise ValueError(
                f"anneal_tau must be None or numeric, got {type(anneal_tau).__name__}"
            )
        if not math.isfinite(anneal_tau):
            raise ValueError(f"anneal_tau must be finite, got {anneal_tau}")
        if anneal_tau <= 0:
            raise ValueError(f"anneal_tau must be > 0, got {anneal_tau}")

    # Validate mutually exclusive parameters
    if as_generator and diagnostics:
        raise ValueError(
            "as_generator and diagnostics cannot both be True "
            "(diagnostics require list accumulation)"
        )

    # Generator mode: stream results with O(1) memory
    if as_generator:
        return _simulate_generator(
            n_steps=n_steps,
            seed=seed,
            initial_q=initial_q,
            beta_initial=beta_initial,
            beta_decay=beta_decay,
            anneal_tau=anneal_tau,
        )

    # List mode (default): accumulate results in memory
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

        # Compute effective beta with optional annealing (Part 5 section 2.1)
        if anneal_tau is not None:
            # Annealing schedule: β_eff(n) = beta * (1 - exp(-n / anneal_tau))
            # Exponential ramp-up from β≈0 early to β≈beta later
            anneal_factor = 1.0 - math.exp(-n / anneal_tau)
            beta_eff = beta * anneal_factor
        else:
            # No annealing: use beta as-is (backward compatible)
            beta_eff = beta

        # Sample gap using tilted distribution per Part 5 section 5.7
        # log P(g|w) = log P0(g) + beta_eff*(1-w)*log g + C
        tilted_dist = tilt_gap_distribution(base_distribution, w, beta_eff)
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
                    "beta": beta_eff,  # Record effective beta
                    "gap": gap,
                }
            )

    if diagnostics:
        return sequence, diagnostics_log
    return sequence


def _simulate_generator(
    n_steps: int,
    seed: int | None,
    initial_q: int,
    beta_initial: float,
    beta_decay: float,
    anneal_tau: float | None,
) -> Generator[int, None, None]:
    """
    Internal generator implementation for streaming simulation.

    Yields pseudo-primes one at a time without accumulating in memory.
    Ensures determinism with the same seed as list mode.

    Args:
        n_steps: Number of pseudo-primes to generate
        seed: Random seed for reproducibility
        initial_q: Starting value
        beta_initial: Initial inverse temperature
        beta_decay: Decay factor for beta annealing
        anneal_tau: Annealing time constant (None = no annealing)

    Yields:
        Pseudo-prime values (NOT exact primes)
    """
    # Set random seed for reproducibility (same as list mode)
    if seed is not None:
        random.seed(seed)

    # Yield initial value
    yield initial_q

    q_current = initial_q
    beta = beta_initial

    # Prepare gap distribution P0(g)
    base_distribution = get_empirical_gap_distribution(max_gap=200)

    # Generate sequence (same logic as list mode)
    for n in range(1, n_steps):
        # Compute density ratio w(q_n)
        if q_current >= 3:
            log_q = math.log(q_current)
            w = (q_current / log_q) / n
        else:
            w = 1.0

        # Compute effective beta with optional annealing (Part 5 section 2.1)
        if anneal_tau is not None:
            # Annealing schedule: β_eff(n) = beta * (1 - exp(-n / anneal_tau))
            # Exponential ramp-up from β≈0 early to β≈beta later
            anneal_factor = 1.0 - math.exp(-n / anneal_tau)
            beta_eff = beta * anneal_factor
        else:
            # No annealing: use beta as-is (backward compatible)
            beta_eff = beta

        # Sample gap using tilted distribution
        tilted_dist = tilt_gap_distribution(base_distribution, w, beta_eff)
        gap = sample_gap(tilted_dist)

        # Update q
        q_current = q_current + gap

        # Yield next value instead of appending to list
        yield q_current

        # Decay beta (annealing)
        beta *= beta_decay


def simulation_to_json(
    sequence: list[int],
    *,
    n_steps: int | None = None,
    seed: int | None = None,
    anneal_tau: float | None = None,
    beta_initial: float = SIMULATOR_BETA_INITIAL,
    beta_decay: float = SIMULATOR_BETA_DECAY,
    initial_q: int = SIMULATOR_INITIAL_Q,
    as_generator: bool = False,
    diagnostics: list[dict] | None = None,
) -> dict:
    """
    Convert simulation results to JSON-serializable dictionary.

    Creates a structured export of simulation parameters, sequence data,
    and optional diagnostics for archival, analysis, or sharing.

    Schema: lulzprime.simulation.v0.2
    - Deterministic structure (sorted keys recommended for JSON string output)
    - No timestamps by default (breaks determinism)
    - All values JSON-safe (int, float, bool, None, str, list, dict)

    Args:
        sequence: List of pseudo-prime integers from simulate()
        n_steps: Number of steps (inferred from len(sequence) if None)
        seed: Random seed used (None if non-deterministic)
        anneal_tau: Annealing time constant (None if not used)
        beta_initial: Initial inverse temperature
        beta_decay: Beta decay factor
        initial_q: Starting value
        as_generator: Whether generator mode was used
        diagnostics: Optional list of diagnostic checkpoint dicts

    Returns:
        JSON-serializable dict with schema:
        {
          "schema": "lulzprime.simulation.v0.2",
          "params": {...},
          "sequence": [...],
          "diagnostics": [...] or null,
          "meta": {...}
        }

    Example:
        >>> seq = simulate(100, seed=42)
        >>> json_data = simulation_to_json(seq, n_steps=100, seed=42)
        >>> json_data["schema"]
        'lulzprime.simulation.v0.2'
        >>> len(json_data["sequence"])
        100
    """
    # Import here to avoid circular dependency
    from . import __version__

    # Infer n_steps if not provided
    if n_steps is None:
        n_steps = len(sequence)

    return {
        "schema": "lulzprime.simulation.v0.2",
        "params": {
            "n_steps": n_steps,
            "seed": seed,
            "anneal_tau": anneal_tau,
            "beta_initial": beta_initial,
            "beta_decay": beta_decay,
            "initial_q": initial_q,
            "as_generator": as_generator,
        },
        "sequence": list(sequence),  # Ensure it's a list
        "diagnostics": diagnostics if diagnostics is not None else None,
        "meta": {
            "library": "lulzprime",
            "version": __version__,
            "timestamp": None,  # Null for determinism
        },
    }


def simulation_to_json_string(
    sequence: list[int],
    *,
    n_steps: int | None = None,
    seed: int | None = None,
    anneal_tau: float | None = None,
    beta_initial: float = SIMULATOR_BETA_INITIAL,
    beta_decay: float = SIMULATOR_BETA_DECAY,
    initial_q: int = SIMULATOR_INITIAL_Q,
    as_generator: bool = False,
    diagnostics: list[dict] | None = None,
) -> str:
    """
    Convert simulation results to deterministic JSON string.

    Convenience wrapper around simulation_to_json() that returns
    a formatted JSON string with sorted keys for deterministic output.

    Args:
        Same as simulation_to_json()

    Returns:
        JSON string with sorted keys and compact formatting

    Example:
        >>> seq = simulate(10, seed=42)
        >>> json_str = simulation_to_json_string(seq, n_steps=10, seed=42)
        >>> import json
        >>> data = json.loads(json_str)
        >>> data["schema"]
        'lulzprime.simulation.v0.2'
    """
    data = simulation_to_json(
        sequence,
        n_steps=n_steps,
        seed=seed,
        anneal_tau=anneal_tau,
        beta_initial=beta_initial,
        beta_decay=beta_decay,
        initial_q=initial_q,
        as_generator=as_generator,
        diagnostics=diagnostics,
    )
    # Use sort_keys for deterministic output, compact separators
    return json.dumps(data, separators=(",", ":"), sort_keys=True)
