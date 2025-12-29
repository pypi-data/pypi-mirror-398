# Copyright 2025 Tenro.ai
# SPDX-License-Identifier: Apache-2.0

"""Helper functions for simulation logic shared across tools/LLMs/agents.

Shared helpers to keep simulation logic consistent across tools, LLMs, and agents.
"""

from __future__ import annotations

from typing import Any


def validate_simulation_params(result: Any, results: list[Any] | None, side_effect: Any) -> None:
    """Validate that only one simulation parameter is provided.

    Args:
        result: Single result value.
        results: List of result values.
        side_effect: Callable for dynamic behavior.

    Raises:
        ValueError: If more than one parameter is provided.
    """
    param_count = sum([result is not None, results is not None, side_effect is not None])
    if param_count > 1:
        raise ValueError("Only one of 'result', 'results', or 'side_effect' can be provided")


def normalize_result_sequence(result: Any, results: list[Any] | None) -> list[Any] | None:
    """Normalize result/results parameters to a single sequence.

    Args:
        result: Single result value.
        results: List of result values.

    Returns:
        Normalized list of results, or `None` if neither provided.
    """
    if result is not None:
        return [result]
    elif results is not None:
        return results.copy()  # Copy to avoid mutating user's list
    else:
        return None


def execute_simulation_logic(
    side_effect: Any,
    result_sequence: list[Any] | None,
    error_context: str,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any:
    """Execute simulation logic: side_effect, result_sequence, or None.

    Args:
        side_effect: Callable for dynamic behavior.
        result_sequence: List of sequential results (modified in-place via pop).
        error_context: Context string for error messages (e.g., tool/agent path).
        args: Positional arguments to pass to side_effect.
        kwargs: Keyword arguments to pass to side_effect.

    Returns:
        Simulated result value.

    Raises:
        RuntimeError: If result sequence is exhausted.
        Exception: Any exception from side_effect or result_sequence.
    """
    if side_effect is not None:
        return side_effect(*args, **kwargs)

    elif result_sequence is not None:
        if not result_sequence:
            error_msg = f"Simulation sequence exhausted for {error_context}"
            raise RuntimeError(error_msg)

        value = result_sequence.pop(0)
        if isinstance(value, Exception):
            raise value
        if isinstance(value, type) and issubclass(value, BaseException):
            raise value()

        return value

    else:
        return None


def get_response_by_index(
    response_sequence: list[Any],
    index: int,
    error_context: str,
) -> Any:
    """Get response from sequence by index (for repeatable LLM calls).

    Args:
        response_sequence: List of responses.
        index: Current call index.
        error_context: Context string for error messages (e.g., LLM path).

    Returns:
        Response value at index.

    Raises:
        RuntimeError: If index exceeds sequence length.
        Exception: Any exception from response_sequence.
    """
    if index < len(response_sequence):
        response_content = response_sequence[index]
    else:
        error_msg = f"Simulation sequence exhausted for {error_context}"
        raise RuntimeError(error_msg)

    if isinstance(response_content, Exception):
        raise response_content
    if isinstance(response_content, type) and issubclass(response_content, BaseException):
        raise response_content()

    return response_content
