"""Custom dataset and evaluation utilities for AixTools.

This module provides wrapper classes and decorators for building and running
evaluations using the pydantic-evals framework. It includes a custom Dataset
class, decorators for marking target functions, scorers, and evaluators, and
a default scoring function based on assertion averages.
"""

from typing import Awaitable, Callable, Generic

from pydantic import BaseModel
from pydantic_evals.dataset import Case, Dataset, InputsT, MetadataT, OutputT
from pydantic_evals.evaluators import Evaluator
from pydantic_evals.reporting import EvaluationReport

TargetT = Callable[[InputsT], Awaitable[OutputT]] | Callable[[InputsT], OutputT]
ScorerT = Callable[[EvaluationReport, "AixDataset", float, bool], bool]


class AixDataset(BaseModel, Generic[InputsT, OutputT, MetadataT]):
    """Custom Dataset class for AixTools evaluations."""

    dataset: Dataset[InputsT, OutputT]
    name: str
    target_func: TargetT
    scorers: list[ScorerT]

    def __init__(  # pylint: disable=R0913,R0917
        self,
        cases: list[Case[InputsT, OutputT]],
        target_func: TargetT,
        evaluators: list[Evaluator[InputsT, OutputT, MetadataT]] | None = None,
        name: str | None = None,
        scoring_funcs: list[ScorerT] | None = None,
    ):
        super().__init__(
            dataset=Dataset(cases=cases, evaluators=evaluators or []),
            target_func=target_func,
            name=name or "dataset",
            scorers=scoring_funcs or [average_assertions],
        )

    @property
    def cases(self) -> list[Case[InputsT, OutputT]]:
        """Return the list of cases in the dataset."""
        return self.dataset.cases

    @property
    def evaluators(self) -> list[Evaluator[InputsT, OutputT, MetadataT]]:
        """Return the list of evaluators in the dataset."""
        return self.dataset.evaluators

    async def evaluate(
        self,
    ) -> EvaluationReport:
        """Run the evaluation using the target function and return an EvaluationReport."""
        return await self.dataset.evaluate(self.target_func)


# Decorators removed - using name-based discovery only for simplicity and async compatibility
# Functions should be named with prefixes: target_, scorer_, evaluator_


def average_assertions(
    report: EvaluationReport, dataset: "AixDataset", min_score: float = 1.0, verbose: bool = False
) -> bool:
    """Scoring function that checks if the average assertions meet a minimum threshold."""
    averages = report.averages()
    if averages and averages.assertions is not None:
        success = averages.assertions >= min_score
        if verbose:
            print(f"\nAssertions Summary for {dataset.name}:")
            print(f"  Assertions Average: {averages.assertions:.3f}")
            print(f"  Minimum Required: {min_score:.3f}")
            print(f"  Status: {'PASSED' if success else 'FAILED'}")
        else:
            print(f"{'PASSED' if success else 'FAILED'} ({averages.assertions:.3f})")
    else:
        success = False
        if verbose:
            print(f"\nAssertions Summary for {dataset.name}:")
            print("  No assertions found or evaluation failed")
            print(f"  Minimum Required: {min_score:.3f}")
            print("  Status: FAILED")
        else:
            print("FAILED (no assertions)")
    return success
