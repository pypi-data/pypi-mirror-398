# Copyright 2025 Tenro.ai
# SPDX-License-Identifier: Apache-2.0

"""Pytest fixtures for Tenro SDK.

This module provides fixtures for:
- Construct: Simulate and intercept tool/LLM calls
"""

from __future__ import annotations

from collections.abc import Generator
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from tenro.construct.construct import Construct


@pytest.fixture
def construct(request: pytest.FixtureRequest) -> Generator[Construct, None, None]:
    """Provide a Construct instance for testing.

    This is the primary pytest fixture for Tenro testing. The construct
    automatically handles setup/teardown of all patches and simulations.

    Args:
        request: Pytest fixture request for accessing test item.

    Yields:
        Construct instance ready for simulation and testing.

    Examples:
        >>> def test_my_agent(construct):
        ...     construct.simulate_llm(provider="openai", response="Hi")
        ...     result = my_agent.run()
        ...     assert "Hi" in result

        Multi-turn conversations:
        >>> def test_conversation(construct):
        ...     construct.simulate_llm(
        ...         provider="anthropic",
        ...         responses=["Turn 1", "Turn 2", "Turn 3"]
        ...     )
        ...     agent = ConversationAgent()
        ...     agent.run()
    """
    from tenro.construct.construct import Construct

    c = Construct()

    # Store reference on test item for trace visualization in teardown
    request.node._tenro_construct = c  # pyright: ignore[reportAttributeAccessIssue]

    with c:
        yield c
