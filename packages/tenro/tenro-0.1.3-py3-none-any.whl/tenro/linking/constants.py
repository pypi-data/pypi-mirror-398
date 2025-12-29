# Copyright 2025 Tenro.ai
# SPDX-License-Identifier: Apache-2.0

"""Entry method constants for decorator target detection.

Centralizes the entry method lists for agents and tools across all supported
frameworks. These are used by the detection module to find wrappable methods.
"""

from __future__ import annotations

# Agent entry methods - covers major frameworks
# See docs-private/linking.md for framework compatibility matrix
AGENT_ENTRY_METHODS: frozenset[str] = frozenset(
    {
        # Generic
        "execute",
        "run",
        "__call__",
        # LangChain
        "invoke",
        "ainvoke",
        # CrewAI
        "kickoff",
        "kickoff_async",
        # AutoGen
        "initiate_chat",
        "initiate_chats",
        # LlamaIndex
        "chat",
        "achat",
        # Pydantic AI
        "run_sync",
        # Streaming methods
        "stream",
        "astream",
        "run_stream",
        "stream_chat",
    }
)

# Tool entry methods - covers LangChain BaseTool and similar patterns
TOOL_ENTRY_METHODS: frozenset[str] = frozenset(
    {
        "invoke",
        "ainvoke",
        "run",
        "_run",
        "_arun",
        "__call__",
        # Streaming methods
        "stream",
        "astream",
    }
)

__all__ = ["AGENT_ENTRY_METHODS", "TOOL_ENTRY_METHODS"]
