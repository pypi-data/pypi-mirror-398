"""
API contract tests for lulzprime public interface.

Verifies all contracts specified in docs/manual/part_4.md.
Tests guarantee tiers, input validation, and determinism.
"""

import pytest

import lulzprime


class TestAPIContracts:
    """Test public API contracts from Part 4."""

    def test_resolve_contract(self):
        """Test resolve() signature and basic contract (Tier A)."""
        # Should return int for valid index
        result = lulzprime.resolve(1)
        assert isinstance(result, int)
        assert result == 2  # p_1 = 2

        result = lulzprime.resolve(10)
        assert isinstance(result, int)
        assert result == 29  # p_10 = 29

    def test_resolve_input_validation(self):
        """Test resolve() input validation (Part 4, section 4.5)."""
        # index must be >= 1
        with pytest.raises(ValueError):
            lulzprime.resolve(0)

        with pytest.raises(ValueError):
            lulzprime.resolve(-1)

        # index must be int
        with pytest.raises(TypeError):
            lulzprime.resolve(1.5)

        with pytest.raises(TypeError):
            lulzprime.resolve("1")

    def test_forecast_contract(self):
        """Test forecast() signature and basic contract (Tier C)."""
        result = lulzprime.forecast(1)
        assert isinstance(result, int)

        # Forecast is an estimate, not exact
        # Just verify it returns reasonable values
        result = lulzprime.forecast(100)
        assert result > 0

    def test_between_contract(self):
        """Test between() signature and contract (Tier B)."""
        result = lulzprime.between(2, 10)
        assert isinstance(result, list)
        assert all(isinstance(p, int) for p in result)
        assert result == [2, 3, 5, 7]  # Known primes in [2, 10]

    def test_between_input_validation(self):
        """Test between() input validation (Part 4, section 4.5)."""
        # x <= y required
        with pytest.raises(ValueError):
            lulzprime.between(10, 5)

        # y >= 2 required
        with pytest.raises(ValueError):
            lulzprime.between(0, 1)

    def test_next_prime_contract(self):
        """Test next_prime() contract (Tier B)."""
        assert lulzprime.next_prime(10) == 11
        assert lulzprime.next_prime(11) == 11
        assert lulzprime.next_prime(2) == 2

    def test_prev_prime_contract(self):
        """Test prev_prime() contract (Tier B)."""
        assert lulzprime.prev_prime(10) == 7
        assert lulzprime.prev_prime(11) == 11
        assert lulzprime.prev_prime(2) == 2

        # Must raise if n < 2
        with pytest.raises(ValueError):
            lulzprime.prev_prime(1)

    def test_is_prime_contract(self):
        """Test is_prime() contract."""
        assert lulzprime.is_prime(2) is True
        assert lulzprime.is_prime(3) is True
        assert lulzprime.is_prime(4) is False
        assert lulzprime.is_prime(17) is True
        assert lulzprime.is_prime(18) is False

    def test_simulate_contract(self):
        """Test simulate() contract (optional mode)."""
        # With seed, must be deterministic
        result1 = lulzprime.simulate(10, seed=42)
        result2 = lulzprime.simulate(10, seed=42)
        assert result1 == result2

        # Must return list of ints
        assert isinstance(result1, list)
        assert all(isinstance(q, int) for q in result1)

        # With diagnostics
        result, diag = lulzprime.simulate(10, seed=42, diagnostics=True)
        assert isinstance(result, list)
        assert isinstance(diag, list)


class TestDeterminism:
    """Test determinism contract (Part 4, section 4.3)."""

    def test_resolve_deterministic(self):
        """resolve() must be deterministic."""
        result1 = lulzprime.resolve(50)
        result2 = lulzprime.resolve(50)
        assert result1 == result2

    def test_between_deterministic(self):
        """between() must be deterministic."""
        result1 = lulzprime.between(100, 200)
        result2 = lulzprime.between(100, 200)
        assert result1 == result2

    def test_simulate_deterministic_with_seed(self):
        """simulate() must be deterministic with explicit seed."""
        result1 = lulzprime.simulate(20, seed=123)
        result2 = lulzprime.simulate(20, seed=123)
        assert result1 == result2


class TestGuaranteeTiers:
    """Test guarantee tiers from Part 4, section 4.4."""

    def test_tier_a_exactness(self):
        """Tier A: resolve() returns exact p_n."""
        # Known primes for verification
        known = {
            1: 2,
            2: 3,
            3: 5,
            4: 7,
            5: 11,
            10: 29,
            25: 97,
            100: 541,
        }
        for index, expected_prime in known.items():
            assert lulzprime.resolve(index) == expected_prime

    def test_tier_b_verified(self):
        """Tier B: between() returns verified primes."""
        primes = lulzprime.between(2, 100)
        # All must be prime
        for p in primes:
            assert lulzprime.is_prime(p)

    def test_tier_c_estimate(self):
        """Tier C: forecast() is estimate only."""
        # Forecast should be close but not necessarily exact
        forecast_val = lulzprime.forecast(100)
        exact_val = lulzprime.resolve(100)

        # Should be within reasonable range (not a strict requirement)
        # Just verify it's not wildly off
        relative_error = abs(forecast_val - exact_val) / exact_val
        assert relative_error < 0.5  # Loose tolerance for estimate
