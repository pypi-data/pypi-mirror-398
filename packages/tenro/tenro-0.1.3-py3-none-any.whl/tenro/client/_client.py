# Copyright 2025 Tenro.ai
# SPDX-License-Identifier: Apache-2.0

"""Tenro client for local agent testing and evaluation."""

from __future__ import annotations

import json
from typing import Any

from tenro.client.prompt import PromptObject
from tenro.core.eval_types import EvalResult


def _print_log_run_data(
    test_case: dict[str, Any],
    prompt_used: PromptObject,
    output: str,
    eval_results: list[EvalResult],
    env: str,
) -> None:
    """Print formatted test run data to console as JSON."""
    log_data = _build_log_data_dict(test_case, prompt_used, output, eval_results, env)

    print("\n" + "=" * 80)
    print("Tenro log_run() - Structured Data")
    print("=" * 80)
    print(json.dumps(log_data, indent=2, default=str))
    print("=" * 80 + "\n")


def _build_log_data_dict(
    test_case: dict[str, Any],
    prompt_used: PromptObject,
    output: str,
    eval_results: list[EvalResult],
    env: str,
) -> dict[str, Any]:
    """Build structured dictionary from log_run data."""
    metadata = {k: v for k, v in test_case.items() if k not in ("input", "expected")}
    evals_data = [
        {
            "score": result.score,
            "passed": result.passed,
            "details": result.details if result.details else {},
        }
        for result in eval_results
    ]

    return {
        "test_case": {
            "input": test_case.get("input", ""),
            "expected": test_case.get("expected", ""),
            "metadata": metadata if metadata else {},
        },
        "prompt": {
            "name": prompt_used.name,
            "version": prompt_used.version,
            "text": prompt_used.text,
            "metadata": prompt_used.metadata if prompt_used.metadata else {},
        },
        "output": output,
        "eval_results": evals_data,
        "env": env,
    }


class Tenro:
    """Main client class for local agent testing."""

    def __init__(self) -> None:
        """Initialize client instance."""
        self._shutdown_called = False

    def log_run(
        self,
        test_case: dict[str, Any],
        prompt_used: PromptObject,
        output: str,
        eval_results: list[EvalResult],
        env: str = "default",
    ) -> None:
        """Log test run to console.

        Prints test context including inputs, outputs, evaluations, and
        metadata for local debugging and analysis.

        Args:
            test_case: Test case with "input", "expected", and optional metadata.
            prompt_used: PromptObject used to generate the output.
            output: The agent's actual output.
            eval_results: List of EvalResult objects from evaluators.
            env: Environment identifier (e.g., "dev", "ci"). Defaults to "default".

        Examples:
            >>> import tenro.evals
            >>> eval1 = tenro.evals.exact_match(output, test_case["expected"])
            >>> client.log_run(
            ...     test_case=test_case,
            ...     prompt_used=prompt,
            ...     output=output,
            ...     eval_results=[eval1],
            ...     env="dev"
            ... )
            >>> assert eval1.passed
        """
        _print_log_run_data(test_case, prompt_used, output, eval_results, env)

    def shutdown(self) -> None:
        """Shutdown the client and release resources.

        Called automatically when using the client as a context manager.
        """
        self._shutdown_called = True

    def __enter__(self) -> Tenro:
        """Context manager entry."""
        return self

    def __exit__(self, *_exc_info: Any) -> None:
        """Context manager exit."""
        self.shutdown()
