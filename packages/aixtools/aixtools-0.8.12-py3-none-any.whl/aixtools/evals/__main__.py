#!/usr/bin/env python3
"""
Script to run all LLM evaluations.

This script discovers and runs all Dataset objects from eval_*.py files in the evals directory.
Similar to test runners but for LLM evaluations using pydantic_evals.
"""

import argparse
import asyncio
import sys
from pathlib import Path

from aixtools.evals.discovery import discover_all_datasets, find_eval_files  # pylint: disable=E0401
from aixtools.evals.run_evals import run_all_evaluations_and_print_results  # pylint: disable=E0401


async def main():
    """Main function to discover and run all evaluations."""
    parser = argparse.ArgumentParser(description="Run LLM evaluations")
    parser.add_argument(
        "--evals-dir", type=Path, default=Path("evals"), help="Directory containing eval_*.py files (default: evals)"
    )
    parser.add_argument(
        "--filter", type=str, help="Filter to run only matching evaluations (matches module, file, or dataset names)"
    )
    parser.add_argument("--include-input", action="store_true", default=True, help="Include input in report output")
    parser.add_argument("--include-output", action="store_true", default=True, help="Include output in report output")
    parser.add_argument(
        "--include-evaluator-failures", action="store_true", help="Include evaluator failures in report output"
    )
    parser.add_argument("--include-reasons", action="store_true", help="Include reasons in report output")
    parser.add_argument(
        "--min-assertions",
        type=float,
        default=1.0,
        help="Minimum assertions average required for success (default: 1.0)",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Print detailed information about discovery and processing"
    )

    args = parser.parse_args()

    # Prepare print options
    print_options = {
        "include_input": args.include_input,
        "include_output": args.include_output,
        "include_evaluator_failures": args.include_evaluator_failures,
        "include_reasons": args.include_reasons,
    }

    # Find all eval files
    eval_files = find_eval_files(args.evals_dir)
    if args.verbose:
        print(f"Scanning directory: {args.evals_dir}")
        print(f"Found {len(eval_files)} eval files:")
        for f in eval_files:
            print(f"  - {f}")

    # Discover all datasets
    all_datasets = discover_all_datasets(eval_files, args.filter, args.verbose)

    if args.filter and not args.verbose:
        print(f"Filter applied: {args.filter}")

    # Run all evaluations and print results
    await run_all_evaluations_and_print_results(all_datasets, print_options, args.min_assertions, args.verbose)


if __name__ == "__main__":
    # Add the current directory to Python path so we can import modules
    sys.path.insert(0, str(Path.cwd()))
    asyncio.run(main())
