"""
Minimal command-line interface for lulzprime.

Provides basic CLI commands for common operations.
Part of Phase 3 (Usability) enhancements.

Usage:
    python -m lulzprime resolve <n>
    python -m lulzprime pi <x>
    python -m lulzprime simulate <n_steps> [--seed SEED] [--anneal-tau TAU] [--generator]
"""

import argparse
import sys
from typing import Any, cast


def cmd_resolve(args: argparse.Namespace) -> int:
    """Execute resolve command."""
    from . import resolve

    try:
        index = int(args.n)
        if index < 1:
            print(f"Error: index must be >= 1, got {index}", file=sys.stderr)
            return 1

        result = resolve(index)
        print(result)
        return 0

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_pi(args: argparse.Namespace) -> int:
    """Execute pi command."""
    from .pi import pi

    try:
        x = int(args.x)
        if x < 2:
            print(f"Error: x must be >= 2, got {x}", file=sys.stderr)
            return 1

        result = pi(x)
        print(result)
        return 0

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_simulate(args: argparse.Namespace) -> int:
    """Execute simulate command."""
    from . import simulate, simulation_to_json_string

    try:
        n_steps = int(args.n_steps)
        if n_steps <= 0:
            print(f"Error: n_steps must be > 0, got {n_steps}", file=sys.stderr)
            return 1

        # Build kwargs
        kwargs: dict[str, Any] = {}
        seed: int | None = None
        anneal_tau: float | None = None

        if args.seed is not None:
            seed = int(args.seed)
            kwargs["seed"] = seed
        if args.anneal_tau is not None:
            tau = float(args.anneal_tau)
            if tau <= 0:
                print(f"Error: anneal_tau must be > 0, got {tau}", file=sys.stderr)
                return 1
            anneal_tau = tau
            kwargs["anneal_tau"] = tau
        if args.generator:
            kwargs["as_generator"] = True

        # Execute
        result = simulate(n_steps, **kwargs)

        # JSON output mode
        if args.json_output:
            # Convert generator to list if needed
            if args.generator:
                result_list = cast(list[int], list(result))
            else:
                # Result is list[int] (no diagnostics in CLI mode)
                result_list = cast(list[int], result)

            # Build JSON
            json_str = simulation_to_json_string(
                result_list,
                n_steps=n_steps,
                seed=seed,
                anneal_tau=anneal_tau,
                as_generator=args.generator,
            )

            # Write to file
            with open(args.json_output, "w") as f:
                f.write(json_str)
                f.write("\n")  # Trailing newline

            print(
                f"Simulation results exported to {args.json_output}",
                file=sys.stderr,
            )
        else:
            # Text output (default)
            if args.generator:
                # Stream one value per line
                for value in result:
                    print(value)
            else:
                # List mode: output all values, one per line
                for value in result:
                    print(value)

        return 0

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="lulzprime",
        description="LULZprime - Prime resolution and OMPC simulation library",
        epilog="For more info: https://github.com/RobLe3/lulzprime",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # resolve command
    parser_resolve = subparsers.add_parser(
        "resolve", help="Compute the exact nth prime p_n"
    )
    parser_resolve.add_argument("n", type=str, help="Prime index (1-based)")

    # pi command
    parser_pi = subparsers.add_parser(
        "pi", help="Compute π(x) - the number of primes <= x"
    )
    parser_pi.add_argument("x", type=str, help="Upper bound")

    # simulate command
    parser_simulate = subparsers.add_parser(
        "simulate", help="Generate pseudo-primes using OMPC simulation"
    )
    parser_simulate.add_argument("n_steps", type=str, help="Number of steps to simulate")
    parser_simulate.add_argument(
        "--seed", type=str, default=None, help="Random seed for reproducibility"
    )
    parser_simulate.add_argument(
        "--anneal-tau",
        type=str,
        default=None,
        help="Annealing time constant (>0, optional)",
    )
    parser_simulate.add_argument(
        "--generator",
        action="store_true",
        help="Stream results (low memory mode)",
    )
    parser_simulate.add_argument(
        "--json",
        dest="json_output",
        type=str,
        default=None,
        help="Export results to JSON file",
    )

    args = parser.parse_args()

    # Dispatch
    if args.command == "resolve":
        return cmd_resolve(args)
    elif args.command == "pi":
        return cmd_pi(args)
    elif args.command == "simulate":
        return cmd_simulate(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
