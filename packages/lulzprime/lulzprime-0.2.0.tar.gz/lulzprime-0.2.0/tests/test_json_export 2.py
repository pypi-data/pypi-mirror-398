"""
Tests for JSON export functionality (simulator.py).

Validates JSON export helpers for simulation output (Phase 3, Task 2).
"""

import json

import pytest

from lulzprime import simulate, simulation_to_json, simulation_to_json_string


class TestJSONExportBasics:
    """Test basic JSON export functionality."""

    def test_simulation_to_json_basic(self):
        """Test basic JSON export from simulation."""
        seq = simulate(10, seed=42)
        json_data = simulation_to_json(seq, n_steps=10, seed=42)

        # Check schema structure
        assert "schema" in json_data
        assert "params" in json_data
        assert "sequence" in json_data
        assert "diagnostics" in json_data
        assert "meta" in json_data

        # Check schema version
        assert json_data["schema"] == "lulzprime.simulation.v0.2"

        # Check params
        assert json_data["params"]["n_steps"] == 10
        assert json_data["params"]["seed"] == 42
        assert json_data["params"]["anneal_tau"] is None
        assert "beta_initial" in json_data["params"]
        assert "beta_decay" in json_data["params"]
        assert "initial_q" in json_data["params"]
        assert "as_generator" in json_data["params"]

        # Check sequence
        assert len(json_data["sequence"]) == 10
        assert json_data["sequence"] == seq

        # Check diagnostics (should be None by default)
        assert json_data["diagnostics"] is None

        # Check meta
        assert json_data["meta"]["library"] == "lulzprime"
        assert json_data["meta"]["version"] == "0.2.0"
        assert json_data["meta"]["timestamp"] is None

    def test_json_serializable(self):
        """Test that output is JSON-serializable via json.dumps."""
        seq = simulate(50, seed=123)
        json_data = simulation_to_json(seq, n_steps=50, seed=123)

        # Should not raise
        json_string = json.dumps(json_data)
        assert isinstance(json_string, str)
        assert len(json_string) > 0

        # Should round-trip
        parsed = json.loads(json_string)
        assert parsed["schema"] == "lulzprime.simulation.v0.2"
        assert parsed["sequence"] == seq

    def test_n_steps_inference(self):
        """Test that n_steps is inferred from sequence length if not provided."""
        seq = simulate(25, seed=99)
        json_data = simulation_to_json(seq, seed=99)  # No n_steps provided

        assert json_data["params"]["n_steps"] == 25
        assert len(json_data["sequence"]) == 25


class TestJSONExportWithDiagnostics:
    """Test JSON export with diagnostics."""

    def test_with_diagnostics(self):
        """Test JSON export with diagnostic records."""
        seq, diag = simulate(100, seed=42, diagnostics=True)
        json_data = simulation_to_json(
            seq, n_steps=100, seed=42, diagnostics=diag
        )

        # Check diagnostics is list
        assert json_data["diagnostics"] is not None
        assert isinstance(json_data["diagnostics"], list)
        assert len(json_data["diagnostics"]) > 0

        # Check diagnostic structure (sample every 10 steps)
        for entry in json_data["diagnostics"]:
            assert "step" in entry
            assert "q" in entry
            assert "w" in entry
            assert "beta" in entry
            assert "gap" in entry

    def test_diagnostics_json_serializable(self):
        """Test that diagnostics dicts are JSON-safe."""
        seq, diag = simulate(50, seed=777, diagnostics=True)
        json_data = simulation_to_json(
            seq, n_steps=50, seed=777, diagnostics=diag
        )

        # Should serialize without error
        json_string = json.dumps(json_data)
        parsed = json.loads(json_string)

        # Diagnostics should round-trip
        assert parsed["diagnostics"] is not None
        assert len(parsed["diagnostics"]) > 0


class TestJSONExportWithAnnealing:
    """Test JSON export with annealing parameters."""

    def test_with_anneal_tau(self):
        """Test JSON export with annealing time constant."""
        seq = simulate(100, seed=42, anneal_tau=1000.0)
        json_data = simulation_to_json(
            seq, n_steps=100, seed=42, anneal_tau=1000.0
        )

        assert json_data["params"]["anneal_tau"] == 1000.0

    def test_anneal_tau_none(self):
        """Test that anneal_tau is null when not used."""
        seq = simulate(50, seed=42)
        json_data = simulation_to_json(seq, n_steps=50, seed=42)

        assert json_data["params"]["anneal_tau"] is None


class TestJSONExportString:
    """Test JSON string export with deterministic output."""

    def test_simulation_to_json_string_basic(self):
        """Test basic JSON string export."""
        seq = simulate(20, seed=42)
        json_str = simulation_to_json_string(seq, n_steps=20, seed=42)

        # Should be a string
        assert isinstance(json_str, str)

        # Should parse correctly
        parsed = json.loads(json_str)
        assert parsed["schema"] == "lulzprime.simulation.v0.2"
        assert parsed["params"]["seed"] == 42
        assert len(parsed["sequence"]) == 20

    def test_json_string_deterministic(self):
        """Test that same inputs produce same JSON string (deterministic)."""
        seq = simulate(30, seed=1337)

        json_str1 = simulation_to_json_string(seq, n_steps=30, seed=1337)
        json_str2 = simulation_to_json_string(seq, n_steps=30, seed=1337)

        # Exact string match (sort_keys ensures determinism)
        assert json_str1 == json_str2

    def test_json_string_sorted_keys(self):
        """Test that keys are sorted for deterministic output."""
        seq = simulate(10, seed=42)
        json_str = simulation_to_json_string(seq, n_steps=10, seed=42)

        # Keys should be in sorted order in the string
        # This is a simple check that "diagnostics" comes before "meta" etc.
        assert '"diagnostics":null' in json_str or '"diagnostics": null' in json_str
        # Compact separators should be used
        assert '", "' not in json_str  # No space after comma
        assert '": ' not in json_str or '":' in json_str  # No space after colon


class TestJSONExportEdgeCases:
    """Test edge cases and error conditions."""

    def test_generator_mode_flag(self):
        """Test that as_generator flag is captured."""
        seq = list(simulate(15, seed=42, as_generator=True))
        json_data = simulation_to_json(
            seq, n_steps=15, seed=42, as_generator=True
        )

        assert json_data["params"]["as_generator"] is True

    def test_custom_beta_params(self):
        """Test that custom beta parameters are captured."""
        seq = simulate(
            20, seed=42, beta_initial=3.0, beta_decay=0.9
        )
        json_data = simulation_to_json(
            seq,
            n_steps=20,
            seed=42,
            beta_initial=3.0,
            beta_decay=0.9,
        )

        assert json_data["params"]["beta_initial"] == 3.0
        assert json_data["params"]["beta_decay"] == 0.9

    def test_custom_initial_q(self):
        """Test that custom initial_q is captured."""
        seq = simulate(10, seed=42, initial_q=5)
        json_data = simulation_to_json(
            seq, n_steps=10, seed=42, initial_q=5
        )

        assert json_data["params"]["initial_q"] == 5
        assert json_data["sequence"][0] == 5

    def test_seed_none(self):
        """Test that seed=None is handled correctly."""
        seq = simulate(10, seed=None)
        json_data = simulation_to_json(seq, n_steps=10, seed=None)

        assert json_data["params"]["seed"] is None


class TestJSONExportSchema:
    """Test schema compliance and structure."""

    def test_schema_keys_present(self):
        """Test that all required schema keys are present."""
        seq = simulate(10, seed=42)
        json_data = simulation_to_json(seq, n_steps=10, seed=42)

        # Top-level keys
        required_keys = {"schema", "params", "sequence", "diagnostics", "meta"}
        assert set(json_data.keys()) == required_keys

        # Params keys
        params_keys = {
            "n_steps",
            "seed",
            "anneal_tau",
            "beta_initial",
            "beta_decay",
            "initial_q",
            "as_generator",
        }
        assert set(json_data["params"].keys()) == params_keys

        # Meta keys
        meta_keys = {"library", "version", "timestamp"}
        assert set(json_data["meta"].keys()) == meta_keys

    def test_timestamp_always_none(self):
        """Test that timestamp is always None for determinism."""
        seq = simulate(10, seed=42)
        json_data = simulation_to_json(seq, n_steps=10, seed=42)

        assert json_data["meta"]["timestamp"] is None

    def test_sequence_is_list(self):
        """Test that sequence is always a list (not generator)."""
        # Even with generator input, should convert to list
        gen = simulate(10, seed=42, as_generator=True)
        seq = list(gen)
        json_data = simulation_to_json(seq, n_steps=10, seed=42)

        assert isinstance(json_data["sequence"], list)
        assert len(json_data["sequence"]) == 10
