# Copyright 2025 Tenro.ai
# SPDX-License-Identifier: Apache-2.0

"""Testing module for Tenro SDK.

This module provides:
- Core testing functionality (init, client, tracing)
- Pytest plugin integration (auto-loaded via pytest11 entry point)
- Pytest fixtures (construct)
"""

from __future__ import annotations

from tenro.client._client import Tenro
from tenro.client.init import init

# Pytest plugin components (imported for convenience, auto-loaded by pytest)
from tenro.pytest_plugin.fixtures import construct
from tenro.pytest_plugin.marks import tenro

__all__ = [
    # Core testing API
    "init",
    "Tenro",
    # Pytest fixtures (auto-loaded by pytest, exported for convenience)
    "construct",
    # Pytest marker (optional, for explicit imports)
    "tenro",
]
