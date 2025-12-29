# Copyright 2025 Tenro.ai
# SPDX-License-Identifier: Apache-2.0

"""Verification API for construct testing.

Provides clean, expressive verifications for testing agent behavior:
- construct.verify_tool("fetch_data", times=1)
- construct.verify_llm(provider="openai", times=2)
- construct.verify_agent("RiskAgent", threshold=0.8)
- construct.verify_llm(output_contains="success")
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from tenro.construct.verify.agent import AgentVerifications
from tenro.construct.verify.llm import LLMVerifications
from tenro.construct.verify.tool import ToolVerifications

if TYPE_CHECKING:
    from tenro.core.spans import AgentRun


class ConstructVerifications:
    """Verification API for testing agent behavior.

    Provides expressive verifications for tools, agents, and LLMs with support
    for count matching, argument checking, and sequence verification.
    """

    def __init__(
        self,
        agent_runs: list[AgentRun],
        llm_calls: list[Any] | None = None,
        tool_calls: list[Any] | None = None,
    ) -> None:
        """Initialize with hierarchical agent runs and optionally flat call lists.

        Args:
            agent_runs: List of agent runs (with populated .spans field).
            llm_calls: Optional pre-computed list of LLM calls (including orphans).
            tool_calls: Optional pre-computed list of tool calls (including orphans).
        """
        # Use provided lists or extract from agent runs
        if llm_calls is None:
            llm_calls = [llm for agent in agent_runs for llm in agent.get_llm_calls(recursive=True)]
        if tool_calls is None:
            tool_calls = [
                tool for agent in agent_runs for tool in agent.get_tool_calls(recursive=True)
            ]

        # Initialize specialized verification modules
        self._tool_verifications = ToolVerifications(tool_calls, agent_runs)
        self._agent_verifications = AgentVerifications(agent_runs)
        self._llm_verifications = LLMVerifications(llm_calls, agent_runs)

    def verify_tool(
        self,
        target: str,
        called_with: dict[str, Any] | None = None,
        *,
        times: int | None = None,
        output: Any = None,
        output_contains: str | None = None,
        output_exact: Any = None,
        call_index: int | None = 0,
        **kwargs: Any,
    ) -> None:
        """Verify tool was called with optional argument and output matching.

        Args:
            target: Name or path of the tool.
            called_with: Dict of expected arguments. Use when a key conflicts
                with a verification parameter like `times`.
            times: Expected number of calls (`None` = at least once).
            output: Expected output (dict=subset match, scalar=exact).
            output_contains: Expected substring in output.
            output_exact: Expected output (strict deep equality).
            call_index: Which call to check (0=first, -1=last, `None`=any).
            **kwargs: Expected keyword arguments.

        Raises:
            AssertionError: If verification fails.

        Examples:
            >>> construct.verify_tool("fetch_data")  # at least once
            >>> construct.verify_tool("fetch_data", times=1)  # exactly once
            >>> construct.verify_tool("get_weather", output={"temp": 72})  # subset
            >>> construct.verify_tool("search", output_contains="results")
        """
        self._tool_verifications.verify_tool(
            target,
            called_with,
            times=times,
            output=output,
            output_contains=output_contains,
            output_exact=output_exact,
            call_index=call_index,
            **kwargs,
        )

    def verify_tool_never(self, target: str) -> None:
        """Verify tool was never called.

        Args:
            target: Name or path of the tool.

        Raises:
            AssertionError: If tool was called.

        Examples:
            >>> construct.verify_tool_never("dangerous_operation")
        """
        self._tool_verifications.verify_tool_never(target)

    def verify_tool_sequence(self, expected_sequence: list[str]) -> None:
        """Verify tools were called in a specific order.

        Args:
            expected_sequence: Expected sequence of tool names.

        Raises:
            AssertionError: If sequence doesn't match.

        Examples:
            >>> construct.verify_tool_sequence(["search", "summarize", "format"])
        """
        self._tool_verifications.verify_tool_sequence(expected_sequence)

    def verify_tools(
        self,
        count: int | None = None,
        min: int | None = None,
        max: int | None = None,
        target: str | None = None,
    ) -> None:
        """Verify tool calls with optional count/range and name filter.

        Args:
            count: Expected exact number of calls (mutually exclusive with min/max).
            min: Minimum number of calls (inclusive).
            max: Maximum number of calls (inclusive).
            target: Optional tool name filter.

        Raises:
            AssertionError: If verification fails.
            ValueError: If count and min/max are both specified.

        Examples:
            >>> construct.verify_tools()  # at least one tool call
            >>> construct.verify_tools(count=3)  # exactly 3 tool calls
            >>> construct.verify_tools(min=2, max=4)  # between 2 and 4 calls
        """
        self._tool_verifications.verify_tools(count=count, min=min, max=max, target=target)

    def verify_agent(
        self,
        target: str,
        called_with: dict[str, Any] | None = None,
        *,
        times: int | None = None,
        **kwargs: Any,
    ) -> None:
        """Verify agent was called with optional argument matching.

        Args:
            target: Name of the agent.
            called_with: Dict of expected arguments. Use when a key conflicts with
                a verification parameter like "times".
            times: Expected number of calls (None = at least once).
            **kwargs: Expected keyword arguments.

        Raises:
            AssertionError: If verification fails.

        Examples:
            >>> construct.verify_agent("RiskAgent")  # at least once
            >>> construct.verify_agent("RiskAgent", times=1)  # exactly once
            >>> construct.verify_agent("RiskAgent", threshold=0.8)  # with threshold=0.8
        """
        self._agent_verifications.verify_agent(target, called_with, times=times, **kwargs)

    def verify_agent_never(self, target: str) -> None:
        """Verify agent was never called.

        Args:
            target: Name of the agent.

        Raises:
            AssertionError: If agent was called.

        Examples:
            >>> construct.verify_agent_never("DatabaseAgent")
        """
        self._agent_verifications.verify_agent_never(target)

    def verify_agent_sequence(self, expected_sequence: list[str]) -> None:
        """Verify agents were called in a specific order.

        Args:
            expected_sequence: Expected sequence of agent names.

        Raises:
            AssertionError: If sequence doesn't match.

        Examples:
            >>> construct.verify_agent_sequence(["Manager", "Researcher", "Writer"])
        """
        self._agent_verifications.verify_agent_sequence(expected_sequence)

    def verify_agents(
        self,
        count: int | None = None,
        min: int | None = None,
        max: int | None = None,
        target: str | None = None,
    ) -> None:
        """Verify agent calls with optional count/range and name filter.

        Args:
            count: Expected exact number of calls (mutually exclusive with min/max).
            min: Minimum number of calls (inclusive).
            max: Maximum number of calls (inclusive).
            target: Optional agent name filter.

        Raises:
            AssertionError: If verification fails.
            ValueError: If count and min/max are both specified.

        Examples:
            >>> construct.verify_agents()  # at least one agent call
            >>> construct.verify_agents(count=3)  # exactly 3 agent calls
            >>> construct.verify_agents(target="Manager")  # at least one Manager call
        """
        self._agent_verifications.verify_agents(count=count, min=min, max=max, target=target)

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
            target: Optional target filter.
            provider: Optional provider filter (e.g., `openai`).
            times: Expected number of calls (`None` = at least once).
            output: Expected output (dict=subset match, scalar=exact).
            output_contains: Expected substring in output.
            output_exact: Expected output (strict deep equality).
            where: Selector (`None`=response, `"json"`, `"model"`).
            call_index: Which call to check (0=first, -1=last, `None`=any).

        Raises:
            AssertionError: If verification fails.

        Examples:
            >>> construct.verify_llm()  # at least once
            >>> construct.verify_llm(provider="openai", times=1)
            >>> construct.verify_llm(output_contains="success")
            >>> construct.verify_llm(where="json", output={"temp": 72})
        """
        self._llm_verifications.verify_llm(
            target,
            provider,
            times=times,
            output=output,
            output_contains=output_contains,
            output_exact=output_exact,
            where=where,
            call_index=call_index,
        )

    def verify_llm_never(self, target: str | None = None, provider: str | None = None) -> None:
        """Verify LLM was never called.

        Args:
            target: Optional target filter (specific function like
                `openai.chat.completions.create`).
            provider: Optional provider filter (broad filter like `openai`
                for all OpenAI calls).

        Raises:
            AssertionError: If LLM was called.

        Examples:
            >>> construct.verify_llm_never()
            >>> construct.verify_llm_never(target="openai.chat.completions.create")
            >>> construct.verify_llm_never(provider="anthropic")
        """
        self._llm_verifications.verify_llm_never(target, provider)

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
            target: Optional target filter (specific function like
                `openai.chat.completions.create`).
            provider: Optional provider filter (broad filter like `openai`
                for all OpenAI calls).

        Raises:
            AssertionError: If verification fails.
            ValueError: If count and min/max are both specified.

        Examples:
            >>> construct.verify_llms()  # at least one LLM call
            >>> construct.verify_llms(count=2)  # exactly 2 LLM calls
            >>> construct.verify_llms(target="openai.chat.completions.create")  # specific function
            >>> construct.verify_llms(provider="openai")  # at least one OpenAI call
        """
        self._llm_verifications.verify_llms(
            count=count, min=min, max=max, target=target, provider=provider
        )


__all__ = ["ConstructVerifications"]
