# Copyright 2025 Tenro.ai
# SPDX-License-Identifier: Apache-2.0

"""Compatibility shim for decorator imports."""

from __future__ import annotations

from tenro.linking.decorators import (
    _get_active_construct,
    _set_active_construct,
    link_agent,
    link_llm,
    link_tool,
)

__all__ = [
    "link_agent",
    "link_llm",
    "link_tool",
    "_get_active_construct",
    "_set_active_construct",
]
