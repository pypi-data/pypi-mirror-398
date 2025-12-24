"""
Gap distributions for OMPC simulation.

Provides empirical and theoretical gap distributions for pseudo-prime generation.
See docs/manual/part_5.md section 5.7 for usage in simulator.

Canonical reference: https://roblemumin.com/library.html
"""


def get_empirical_gap_distribution(
    max_gap: int = 100,
) -> dict[int, float]:
    """
    Return empirical gap distribution P0(g) for small primes.

    Uses exponentially decaying distribution to approximate real prime gap statistics.
    Small gaps (2, 4, 6) are heavily favored, with probability decreasing exponentially.

    Args:
        max_gap: Maximum gap to include

    Returns:
        Dictionary mapping gap -> probability (normalized)
    """
    import math

    distribution = {}
    total_weight = 0.0

    # Use exponential decay: weight ~ exp(-g/scale)
    # This gives small gaps much higher probability
    # Scale tuned so average gap ~ 5-7 (realistic for primes in our range)
    scale = 8.0

    for g in range(2, max_gap + 1, 2):  # Only even gaps (odd primes)
        # Exponential decay with additional 1/g factor for heavy tail
        weight = math.exp(-g / scale) / math.sqrt(g)
        distribution[g] = weight
        total_weight += weight

    # Normalize
    for g in distribution:
        distribution[g] /= total_weight

    return distribution


def tilt_gap_distribution(
    base_distribution: dict[int, float],
    w: float,
    beta: float,
) -> dict[int, float]:
    """
    Apply density-based tilting to gap distribution.

    From Part 5, section 5.7:
    log P(g|w) = log P0(g) + beta*(1-w)*log g + C

    Args:
        base_distribution: Base distribution P0(g)
        w: Density ratio
        beta: Inverse temperature

    Returns:
        Tilted distribution (normalized)
    """
    import math

    tilted = {}
    total_weight = 0.0

    for g, p0 in base_distribution.items():
        if p0 <= 0:
            continue

        # Compute tilt: log P(g|w) = log P0(g) + beta*(1-w)*log g
        log_p0 = math.log(p0)
        log_g = math.log(g)
        log_tilt = log_p0 + beta * (1 - w) * log_g

        # Convert back to probability space
        tilted_weight = math.exp(log_tilt)
        tilted[g] = tilted_weight
        total_weight += tilted_weight

    # Normalize
    if total_weight > 0:
        for g in tilted:
            tilted[g] /= total_weight

    return tilted


def sample_gap(
    distribution: dict[int, float],
    rng: object | None = None,
) -> int:
    """
    Sample a gap from the given distribution.

    Args:
        distribution: Gap distribution (gap -> probability)
        rng: Random number generator (if None, use random module)

    Returns:
        Sampled gap
    """
    import random

    gaps = list(distribution.keys())
    weights = [distribution[g] for g in gaps]

    if rng is None:
        return random.choices(gaps, weights=weights, k=1)[0]
    else:
        # Use provided RNG
        return rng.choices(gaps, weights=weights, k=1)[0]
