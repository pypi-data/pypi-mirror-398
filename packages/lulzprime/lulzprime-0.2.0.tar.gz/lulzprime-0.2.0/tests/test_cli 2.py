"""
Tests for CLI interface (cli.py).

Validates argument parsing and command execution (Phase 3, Task 1).
"""

import subprocess
import sys

import pytest


class TestCLIBasics:
    """Test basic CLI functionality and argument parsing."""

    def test_cli_help(self):
        """Test that --help works and shows commands."""
        result = subprocess.run(
            [sys.executable, "-m", "lulzprime", "--help"],
            capture_output=True,
            text=True,
            cwd=".",
            env={"PYTHONPATH": "src"},
        )

        assert result.returncode == 0
        assert "resolve" in result.stdout
        assert "pi" in result.stdout
        assert "simulate" in result.stdout

    def test_cli_no_command(self):
        """Test that CLI with no command shows help."""
        result = subprocess.run(
            [sys.executable, "-m", "lulzprime"],
            capture_output=True,
            text=True,
            cwd=".",
            env={"PYTHONPATH": "src"},
        )

        # Should show help or error
        assert "resolve" in result.stdout or "resolve" in result.stderr


class TestResolveCommand:
    """Test resolve command."""

    def test_resolve_basic(self):
        """Test basic resolve command."""
        result = subprocess.run(
            [sys.executable, "-m", "lulzprime", "resolve", "10"],
            capture_output=True,
            text=True,
            cwd=".",
            env={"PYTHONPATH": "src"},
        )

        assert result.returncode == 0
        assert result.stdout.strip() == "29"  # p_10 = 29

    def test_resolve_first_prime(self):
        """Test resolve for first prime."""
        result = subprocess.run(
            [sys.executable, "-m", "lulzprime", "resolve", "1"],
            capture_output=True,
            text=True,
            cwd=".",
            env={"PYTHONPATH": "src"},
        )

        assert result.returncode == 0
        assert result.stdout.strip() == "2"  # p_1 = 2

    def test_resolve_invalid_index_zero(self):
        """Test that resolve rejects index=0."""
        result = subprocess.run(
            [sys.executable, "-m", "lulzprime", "resolve", "0"],
            capture_output=True,
            text=True,
            cwd=".",
            env={"PYTHONPATH": "src"},
        )

        assert result.returncode != 0
        assert "Error" in result.stderr

    def test_resolve_invalid_index_negative(self):
        """Test that resolve rejects negative index."""
        result = subprocess.run(
            [sys.executable, "-m", "lulzprime", "resolve", "-5"],
            capture_output=True,
            text=True,
            cwd=".",
            env={"PYTHONPATH": "src"},
        )

        assert result.returncode != 0


class TestPiCommand:
    """Test pi command."""

    def test_pi_basic(self):
        """Test basic pi command."""
        result = subprocess.run(
            [sys.executable, "-m", "lulzprime", "pi", "100"],
            capture_output=True,
            text=True,
            cwd=".",
            env={"PYTHONPATH": "src"},
        )

        assert result.returncode == 0
        assert result.stdout.strip() == "25"  # π(100) = 25

    def test_pi_small_value(self):
        """Test pi for small value."""
        result = subprocess.run(
            [sys.executable, "-m", "lulzprime", "pi", "10"],
            capture_output=True,
            text=True,
            cwd=".",
            env={"PYTHONPATH": "src"},
        )

        assert result.returncode == 0
        assert result.stdout.strip() == "4"  # π(10) = 4 (2, 3, 5, 7)

    def test_pi_invalid_value(self):
        """Test that pi rejects x < 2."""
        result = subprocess.run(
            [sys.executable, "-m", "lulzprime", "pi", "1"],
            capture_output=True,
            text=True,
            cwd=".",
            env={"PYTHONPATH": "src"},
        )

        assert result.returncode != 0
        assert "Error" in result.stderr


class TestSimulateCommand:
    """Test simulate command."""

    def test_simulate_basic(self):
        """Test basic simulate command."""
        result = subprocess.run(
            [sys.executable, "-m", "lulzprime", "simulate", "5", "--seed", "42"],
            capture_output=True,
            text=True,
            cwd=".",
            env={"PYTHONPATH": "src"},
        )

        assert result.returncode == 0
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 5
        # All should be integers
        for line in lines:
            int(line)  # Should not raise

    def test_simulate_determinism(self):
        """Test that simulate with same seed is deterministic."""
        result1 = subprocess.run(
            [sys.executable, "-m", "lulzprime", "simulate", "10", "--seed", "1337"],
            capture_output=True,
            text=True,
            cwd=".",
            env={"PYTHONPATH": "src"},
        )

        result2 = subprocess.run(
            [sys.executable, "-m", "lulzprime", "simulate", "10", "--seed", "1337"],
            capture_output=True,
            text=True,
            cwd=".",
            env={"PYTHONPATH": "src"},
        )

        assert result1.returncode == 0
        assert result2.returncode == 0
        assert result1.stdout == result2.stdout

    def test_simulate_with_generator(self):
        """Test simulate with --generator flag."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "lulzprime",
                "simulate",
                "5",
                "--seed",
                "42",
                "--generator",
            ],
            capture_output=True,
            text=True,
            cwd=".",
            env={"PYTHONPATH": "src"},
        )

        assert result.returncode == 0
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 5

    def test_simulate_with_anneal_tau(self):
        """Test simulate with --anneal-tau parameter."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "lulzprime",
                "simulate",
                "5",
                "--seed",
                "42",
                "--anneal-tau",
                "1000",
            ],
            capture_output=True,
            text=True,
            cwd=".",
            env={"PYTHONPATH": "src"},
        )

        assert result.returncode == 0
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 5

    def test_simulate_invalid_n_steps(self):
        """Test that simulate rejects n_steps <= 0."""
        result = subprocess.run(
            [sys.executable, "-m", "lulzprime", "simulate", "0"],
            capture_output=True,
            text=True,
            cwd=".",
            env={"PYTHONPATH": "src"},
        )

        assert result.returncode != 0
        assert "Error" in result.stderr

    def test_simulate_invalid_anneal_tau(self):
        """Test that simulate rejects invalid anneal_tau."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "lulzprime",
                "simulate",
                "5",
                "--anneal-tau",
                "-100",
            ],
            capture_output=True,
            text=True,
            cwd=".",
            env={"PYTHONPATH": "src"},
        )

        assert result.returncode != 0
        assert "Error" in result.stderr

    def test_simulate_json_export(self):
        """Test simulate with JSON export."""
        import json
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            json_file = os.path.join(tmpdir, "output.json")
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "lulzprime",
                    "simulate",
                    "10",
                    "--seed",
                    "42",
                    "--json",
                    json_file,
                ],
                capture_output=True,
                text=True,
                cwd=".",
                env={"PYTHONPATH": "src"},
            )

            assert result.returncode == 0
            assert os.path.exists(json_file)

            # Verify JSON content
            with open(json_file) as f:
                data = json.load(f)

            assert data["schema"] == "lulzprime.simulation.v0.2"
            assert data["params"]["n_steps"] == 10
            assert data["params"]["seed"] == 42
            assert len(data["sequence"]) == 10
