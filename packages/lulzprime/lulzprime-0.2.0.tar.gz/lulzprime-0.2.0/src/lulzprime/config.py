"""
Configuration and default parameters for lulzprime.

Defines tunables, thresholds, and operational defaults.
See docs/manual/part_2.md for constraints.
"""

# Performance constraints (Part 2, section 2.5)
MAX_MEMORY_MB = 25  # Target maximum memory footprint

# Small primes cache for optimization
# These are used for quick lookups and divisibility checks
SMALL_PRIMES = [
    2,
    3,
    5,
    7,
    11,
    13,
    17,
    19,
    23,
    29,
    31,
    37,
    41,
    43,
    47,
    53,
    59,
    61,
    67,
    71,
    73,
    79,
    83,
    89,
    97,
]

# Forecast thresholds
# Below this index, use hardcoded lookup instead of analytic estimate
FORECAST_SMALL_THRESHOLD = 100

# π(x) implementation defaults
PI_CACHE_SIZE = 1000  # Configurable cache size for π(x) results

# Primality testing configuration
# For deterministic Miller-Rabin in 64-bit range
MILLER_RABIN_BASES_64BIT = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]

# Diagnostic sampling rate (Part 7)
# Sample diagnostics every N steps to control overhead
DIAGNOSTIC_SAMPLE_RATE = 100

# Simulator defaults (Part 5, section 5.7)
SIMULATOR_DEFAULT_SEED = None  # None = random, int = deterministic
SIMULATOR_INITIAL_Q = 2
SIMULATOR_BETA_INITIAL = 1.0
SIMULATOR_BETA_DECAY = 0.99

# Parallel π(x) configuration (opt-in, ADR 0004)
# Note: These settings are for pi_parallel() only, NOT used by default resolve()
ENABLE_PARALLEL_PI = False  # Opt-in flag (not currently wired to auto-use)
PARALLEL_PI_WORKERS = 8  # Default worker count (capped at min(cpu_count, 8))
PARALLEL_PI_THRESHOLD = 1_000_000  # Minimum x for parallel (avoid overhead below)

# Meissel π(x) configuration (v0.2.0 default, ADR 0005)
# Meissel-Lehmer with P2 correction (_pi_meissel) is implemented and validated
# Performance: 8.33× faster than segmented sieve at 10M (π(x)-level benchmark)
# Resolve-level evidence: segmented impractical at 150k+ (timeouts),
#   Meissel completes 250k in 17.5s (>3.43× speedup vs >60s timeout)
# ENABLED in v0.2.0 per docs/defaults.md section 8 (Meissel-Lehmer π(x) backend enabled by default)
ENABLE_LEHMER_PI = True  # v0.2.0 default - activated for Tier B guarantees at large n
LEHMER_PI_THRESHOLD = 250_000  # Evidence-backed from resolve validation (150k+ timeout)
