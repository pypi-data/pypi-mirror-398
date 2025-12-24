"""
Tests for resolve() function and resolution pipeline.

Verifies workflow from docs/manual/part_5.md section 5.3.
"""

import lulzprime
from lulzprime.diagnostics import ResolveStats
from lulzprime.lookup import resolve_internal_with_pi
from lulzprime.pi import pi


class TestResolve:
    """Test resolve() function."""

    def test_resolve_small_primes(self):
        """Test resolution of first 25 primes."""
        known_primes = [
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
        for i, expected in enumerate(known_primes, start=1):
            result = lulzprime.resolve(i)
            assert result == expected, f"resolve({i}) should be {expected}, got {result}"

    def test_resolve_larger_indices(self):
        """Test resolution at larger indices."""
        # Known values from prime tables
        test_cases = {
            100: 541,
            500: 3571,
            1000: 7919,
        }
        for index, expected in test_cases.items():
            result = lulzprime.resolve(index)
            assert result == expected, f"resolve({index}) should be {expected}, got {result}"

    def test_resolve_verification(self):
        """Test that resolve() satisfies Tier A guarantees."""
        # For any resolved prime, pi(p_n) must equal n
        for index in [1, 5, 10, 50, 100]:
            p_n = lulzprime.resolve(index)

            # Verify it's prime
            assert lulzprime.is_prime(p_n), f"resolve({index}) = {p_n} is not prime"

            # Verify pi(p_n) == index
            assert pi(p_n) == index, f"pi({p_n}) != {index}"


class TestResolutionPipeline:
    """Test internal resolution pipeline workflow."""

    def test_forecast_used_as_starting_point(self):
        """Verify forecast is used in resolution pipeline."""
        from lulzprime.forecast import forecast

        index = 50
        forecast_val = forecast(index)
        resolved_val = lulzprime.resolve(index)

        # Forecast should be reasonably close (within 20% typical)
        # This isn't a requirement, just checking the forecast is sensible
        relative_diff = abs(forecast_val - resolved_val) / resolved_val
        assert relative_diff < 0.3, f"Forecast too far from actual for index {index}"

    def test_resolution_consistency(self):
        """Test that multiple calls give same result."""
        index = 75
        results = [lulzprime.resolve(index) for _ in range(5)]
        assert len(set(results)) == 1, "resolve() not deterministic"

    def test_correction_step_compliance(self):
        """
        Verify that resolve_internal implements both correction steps from Part 5.

        Part 5 section 5.3 step 8 requires:
        - While pi(x) > index, step backward prime-by-prime
        - While pi(x) < index, step forward prime-by-prime

        This structural test verifies the implementation contains both loops.
        Note: The forward step is typically a no-op due to binary search finding
        minimal x where pi(x) >= index, but it must exist for spec compliance.
        """
        import inspect

        from lulzprime.lookup import resolve_internal_with_pi

        # Get source code of resolve_internal_with_pi (actual implementation)
        source = inspect.getsource(resolve_internal_with_pi)

        # Verify both correction loops are present
        # (uses counted_pi_fn which wraps pi_fn for stats tracking)
        assert (
            "while counted_pi_fn(x) > index:" in source
        ), "Missing backward correction: 'while counted_pi_fn(x) > index'"
        assert (
            "while counted_pi_fn(x) < index:" in source
        ), "Missing forward correction: 'while counted_pi_fn(x) < index'"

        # Verify they use the correct navigation functions
        assert "prev_prime" in source, "Missing prev_prime for backward correction"
        assert "next_prime" in source, "Missing next_prime for forward correction"


class TestResolveInstrumentation:
    """Test resolve() instrumentation with ResolveStats."""

    def test_stats_no_change_to_output(self):
        """Verify stats collection doesn't alter results."""
        index = 100

        # Resolve without stats
        result_no_stats = lulzprime.resolve(index)

        # Resolve with stats
        stats = ResolveStats()
        result_with_stats = resolve_internal_with_pi(index, pi, stats)

        # Results must be identical
        assert result_with_stats == result_no_stats == 541

    def test_stats_deterministic(self):
        """Verify stats are deterministic for same input."""
        index = 100

        # Run twice with stats
        stats1 = ResolveStats()
        result1 = resolve_internal_with_pi(index, pi, stats1)

        stats2 = ResolveStats()
        result2 = resolve_internal_with_pi(index, pi, stats2)

        # Results must match
        assert result1 == result2

        # Stats must match
        assert stats1.pi_calls == stats2.pi_calls
        assert stats1.binary_search_iterations == stats2.binary_search_iterations
        assert stats1.correction_backward_steps == stats2.correction_backward_steps
        assert stats1.correction_forward_steps == stats2.correction_forward_steps
        assert stats1.forecast_value == stats2.forecast_value
        assert stats1.final_result == stats2.final_result

    def test_stats_pi_calls_counted(self):
        """Verify π(x) calls are counted."""
        index = 50
        stats = ResolveStats()
        result = resolve_internal_with_pi(index, pi, stats)

        # Should have made some pi calls
        assert stats.pi_calls > 0
        # Binary search should have run
        assert stats.binary_search_iterations > 0
        # Result should be set
        assert stats.final_result == result

    def test_stats_to_dict(self):
        """Verify stats.to_dict() works."""
        index = 100
        stats = ResolveStats()
        resolve_internal_with_pi(index, pi, stats)

        stats_dict = stats.to_dict()

        assert "pi_calls" in stats_dict
        assert "binary_search_iterations" in stats_dict
        assert "correction_backward_steps" in stats_dict
        assert "correction_forward_steps" in stats_dict
        assert "forecast_value" in stats_dict
        assert "final_result" in stats_dict

        assert stats_dict["final_result"] == 541

    def test_stats_disabled_by_default(self):
        """Verify stats are disabled by default (None)."""
        # Should work fine without stats parameter
        index = 25
        result = resolve_internal_with_pi(index, pi)
        assert result == 97
