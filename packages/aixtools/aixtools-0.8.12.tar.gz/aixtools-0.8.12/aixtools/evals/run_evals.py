"""
Evaluation execution functionality for LLM evaluations.

This module handles running evaluations and printing results.
"""

import sys

from pydantic_evals.reporting import EvaluationReport

from aixtools.evals.dataset import AixDataset  # pylint: disable=E0401


async def run_dataset_evaluation(
    dataset: AixDataset,
    print_options: dict[str, bool],
    min_assertions: float,
    verbose: bool = False,
) -> tuple[str, bool, EvaluationReport | None]:
    """Run evaluation for a single dataset and return (name, success, report)."""
    if verbose:
        print(f"\n{'=' * 60}")
        print(f"Running evaluation: {dataset.name}")
        print(f"{'=' * 60}")
    else:
        print(f"Running {dataset.name}...", end=" ")

    try:
        # Execute the evaluation
        report = await dataset.evaluate()

        # Print the results
        report.print(
            include_input=print_options["include_input"],
            include_output=print_options["include_output"],
            include_evaluator_failures=print_options["include_evaluator_failures"],
            include_reasons=print_options["include_reasons"],
        )

        success = all(scorer(report, dataset, min_assertions, verbose) for scorer in dataset.scorers)

        if print_options["include_evaluator_failures"] and success:
            has_evaluator_failures = any(
                result.evaluator_failures for result in report.cases if result.evaluator_failures
            )
            if has_evaluator_failures:
                success = False

        return dataset.name, success, report

    except Exception as e:  # pylint: disable=broad-exception-caught
        if verbose:
            print(f"Error running evaluation {dataset.name}: {e}")
        else:
            print(f"ERROR ({e})")
        return dataset.name, False, None


async def run_all_evaluations_and_print_results(
    datasets: list[AixDataset], print_options: dict[str, bool], min_assertions: float, verbose: bool
) -> None:
    """Run all evaluations and print results with summary."""
    # Run all evaluations
    results = []
    for dataset in datasets:
        result = await run_dataset_evaluation(dataset, print_options, min_assertions, verbose)
        results.append(result)

    # Print reports
    for _, _, report in results:
        if report:
            report.print(
                include_input=print_options["include_input"],
                include_output=print_options["include_output"],
                include_evaluator_failures=print_options["include_evaluator_failures"],
                include_reasons=print_options["include_reasons"],
            )

    # Print summary
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    failed_results = [(name, success, _) for name, success, _ in results if not success]

    if verbose:
        print(f"\n{'=' * 60}")
        print("EVALUATION SUMMARY")
        print(f"{'=' * 60}")

        for name, success, _ in results:
            status = "PASSED" if success else "FAILED"
            print(f"  {name}: {status}")

        print(f"\nTotal: {passed}/{total} evaluations passed")
    # Only show failed evaluations when not verbose
    elif failed_results:
        print("\nFailed evaluations:")
        for name, _, _ in failed_results:
            print(f"  {name}: FAILED")

    # Exit with non-zero code if any evaluations failed
    if passed < total:
        print(f"\n{total - passed} evaluation(s) failed")
        sys.exit(1)
    else:
        print("\nAll evaluations passed!")
