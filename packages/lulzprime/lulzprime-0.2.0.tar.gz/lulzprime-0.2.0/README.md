<p align="center">
  <img src="https://raw.githubusercontent.com/RobLe3/lulzprime/main/lulzprime.jpg" alt="LULZprime logo" width="320">
</p>

# LULZprime

**Prime resolution and navigation library based on OMPC**

LULZprime is a Python library for efficient prime number resolution using analytic forecasting + exact correction, derived from the OMPC approach. It enables fast access to the nth prime and primes in numeric intervals without requiring full enumeration or sieving.

## What LULZprime Is

- **Prime navigator**: Efficiently locates primes using analytic forecasting + exact correction
- **Deterministic resolver**: Same inputs always yield same exact primes (Tier A guarantee)
- **Hardware efficient**: Runs on low-end devices (< 25 MB memory footprint)
- **Practical up to 500k indices**: Completes within seconds to ~90s for typical use cases (with Meissel backend)
- **Well-defined guarantees**: Explicit Tier A/B/C contracts (exact, verified, estimate)
- **Sublinear algorithm**: O(x^(2/3)) complexity with Meissel-Lehmer implementation

## What LULZprime Is NOT

- **NOT a cryptographic primitive**: Not suitable for security-critical applications
- **NOT for unbounded indices**: Practical range validated to 500,000 indices
- **NOT a prime "predictor"**: Uses navigation, not prediction or guessing
- **NOT a factorization tool**: No shortcuts for integer factorization or RSA
- **NOT a replacement for crypto libraries**: Use established cryptographic tools for security

## Practical Performance

**Default backend (segmented sieve):**
- **Small indices (< 1,000):** milliseconds
- **Medium indices (1,000 - 100,000):** seconds
- **Large indices (100,000 - 250,000):** minutes

**With Meissel backend enabled (recommended for indices ≥ 250k):**
- **resolve(100k):** ~8s
- **resolve(250k):** ~18s
- **resolve(500k):** ~73s ✓ Validated

**Memory:** 0.66-1.16 MB (well under 25 MB constraint)

See `docs/PAPER_ALIGNMENT_STATUS.md` for complete performance analysis and validation results.

### Meissel-Lehmer Backend

The Meissel-Lehmer backend provides O(x^(2/3)) sublinear complexity for large indices. **Enabled by default in v0.2.0.**

```python
# Enabled automatically - no configuration needed
import lulzprime
result = lulzprime.resolve(500_000)  # Fast with Meissel backend

# Optional: Disable if needed for backward compatibility
import lulzprime.config as config
config.ENABLE_LEHMER_PI = False  # Revert to segmented sieve
```

**Default change:** v0.2.0 enables ENABLE_LEHMER_PI=True by default. Extensive validation complete (258 tests pass). Safe and reversible.

**Rollback:** Simply set `ENABLE_LEHMER_PI = False` to revert to segmented sieve.

## Guarantees

LULZprime provides three tiers of guarantees:

- **Tier A (Exact)**: `resolve()`, `resolve_many()` - Exact, deterministic, bit-identical results
- **Tier B (Verified)**: `between()`, `is_prime()`, `next_prime()`, `prev_prime()` - Verified correct via primality testing
- **Tier C (Estimate)**: `forecast()` - Analytic estimate only, NOT exact

**Determinism:** All operations use integer-only math (no floating-point drift). Same inputs always produce identical results across all platforms.

**Validation:** All results validated to 10M indices. Memory constraint < 25 MB verified. Full test coverage (258 tests passing).

See `docs/api_contract.md` for complete guarantee specifications.

## Installation

```bash
pip install lulzprime
```

Or install from source:

```bash
git clone https://github.com/RobLe3/lulzprime.git
cd lulzprime
pip install -e .
```

## CLI Quickstart

LULZprime provides a command-line interface for common operations:

```bash
# Resolve: Find the exact nth prime
python -m lulzprime resolve 100000
# Output: 1299709

# Pi: Count primes <= x
python -m lulzprime pi 1000000
# Output: 78498

# Simulate: Generate pseudo-primes (Tier C: statistical, deterministic with seed)
python -m lulzprime simulate 1000 --seed 42
# Output: 1000 pseudo-prime values, one per line

# Simulate with generator mode (low memory, streaming)
python -m lulzprime simulate 1000000 --seed 42 --generator
# Streams values without accumulating in memory

# Simulate with annealing (reduced early variance)
python -m lulzprime simulate 50000 --seed 1337 --anneal-tau 10000
# Uses dynamic β scheduling for more stable convergence

# Export simulation to JSON
python -m lulzprime simulate 100 --seed 42 --json output.json
# Creates output.json with full params, sequence, and metadata
```

Run `python -m lulzprime --help` for full command reference.

## Python API Quickstart

```python
import lulzprime

# Example 1: Get the exact 100th prime (Tier A: Exact)
p_100 = lulzprime.resolve(100)
print(f"The 100th prime is {p_100}")  # Output: 541 (exact, deterministic)

# Example 2: Get all primes in a range (Tier B: Verified)
primes = lulzprime.between(10, 30)
print(f"Primes from 10 to 30: {primes}")
# Output: [11, 13, 17, 19, 23, 29] (all verified primes)

# Example 3: Check primality (Tier B: Verified, deterministic for n < 2^64)
print(lulzprime.is_prime(541))  # True
print(lulzprime.is_prime(540))  # False

# Example 4: Navigate primes (Tier B: Verified)
next_p = lulzprime.next_prime(100)   # 101 (smallest prime >= 100)
prev_p = lulzprime.prev_prime(100)   # 97 (largest prime <= 100)

# Example 5: Forecast with refinement (Tier C: Estimate only, NOT exact)
# Use refinement_level=2 for better accuracy on large indices
estimate = lulzprime.forecast(100000000, refinement_level=2)
# More accurate than refinement_level=1, <0.2% error for n >= 10^8

# Example 6: Batch resolution for efficiency (Tier A: Exact, with π(x) caching)
indices = [1, 10, 100, 50, 25]
primes = lulzprime.resolve_many(indices)
# Returns: [2, 29, 541, 229, 97] (order preserved, faster than loop)

# Example 7: Simulation with generator mode (Tier C: statistical)
# Memory-efficient streaming for large sequences
for q in lulzprime.simulate(1000000, seed=42, as_generator=True):
    process(q)  # Stream without storing full list

# Example 8: Simulation with annealing
# Reduces early transient variance
seq = lulzprime.simulate(10000, seed=1337, anneal_tau=5000)

# Example 9: Export simulation to JSON
seq = lulzprime.simulate(100, seed=42)
json_data = lulzprime.simulation_to_json(seq, n_steps=100, seed=42)
json_str = lulzprime.simulation_to_json_string(seq, n_steps=100, seed=42)
# JSON schema: lulzprime.simulation.v0.2
```

**Important Note on Simulation (Tier C):**

The `simulate()` function generates pseudo-prime sequences that are **statistically prime-like** but NOT exact primes. Key guarantees:
- ✓ **Deterministic**: Same seed always produces same sequence
- ✓ **Statistical correctness**: Reproduces prime gap distributions and density
- ✗ **NOT identical to resolve()**: simulate(n)[i] may differ from resolve(i)
- ✗ **NOT exact primes**: Output values may not be prime
- ✗ **No cross-implementation guarantee**: Different sampling implementations may produce different sequences (even with same seed)

Use `resolve()` for exact primes. Use `simulate()` for testing, validation, and statistical analysis only.

## Public API

**Core Functions:**
- **`resolve(index)`** → Returns the exact p_index (Tier A: Exact)
- **`forecast(index, refinement_level=1)`** → Returns an analytic estimate for p_index (Tier C: Estimate)
- **`between(x, y)`** → Returns all primes in [x, y] (Tier B: Verified)
- **`next_prime(n)`** → Returns smallest prime >= n (Tier B: Verified)
- **`prev_prime(n)`** → Returns largest prime <= n (Tier B: Verified)
- **`is_prime(n)`** → Primality predicate (Tier B: Verified)
- **`simulate(n_steps, *, seed, diagnostics, as_generator, anneal_tau, ...)`** → OMPC simulator for pseudo-prime sequences (Tier C: statistical)

**Batch API (efficient multi-resolution):**
- **`resolve_many(indices)`** → Batch resolve with π(x) caching (Tier A: Exact)
- **`between_many(ranges)`** → Batch range queries (Tier B: Verified)

**JSON Export (simulation results):**
- **`simulation_to_json(sequence, ...)`** → Returns JSON-serializable dict (schema: lulzprime.simulation.v0.2)
- **`simulation_to_json_string(sequence, ...)`** → Returns deterministic JSON string

See `docs/api_contract.md` for complete API contracts and guarantee specifications.

## Safety and Determinism

**Integer-only arithmetic:** No floating-point operations. All calculations use exact integer math to prevent drift and ensure deterministic results.

**Deterministic behavior:** Same inputs always produce identical outputs across all platforms, Python versions, and runs.

**Memory safety:** All operations respect the < 25 MB memory constraint. Peak usage validated at 0.66-1.16 MB for tested indices.

**Rollback:** Meissel backend can be disabled with a one-line change (`ENABLE_LEHMER_PI = False`). All tests continue to pass with either backend.

## Core Concepts

LULZprime inherits from the OMPC approach:

1. **Analytic navigation**: Use refined Prime Number Theorem approximations to jump close to desired prime locations (O(1) estimates)
2. **Exact correction**: Use prime counting π(x) and primality tests to correct estimates and guarantee correctness
3. **Controlled stochastic modeling**: Optional simulator for validation and testing (not for truth generation)

This reframes primes from a brute-force enumeration problem into a navigable space.

**Canonical reference**: [OMPC Paper at roblemumin.com](https://roblemumin.com/library.html)

## Documentation

- **Quick start**: This README (CLI + Python API examples)
- **Development manual (current)**: `docs/0.2.0/part_0.md` through `part_9.md`
- **Development manual (historical)**: `docs/0.1.2/part_0.md` through `part_9.md`
- **Developer guide**: `docs/autostart.md` and `docs/defaults.md`
- **Canonical paper**: [OMPC at roblemumin.com](https://roblemumin.com/library.html)

**Key Documentation:**
- Part 0: Foundation and invariants
- Part 2: Contracts and guarantees (Tier A/B/C definitions)
- Part 6: Forecasting and approximation (refinement_level usage)
- Part 8: Extensions and usability (CLI, JSON export)
- Part 9: Historical and maintenance (phase tracking)

## Maintenance Status

**Current Status:** Completed reference implementation (v0.2.0)

LULZprime is a **finished artifact**. The implementation has achieved full paper alignment and is production-ready for indices up to 500k.

**Maintenance model:**
- **Bug fixes:** Critical bugs will be addressed
- **Security issues:** Reported vulnerabilities will be fixed
- **No active feature development:** The library is feature-complete for its intended scope
- **No performance tuning:** Python implementation is at optimum (Phase 3 validated)
- **Community contributions:** Bug fixes and documentation improvements welcome (see CONTRIBUTING.md)

**What this means:**
- The library is stable and safe to use in production
- API will not change (backward compatibility preserved)
- No new features planned (scope is deliberately limited)
- All 258 tests continue to pass
- Meissel-Lehmer backend enabled by default (ENABLE_LEHMER_PI = True)

**Future work (out of scope):**
- C/Rust port for paper-exceedance performance (10-50× gains possible)
- P3 correction or Deleglise-Rivat algorithms (research-level)

See `docs/PAPER_EXCEEDANCE_ROADMAP.md` for potential future directions (informational only).

## How to Support

If you leverage this library in a production environment and it helps you save money—whether through reduced computational costs, faster processing, or more efficient resource usage—I would appreciate it if you donated 1% of the budget it saves you to homeless people or local homelessness support organizations.

**Ways to help:**
- Donate to local homeless shelters, food banks, or support services
- Support organizations working on homelessness prevention
- Contribute to housing-first initiatives in your community

This request is entirely voluntary and comes with no obligation. The library remains freely available under the MIT license regardless of whether you choose to donate.

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/RobLe3/lulzprime.git
cd lulzprime

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=src/lulzprime --cov-report=html
```

### Project Structure

```
lulzprime/
├── src/lulzprime/      # Core deterministic implementation
├── tests/              # Test suite (258 tests, all passing)
├── docs/               # Design decisions, validation, release notes
│   ├── 0.2.0/          # Development manual (v0.2.0, current)
│   ├── 0.1.2/          # Development manual (v0.1.2, historical)
│   ├── adr/            # Architecture Decision Records
│   ├── autostart.md    # Startup procedure and consultation order
│   └── defaults.md     # Repository rules and defaults
├── benchmarks/         # Manual benchmarks (not run in CI)
└── experiments/        # One-off validation scripts
```

### Contributing

See `CONTRIBUTING.md` for contribution guidelines.

**Scope:** Bug fixes and documentation improvements are welcome. New features or algorithm changes are out of scope (library is feature-complete).

## Non-Goals

LULZprime explicitly does **NOT** claim or implement:
- Factorization acceleration
- Cryptographic breaks (RSA/ECC/discrete log)
- "Predicting primes" as deterministic truth
- Replacement for cryptographic entropy sources

This library is an efficiency and navigation toolkit, consistent with the paper's scope.

## License

MIT License - See `LICENSE` file for details.

## Citation

If you use LULZprime in academic work, please cite the canonical OMPC paper available at:
https://roblemumin.com/library.html

## Support & Issues

- **Issues**: https://github.com/RobLe3/lulzprime/issues
- **Documentation**: https://github.com/RobLe3/lulzprime/tree/main/docs
- **Repository**: https://github.com/RobLe3/lulzprime

---

**Status**: v0.2.0 - Full paper alignment achieved ✓

**Test Coverage**: 258 passing (225 core + 15 CLI + 18 JSON export)
**Validation**: resolve(500k) measured at 73.044s with Meissel backend
**Memory**: 1.16 MB (< 25 MB constraint)
**Determinism**: Bit-identical results, integer-only math

Generated with documentation-first development approach.
