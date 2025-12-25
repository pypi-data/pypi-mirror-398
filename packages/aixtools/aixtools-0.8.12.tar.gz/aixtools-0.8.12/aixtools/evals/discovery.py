"""
Dataset discovery functionality for LLM evaluations.

This module handles discovering and loading Dataset objects from eval_*.py files.
"""

import importlib.util
import inspect
import sys
import traceback
from pathlib import Path
from typing import Any, TypeVar

from pydantic_evals.dataset import Dataset

from aixtools.evals.dataset import AixDataset  # pylint: disable=E0401

SpecialFuncT = TypeVar("SpecialFuncT")


def find_eval_files(evals_dir: Path) -> list[Path]:
    """Find all eval_*.py files in the evals directory."""
    if not evals_dir.exists():
        print(f"Error: Evals directory '{evals_dir}' does not exist")
        sys.exit(1)

    eval_files = list(evals_dir.glob("eval_*.py"))
    if not eval_files:
        print(f"No eval_*.py files found in '{evals_dir}'")
        sys.exit(1)

    return eval_files


def find_datasets_in_module(module: Any) -> list[tuple[str, Dataset]]:
    """Find all Dataset objects with names matching dataset_* in a module."""
    datasets = []

    for name, obj in inspect.getmembers(module):
        if name.startswith("dataset_") and isinstance(obj, (Dataset, AixDataset)):
            datasets.append((name, obj))

    return datasets


def load_module_from_file(file_path: Path) -> Any:
    """Load a Python module from a file path."""
    module_name = file_path.stem
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {file_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def matches_filter(module_name: str, file_name: str, dataset_name: str, name_filter: str | None) -> bool:
    """Check if the dataset matches the name filter."""
    if name_filter is None:
        return True

    # Check if filter matches any of: module name, file name, dataset name, or full qualified name
    full_name = f"{module_name}.{dataset_name}"
    return (
        name_filter in module_name
        or name_filter in file_name
        or name_filter in dataset_name
        or name_filter in full_name
    )


def find_prefixed_functions(module: Any, prefix: str) -> list[Any]:
    """Find all functions with a specific prefix (name-based discovery only)."""
    funcs = []
    for name, obj in inspect.getmembers(module):
        if name.startswith(prefix) and (inspect.isfunction(obj) or inspect.iscoroutinefunction(obj)):
            funcs.append(obj)  # Return function directly, no decorator wrapping

    return funcs


def print_v(message: str, verbose: bool) -> None:
    """Print message if verbose is enabled."""
    if verbose:
        print(message)


def process_datasets_from_module(
    module: Any, eval_file: Path, name_filter: str | None, verbose: bool
) -> list[AixDataset]:
    """Process all datasets from a single module and return valid dataset tuples."""
    datasets = find_datasets_in_module(module)

    print_v(f"  Found {len(datasets)} datasets: {[name for name, _ in datasets]}", verbose)

    valid_datasets = []

    targets = find_prefixed_functions(module, "target_")
    scorers = find_prefixed_functions(module, "scorer_")
    evaluators = find_prefixed_functions(module, "evaluator_")

    print_v(f"  Found target functions: {[f.__name__ for f in targets]}", verbose)
    print_v(f"  Found scoring functions: {[f.__name__ for f in scorers]}", verbose)
    print_v(f"  Found evaluator functions: {[f.__name__ for f in evaluators]}", verbose)

    for dataset_name, dataset in datasets:
        full_name = f"{eval_file.stem}.{dataset_name}"

        if not matches_filter(module.__name__, eval_file.stem, dataset_name, name_filter):
            print_v(f"    ✗ Skipping dataset: {dataset_name} (doesn't match filter: {name_filter})", verbose)
            continue

        print_v(f"    ✓ Including dataset: {dataset_name}", verbose)

        if isinstance(dataset, Dataset):
            # Wrap in AixDataset if not already

            if len(targets) != 1:
                print_v(
                    f"    ✗ Skipping dataset: {dataset_name} (has {len(targets)} target functions, expected exactly 1)",
                    verbose,
                )

                continue

            dataset = AixDataset(  # noqa: PLW2901
                cases=dataset.cases,
                evaluators=dataset.evaluators,  # evaluators are plain functions now
                name=full_name,
                target_func=targets[0],  # target function is used directly
                scoring_funcs=scorers,  # scorers are plain functions now
            )

            valid_datasets.append(dataset)

    return valid_datasets


def discover_all_datasets(eval_files: list[Path], name_filter: str | None, verbose: bool) -> list[AixDataset]:
    """Discover all datasets from eval files."""
    all_datasets = []

    for eval_file in eval_files:
        if verbose:
            print(f"\nProcessing file: {eval_file}")

        try:
            module = load_module_from_file(eval_file)
            if verbose:
                print(f"  Loaded module: {module.__name__}")

            datasets = process_datasets_from_module(module, eval_file, name_filter, verbose)
            all_datasets.extend(datasets)

        except Exception as e:  # pylint: disable=broad-exception-caught
            if verbose:
                print(f"Error loading {eval_file}: {e}")
                print(f"  Traceback: {traceback.format_exc()}")
            continue

    # Check if any datasets were found
    if not all_datasets:
        print("No datasets found to evaluate")
        if verbose:
            print("This could be because:")
            print("  - No eval_*.py files contain dataset_* objects")
            print("  - The filter excluded all datasets")
            print("  - There were errors loading the modules")
        sys.exit(1)

    # Print summary of discovered datasets
    if verbose:
        print(f"\n{'=' * 60}")
        print("Datasets to Evaluate:")
        print(f"{'=' * 60}")
        for i, (dataset) in enumerate(all_datasets, 1):
            print(f"{i}. {dataset.name}")
            print(f"   Target function: {dataset.target_func.__name__}")
            print(f"   Cases: {len(dataset.cases)}")
            print(f"   Evaluators: {len(dataset.evaluators)}")
        print(f"{'=' * 60}")
    else:
        print(f"Found {len(all_datasets)} datasets to evaluate")

    return all_datasets
