# Copyright 2025 Tenro.ai
# SPDX-License-Identifier: Apache-2.0

"""Trace renderer for console output.

Main TraceRenderer class that coordinates extraction and formatting
to produce trace visualization output.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from tenro.debug.icons import (
    ARROW_IN,
    ARROW_OUT,
    BRANCH,
    LAST,
    SPACE,
    VERTICAL,
    get_span_icon,
)

if TYPE_CHECKING:
    from tenro.core.spans import AgentRun, BaseSpan
    from tenro.debug.config import TraceConfig


class TraceRenderer:
    """Renders trace visualization to console.

    Coordinates extraction of span data and Rich formatting to produce
    a timeline view of the trace.

    Example:
        >>> from tenro.debug import TraceRenderer
        >>> renderer = TraceRenderer()
        >>> renderer.render(construct.agent_runs)
    """

    def __init__(self, config: TraceConfig | None = None) -> None:
        """Initialize renderer with configuration.

        Args:
            config: Trace configuration. If None, reads from environment.
        """
        from tenro.debug.config import get_trace_config

        self._config = config or get_trace_config()

    def render(self, agents: list[AgentRun], test_name: str | None = None) -> None:
        """Render agent traces to console.

        Args:
            agents: List of root agent runs to render.
            test_name: Optional test name for the header.
        """
        if not agents:
            return

        output = self.render_to_string(agents, test_name)

        from rich.console import Console

        console = Console()
        console.print(output)

    def render_to_string(self, agents: list[AgentRun], test_name: str | None = None) -> str:
        """Render traces to string for testing.

        Args:
            agents: List of root agent runs to render.
            test_name: Optional test name for the header.

        Returns:
            Formatted trace output as string.
        """
        if not agents:
            return ""

        lines: list[str] = []

        # Header
        lines.extend(self._build_header(test_name))

        # Root agents (no tree prefix, separated by blank lines)
        for i, agent in enumerate(agents):
            if i > 0:
                lines.append("")  # Blank line between root agents
            lines.extend(self._build_agent_tree(agent))

        # Footer with summary
        lines.extend(self._build_footer(agents))

        return "\n".join(lines)

    def _build_header(self, test_name: str | None) -> list[str]:
        """Build the header section."""
        lines: list[str] = []
        title = f"Trace: {test_name}" if test_name else "Trace"
        lines.append(f"\n[bold]{title}[/bold]")
        lines.append("[dim]" + "\u2500" * 64 + "[/dim]")
        lines.append("")
        return lines

    def _build_agent_tree(self, agent: AgentRun) -> list[str]:
        """Build tree for a single root agent."""
        lines: list[str] = []

        # Root agent header (no tree prefix)
        lines.append(self._format_span_header(agent))

        # Build span content (input, children, output)
        lines.extend(self._build_span_content(agent, SPACE))

        return lines

    def _build_tree(
        self, spans: Sequence[BaseSpan], indent: str, has_output_after: bool = False
    ) -> list[str]:
        """Build tree representation of child spans recursively."""
        lines: list[str] = []

        for i, span in enumerate(spans):
            is_last = i == len(spans) - 1 and not has_output_after
            connector = LAST if is_last else BRANCH
            child_indent = indent + (SPACE if is_last else f"{VERTICAL}  ")

            # Header line
            lines.append(f"{indent}{connector} {self._format_span_header(span)}")

            # Build span content (input, children, output)
            lines.extend(self._build_span_content(span, child_indent))

        return lines

    def _build_span_content(self, span: BaseSpan, indent: str) -> list[str]:
        """Build input, children, and output for any span type."""
        from tenro.core.spans import AgentRun, LLMCall, ToolCall

        lines: list[str] = []
        if not self._config.show_io_preview:
            # Still need to render children even without IO preview
            if isinstance(span, AgentRun) and span.spans:
                lines.append(f"{indent}{VERTICAL}")
                lines.extend(self._build_tree(span.spans, indent))
            return lines

        input_result = self._get_input(span)
        output_result = self._get_output(span)
        has_children = isinstance(span, AgentRun) and bool(span.spans)

        # Determine semantic labels based on span type
        if isinstance(span, AgentRun):
            in_label = "user: "
            out_label = ""
        elif isinstance(span, LLMCall):
            in_label = "prompt: "
            out_label = ""
        elif isinstance(span, ToolCall):
            in_label = ""
            out_label = ""
        else:
            in_label = ""
            out_label = ""

        # Input (always before children)
        if input_result is not None:
            text, needs_quotes = input_result
            preview = self._truncate(text, self._config.max_preview_length)
            formatted = f'"{preview}"' if needs_quotes else preview
            connector = BRANCH if (has_children or output_result is not None) else LAST
            lines.append(f"{indent}{connector} {ARROW_IN} {in_label}{formatted}")

        # Children (for agents only)
        if isinstance(span, AgentRun) and span.spans:
            lines.append(f"{indent}{VERTICAL}")
            has_output = output_result is not None or span.error is not None
            lines.extend(self._build_tree(span.spans, indent, has_output_after=has_output))

        # Error or Output (always after children)
        if span.error:
            if has_children:
                lines.append(f"{indent}{VERTICAL}")
            lines.append(f"{indent}{LAST} [red]{ARROW_OUT} error: {span.error}[/red]")
        elif output_result is not None:
            text, needs_quotes = output_result
            preview = self._truncate(text, self._config.max_preview_length)
            formatted = f'"{preview}"' if needs_quotes else preview
            if has_children:
                lines.append(f"{indent}{VERTICAL}")
            lines.append(f"{indent}{LAST} {ARROW_OUT} {out_label}{formatted}")

        return lines

    def _format_span_header(self, span: BaseSpan) -> str:
        """Format span header with icon, name, status."""
        from tenro.core.spans import AgentRun, LLMCall, ToolCall

        if isinstance(span, AgentRun):
            icon = get_span_icon("AGENT")
            name = span.name
        elif isinstance(span, LLMCall):
            icon = get_span_icon("LLM")
            # Just model name, no provider prefix
            name = span.model or "unknown"
        elif isinstance(span, ToolCall):
            icon = get_span_icon("TOOL")
            name = span.tool_name
        else:
            icon = "?"
            name = "unknown"

        # Only show ERR on error, nothing on success
        if span.error:
            padding = " " * max(0, 55 - len(name))
            return f"{icon} [bold]{name}[/bold]{padding} [bold red]ERR[/bold red]"
        return f"{icon} [bold]{name}[/bold]"

    def _get_input(self, span: BaseSpan) -> tuple[str, bool] | None:
        """Extract input text from span.

        Args:
            span: The span to extract input from.

        Returns:
            Tuple of (text, is_quoted) or None. is_quoted indicates if quotes needed.
        """
        from tenro.core.spans import AgentRun, LLMCall, ToolCall

        if isinstance(span, AgentRun):
            if span.input_data is not None:
                data = span.input_data
                # Unwrap single-element tuples (common from *args capture)
                if isinstance(data, tuple) and len(data) == 1:
                    data = data[0]
                if isinstance(data, str):
                    return (data, True)
                return (repr(data), False)
            return None
        elif isinstance(span, LLMCall):
            if span.messages:
                last_msg = span.messages[-1]
                content = last_msg.get("content", "")
                return (str(content), True) if content else None
            return None
        elif isinstance(span, ToolCall):
            parts: list[str] = []
            if span.args:
                parts.extend(repr(a) for a in span.args)
            if span.kwargs:
                parts.extend(f"{k}={v!r}" for k, v in span.kwargs.items())
            return (", ".join(parts), False) if parts else None
        return None

    def _get_output(self, span: BaseSpan) -> tuple[str, bool] | None:
        """Extract output text from span.

        Args:
            span: The span to extract output from.

        Returns:
            Tuple of (text, is_quoted) or None. is_quoted indicates if quotes needed.
        """
        from tenro.core.spans import AgentRun, LLMCall, ToolCall

        if isinstance(span, AgentRun):
            if span.output_data is not None:
                if isinstance(span.output_data, str):
                    return (span.output_data, True)
                return (repr(span.output_data), False)
            return None
        elif isinstance(span, LLMCall):
            if span.response:
                return (span.response, True)
            return None
        elif isinstance(span, ToolCall):
            if span.result is not None:
                if isinstance(span.result, str):
                    return (span.result, True)
                return (repr(span.result), False)
            return None
        return None

    def _truncate(self, text: str, max_length: int) -> str:
        """Truncate text with ellipsis."""
        clean = text.replace("\n", " ").replace("\r", "")
        if len(clean) <= max_length:
            return clean
        return clean[: max_length - 3] + "..."

    def _build_footer(self, agents: list[AgentRun]) -> list[str]:
        """Build the footer with summary statistics."""
        lines: list[str] = []
        lines.append("")
        lines.append("[dim]" + "\u2500" * 64 + "[/dim]")

        stats = self._count_spans(agents)
        summary_parts = [
            f"{stats['agents']} agent{'s' if stats['agents'] != 1 else ''}",
            f"{stats['llm_calls']} LLM call{'s' if stats['llm_calls'] != 1 else ''}",
            f"{stats['tool_calls']} tool call{'s' if stats['tool_calls'] != 1 else ''}",
        ]

        if agents:
            total_ms = sum(a.latency_ms for a in agents)
            duration = f"{total_ms / 1000:.2f}s" if total_ms >= 1000 else f"{total_ms:.0f}ms"
            summary_parts.append(f"Total: {duration}")

        lines.append(f"[dim]Summary: {' | '.join(summary_parts)}[/dim]")
        lines.append("")
        return lines

    def _count_spans(self, agents: list[AgentRun]) -> dict[str, int]:
        """Count spans by type."""
        from tenro.core.spans import AgentRun, LLMCall, ToolCall

        counts = {"agents": 0, "llm_calls": 0, "tool_calls": 0}

        def count_recursive(agent: AgentRun) -> None:
            counts["agents"] += 1
            for span in agent.spans:
                if isinstance(span, AgentRun):
                    count_recursive(span)
                elif isinstance(span, LLMCall):
                    counts["llm_calls"] += 1
                elif isinstance(span, ToolCall):
                    counts["tool_calls"] += 1

        for agent in agents:
            count_recursive(agent)

        return counts
