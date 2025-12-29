# Copyright 2025 Tenro.ai
# SPDX-License-Identifier: Apache-2.0

"""LLM verification methods for construct testing.

Provides 3 core verification methods for LLM calls:
- verify_llm() - flexible verification with output checking and where selector
- verify_llm_never() - explicit "never called" check
- verify_llms() - aggregate/range queries
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from tenro.construct.verify.engine import verify_call_count
from tenro.construct.verify.output import (
    verify_output,
    verify_output_contains,
    verify_output_exact,
)

if TYPE_CHECKING:
    from tenro.core.spans import AgentRun, LLMCall


class _LLMValueWrapper:
    """Wrapper to make LLM values work with verify_output functions."""

    def __init__(self, value: Any) -> None:
        self.value = value


class LLMVerifications:
    """LLM verification methods."""

    def __init__(self, llm_calls: list[LLMCall], agent_runs: list[AgentRun]) -> None:
        """Initialize with LLM calls and agent runs."""
        self._llm_calls = llm_calls
        self._agent_runs = agent_runs

    def verify_llm(
        self,
        target: str | None = None,
        provider: str | None = None,
        *,
        times: int | None = None,
        output: Any = None,
        output_contains: str | None = None,
        output_exact: Any = None,
        where: str | None = None,
        call_index: int | None = None,
    ) -> None:
        """Verify LLM was called with optional output checking.

        Args:
            target: Optional target filter (e.g., `openai.chat.completions.create`).
            provider: Optional provider filter (e.g., `openai`).
            times: Expected number of calls (`None` = at least once).
            output: Expected output (dict=subset match, scalar=exact).
            output_contains: Expected substring in output (strings only).
            output_exact: Expected output (strict deep equality).
            where: Selector for which part to check:
                - `None` (default): response text
                - `"json"`: parse response as JSON
                - `"model"`: model name
            call_index: Which call to check (0=first, -1=last, None=any).

        Examples:
            >>> construct.verify_llm()  # at least once
            >>> construct.verify_llm(provider="openai", times=1)
            >>> construct.verify_llm(output_contains="success")
            >>> construct.verify_llm(where="json", output={"temp": 72})
            >>> construct.verify_llm(where="model", output="gpt-5")
        """
        if times == 0:
            self.verify_llm_never(target, provider)
            return

        # Filter by provider
        calls = self._llm_calls
        if provider:
            calls = [c for c in calls if c.provider == provider]

        # Output verification
        if output is not None or output_contains is not None or output_exact is not None:
            items = self._apply_where_selector(calls, where)

            if output is not None:
                verify_output(items, "value", output, "LLM", call_index=call_index)
            elif output_contains is not None:
                verify_output_contains(
                    items, "value", output_contains, "LLM", call_index=call_index
                )
            elif output_exact is not None:
                verify_output_exact(items, "value", output_exact, "LLM", call_index=call_index)
            return

        # Default: verify call count
        verify_call_count(
            calls=self._llm_calls,
            agent_runs=self._agent_runs,
            count=times,
            min=1 if times is None else None,
            max=None,
            name_filter=target,
            agent_filter=None,
            event_type="llm",
            provider_filter=provider,
        )

    def _apply_where_selector(
        self, calls: list[LLMCall], where: str | None
    ) -> list[_LLMValueWrapper]:
        """Apply where selector to extract values from LLM calls."""
        result = []
        for call in calls:
            if where is None:
                result.append(_LLMValueWrapper(call.response))
            elif where == "json":
                try:
                    parsed = json.loads(call.response or "{}")
                    result.append(_LLMValueWrapper(parsed))
                except json.JSONDecodeError:
                    result.append(_LLMValueWrapper(None))
            elif where == "model":
                result.append(_LLMValueWrapper(call.model))
            else:
                msg = f"Unknown where selector: {where!r}. "
                msg += "Supported: None, 'json', 'model'"
                raise ValueError(msg)
        return result

    def verify_llm_never(self, target: str | None = None, provider: str | None = None) -> None:
        """Verify LLM was never called.

        Args:
            target: Optional target filter (e.g., `"openai.chat.completions.create"`).
            provider: Optional provider filter (e.g., `"openai"`, `"anthropic"`).

        Raises:
            AssertionError: If LLM was called.

        Examples:
            >>> construct.verify_llm_never()  # no LLM calls at all
            >>> construct.verify_llm_never(provider="anthropic")  # no Anthropic calls
        """
        verify_call_count(
            calls=self._llm_calls,
            agent_runs=self._agent_runs,
            count=0,
            min=None,
            max=None,
            name_filter=target,
            agent_filter=None,
            event_type="llm",
            provider_filter=provider,
        )

    def verify_llms(
        self,
        count: int | None = None,
        min: int | None = None,
        max: int | None = None,
        target: str | None = None,
        provider: str | None = None,
    ) -> None:
        """Verify LLM calls with optional count/range and target/provider filter.

        Args:
            count: Expected exact number of calls (mutually exclusive with min/max).
            min: Minimum number of calls (inclusive).
            max: Maximum number of calls (inclusive).
            target: Optional target filter.
            provider: Optional provider filter (e.g., `"openai"`, `"anthropic"`).

        Raises:
            AssertionError: If verification fails.
            ValueError: If `count` and min/max are both specified.

        Examples:
            >>> construct.verify_llms()  # at least one LLM call
            >>> construct.verify_llms(count=2)  # exactly 2 LLM calls
            >>> construct.verify_llms(min=1, max=3, provider="openai")
        """
        verify_call_count(
            calls=self._llm_calls,
            agent_runs=self._agent_runs,
            count=count,
            min=min,
            max=max,
            name_filter=target,
            agent_filter=None,
            event_type="llm",
            provider_filter=provider,
        )


__all__ = ["LLMVerifications"]
