# Copyright 2025 Tenro.ai
# SPDX-License-Identifier: Apache-2.0

"""Client initialization for Tenro SDK."""

from __future__ import annotations

from tenro.client._client import Tenro


def init() -> Tenro:
    """Initialize Tenro client for local testing and evaluation.

    Creates a Tenro client instance for use with the Construct testing
    system. The client provides utilities for logging test runs.

    Returns:
        Tenro client instance.

    Examples:
        >>> import tenro
        >>> with tenro.init() as client:
        ...     # Use client for testing
        ...     ...
    """
    return Tenro()
