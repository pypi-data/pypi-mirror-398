# Copyright 2025 Tenro.ai
# SPDX-License-Identifier: Apache-2.0

"""Pytest plugin entry points for Tenro.

Auto-loads with pytest and stays dormant unless enabled via --tenro
or TENRO_ENABLED.
"""

from __future__ import annotations

import os

import pytest
from _pytest.config import Config
from _pytest.config.argparsing import Parser

# Import fixtures so pytest can discover them
from tenro.pytest_plugin.fixtures import construct

# Module-level state
_plugin_enabled = False
_trace_enabled = False

# Re-export fixtures for pytest discovery
__all__ = ["construct"]


def pytest_addoption(parser: Parser) -> None:
    """Add Tenro CLI options to pytest.

    Args:
        parser: Pytest argument parser.
    """
    group = parser.getgroup("tenro")
    group.addoption(
        "--tenro",
        action="store_true",
        default=False,
        help="Enable Tenro tracing and constructing for agent tests",
    )
    group.addoption(
        "--tenro-trace",
        action="store_true",
        default=False,
        help="Print trace visualization after each test",
    )


def pytest_configure(config: Config) -> None:
    """Configure Tenro plugin when pytest starts.

    Registers markers and toggles plugin state based on --tenro or
    TENRO_ENABLED. Trace output is enabled via --tenro-trace or TENRO_TRACE.

    Args:
        config: Pytest configuration object.
    """
    global _plugin_enabled, _trace_enabled

    # Register custom marker
    config.addinivalue_line(
        "markers",
        "tenro: Mark test for Tenro tracing and constructing",
    )

    truthy_values = ("true", "1", "yes")

    # Check if plugin should be enabled
    _plugin_enabled = (
        config.getoption("--tenro", default=False)
        or os.getenv("TENRO_ENABLED", "").lower() in truthy_values
    )

    # Check if trace output should be enabled
    _trace_enabled = (
        config.getoption("--tenro-trace", default=False)
        or os.getenv("TENRO_TRACE", "").lower() in truthy_values
    )


def pytest_collection_modifyitems(config: Config, items: list[pytest.Item]) -> None:
    """Collection hook for selective tracing.

    Args:
        config: Pytest configuration.
        items: Collected test items.
    """
    if not _plugin_enabled:
        return

    pass


def pytest_runtest_setup(item: pytest.Item) -> None:
    """Setup hook called before each test runs.

    Args:
        item: Test item about to run.
    """
    if not _plugin_enabled:
        return

    if "tenro" in item.keywords or _plugin_enabled:
        pass


def pytest_runtest_call(item: pytest.Item) -> None:
    """Hook called when test is executed.

    Args:
        item: Test item being executed.
    """
    if not _plugin_enabled:
        return

    pass


def pytest_runtest_teardown(item: pytest.Item) -> None:
    """Teardown hook called after each test.

    Renders trace visualization if --tenro-trace is enabled and the test
    used the construct fixture.

    Args:
        item: Test item that just ran.
    """
    if not _trace_enabled:
        return

    # Check if this test used the construct fixture
    construct = getattr(item, "_tenro_construct", None)
    if construct is None:
        return

    # Render trace if there are any agent runs
    agents = construct.agent_runs
    if not agents:
        return

    from tenro.debug import TraceConfig, TraceRenderer

    config = TraceConfig(enabled=True)
    renderer = TraceRenderer(config=config)
    renderer.render(agents, test_name=item.name)
