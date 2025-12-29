# Copyright 2025 Tenro.ai
# SPDX-License-Identifier: Apache-2.0

"""Icon and connector constants for trace visualization.

Shared by debug output and verification error messages.
"""

from __future__ import annotations

from typing import Literal

# Span type emojis
EMOJI_AGENT = "\U0001f916"  # 🤖
EMOJI_LLM = "\U0001f9e0"  # 🧠
EMOJI_TOOL = "\U0001f527"  # 🔧

# Tree connectors
BRANCH = "\u251c\u2500"  # ├─
LAST = "\u2514\u2500"  # └─
VERTICAL = "\u2502"  # │
SPACE = "   "  # Three spaces for alignment

# Arrows
ARROW_IN = "\u2192"  # →
ARROW_OUT = "\u2190"  # ←

# Status indicators (Rich markup for colored output)
STATUS_OK = "[green]OK[/green]"
STATUS_ERROR = "[bold red]ERR[/bold red]"
STATUS_RUNNING = "[yellow]...[/yellow]"


def get_span_icon(span_kind: Literal["AGENT", "LLM", "TOOL"]) -> str:
    """Get the emoji for a span kind.

    Args:
        span_kind: The type of span (AGENT, LLM, or TOOL).

    Returns:
        Emoji string.
    """
    icons = {"AGENT": EMOJI_AGENT, "LLM": EMOJI_LLM, "TOOL": EMOJI_TOOL}
    return icons.get(span_kind, "?")


def get_status_icon(status: str, error: str | None = None) -> str:
    """Get the status icon based on span status.

    Args:
        status: The span status (running, completed, error).
        error: Optional error message (indicates error status).

    Returns:
        Rich-formatted status string.
    """
    if error is not None:
        return STATUS_ERROR
    if status == "running":
        return STATUS_RUNNING
    return STATUS_OK
