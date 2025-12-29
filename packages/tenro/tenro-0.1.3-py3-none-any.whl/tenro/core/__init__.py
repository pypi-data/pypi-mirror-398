# Copyright 2025 Tenro.ai
# SPDX-License-Identifier: Apache-2.0

"""Core domain models and infrastructure for Tenro SDK.

This module contains the fundamental building blocks:
- Span types (LLMCall, ToolCall, AgentRun) - operation tracking
- SpanEvent - immutable event records
- Context - async-safe span stack tracking
- LifecycleManager - span lifecycle with event emission
"""

from __future__ import annotations

from tenro.core.context import (
    clear_context,
    get_current_span,
    get_span_stack,
    get_trace_id,
    pop_span,
    push_span,
)
from tenro.core.eval_types import EvalResult, EvalScore
from tenro.core.events import SpanEvent
from tenro.core.lifecycle_manager import LifecycleManager
from tenro.core.response_types import ProviderResponse
from tenro.core.spans import AgentRun, BaseSpan, LLMCall, ToolCall
from tenro.core.trace_types import SpanAttributes, TraceContext

__all__ = [
    # Span types
    "BaseSpan",
    "LLMCall",
    "ToolCall",
    "AgentRun",
    # Events
    "SpanEvent",
    # Context
    "push_span",
    "pop_span",
    "get_current_span",
    "get_trace_id",
    "get_span_stack",
    "clear_context",
    # Lifecycle
    "LifecycleManager",
    # Types
    "EvalResult",
    "EvalScore",
    "ProviderResponse",
    "TraceContext",
    "SpanAttributes",
]
