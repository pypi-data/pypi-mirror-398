# Copyright 2025 Tenro.ai
# SPDX-License-Identifier: Apache-2.0

"""Linking utilities for agents, LLMs, and tools.

Provides decorators for registering functions, classes, and framework objects
with the Tenro system for testing and observability.
"""

from __future__ import annotations

from tenro.linking.context import (
    get_active_construct as _get_active_construct,
)
from tenro.linking.context import (
    set_active_construct as _set_active_construct,
)
from tenro.linking.decorators import link_agent, link_llm, link_tool

__all__ = [
    "link_agent",
    "link_llm",
    "link_tool",
    # Internal APIs used by construct.py
    "_get_active_construct",
    "_set_active_construct",
]
