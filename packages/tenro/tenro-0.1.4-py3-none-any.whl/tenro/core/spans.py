# Copyright 2025 Tenro.ai
# SPDX-License-Identifier: Apache-2.0

"""Span models for tracking LLM calls, tool calls, and agent runs.

These objects track lifecycle during test execution. They start in
"running" state and are updated in-place as operations complete.

User-facing types:
- LLMCall
- ToolCall
- AgentRun

Internal types:
- LLMScope (transparent annotation span for @link_llm decorator)
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from tenro.core.model_base import BaseModel


class BaseSpan(BaseModel):
    """Base class for all span types (LLMCall, ToolCall, AgentRun).

    Defines shared fields for timed operations in a trace. Spans share the
    same lifecycle: running -> completed/error.

    Attributes:
        id: Unique span identifier.
        trace_id: Trace identifier for the overall workflow.
        start_time: Unix timestamp when the span started.
        parent_span_id: Immediate parent span ID (Agent, LLM, or Tool).
        agent_id: Closest agent ancestor span ID, if any.
        status: Lifecycle status (`running`, `completed`, or `error`).
        latency_ms: Span duration in milliseconds.
        error: Error message if the span failed.
        metadata: Additional metadata for the span.
    """

    id: str
    trace_id: str
    start_time: float

    parent_span_id: str | None = None
    agent_id: str | None = None
    status: Literal["running", "completed", "error"] = "running"
    latency_ms: float = 0.0
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class LLMCall(BaseSpan):
    """Mutable object representing an LLM API call lifecycle.

    Created when LLM call starts, updated in-place as it progresses.
    Users can access response, latency, and status at any time.

    Attributes:
        provider: LLM provider name (e.g., `openai`, `anthropic`).
        messages: List of message dicts sent to the provider.
        response: Model response text, when available.
        model: Model identifier used for the call.
        token_usage: Token usage metadata when available.
        caller_signature: Caller function signature for error messages.
        caller_location: Caller file location for error messages.
        agent_name: Name of the @link_agent-decorated agent that made this call,
            or None if called outside of an agent context.
        llm_scope_id: ID of enclosing LLMScope from @link_llm decorator, if any.
    """

    provider: str
    messages: list[dict[str, Any]]

    response: str | None = None
    model: str | None = None
    token_usage: dict[str, int] | None = None

    caller_signature: str | None = None
    caller_location: str | None = None
    agent_name: str | None = None
    llm_scope_id: str | None = None


class LLMScope(BaseSpan):
    """Transparent annotation span created by @link_llm decorator.

    LLMScope marks a code boundary where LLM calls happen. It is transparent
    for parent attribution - LLMCalls reference it via llm_scope_id for
    grouping but get their parent_span_id from structural spans (Agent/Tool).

    Internal type - not exposed to users in get_llm_calls() or verify_llm().

    Attributes:
        provider: Provider specified in the decorator.
        model: Model specified in the decorator, if any.
        caller_signature: Function signature where decorator was applied.
        caller_location: File:line location of the decorated function.
    """

    provider: str
    model: str | None = None
    caller_signature: str | None = None
    caller_location: str | None = None


class ToolCall(BaseSpan):
    """Mutable object representing a tool call lifecycle.

    Created when tool is invoked, updated in-place when completed.
    Tracks arguments, results, timing, and errors.

    Attributes:
        tool_name: Name of the tool being called.
        args: Positional arguments passed to the tool.
        kwargs: Keyword arguments passed to the tool.
        result: Tool result payload, if any.
    """

    tool_name: str
    args: tuple[Any, ...] = Field(default_factory=tuple)
    kwargs: dict[str, Any] = Field(default_factory=dict)
    result: Any = None


class AgentRun(BaseSpan):
    """Mutable object representing an agent execution lifecycle.

    Created when agent starts, updated in-place when completed.
    Represents the top-level span for agent operations, with child
    spans for LLM calls and tool calls.

    The agent's human-readable name is stored in the `name` field.
    The `id` field is a unique span identifier for this specific run.
    The `agent_id` field equals `id` (an agent belongs to itself).

    Used for:
    - Multi-agent hierarchies (Manager -> Researcher -> Writer)
    - Recursive agent composition (Agent calls Agent)
    - Stack-based trace propagation across async boundaries

    Attributes:
        name: Human-readable agent name.
        parent_agent_id: Parent agent span identifier, if any.
        spans: Child spans collected under this agent.
        input_data: Input payload for the agent, if provided.
        output_data: Output payload from the agent, if available.
        kwargs: Keyword arguments passed to the agent.
    """

    name: str
    parent_agent_id: str | None = None
    spans: list[BaseSpan] = Field(default_factory=list)
    input_data: Any = None
    output_data: Any = None
    kwargs: dict[str, Any] = Field(default_factory=dict)

    def get_llm_calls(self, recursive: bool = True) -> list[LLMCall]:
        """Get all LLM calls in this agent's execution.

        Args:
            recursive: Include LLM calls from nested agents.

        Returns:
            List of LLM calls.
        """
        llm_calls = [s for s in self.spans if isinstance(s, LLMCall)]

        if recursive:
            for child in self.spans:
                if isinstance(child, AgentRun):
                    llm_calls.extend(child.get_llm_calls(recursive=True))

        return llm_calls

    def get_tool_calls(self, recursive: bool = True) -> list[ToolCall]:
        """Get all tool calls in this agent's execution.

        Args:
            recursive: Include tool calls from nested agents.

        Returns:
            List of tool calls.
        """
        tool_calls = [s for s in self.spans if isinstance(s, ToolCall)]

        if recursive:
            for child in self.spans:
                if isinstance(child, AgentRun):
                    tool_calls.extend(child.get_tool_calls(recursive=True))

        return tool_calls

    def get_child_agents(self, recursive: bool = True) -> list[AgentRun]:
        """Get all nested agents in this agent's execution.

        Args:
            recursive: Include deeply nested agents.

        Returns:
            List of child agent runs.
        """
        child_agents = [s for s in self.spans if isinstance(s, AgentRun)]

        if recursive:
            for child in child_agents[:]:  # Copy to avoid mutation during iteration
                child_agents.extend(child.get_child_agents(recursive=True))

        return child_agents
