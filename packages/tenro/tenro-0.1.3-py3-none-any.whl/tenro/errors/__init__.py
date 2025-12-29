# Copyright 2025 Tenro.ai
# SPDX-License-Identifier: Apache-2.0

"""Exceptions for Tenro SDK."""

from __future__ import annotations

from tenro.errors.base import (
    AgentRecursionError,
    ConfigurationError,
    ConstructConfigurationError,
    ConstructCoverageError,
    ConstructHarnessError,
    MissingLLMCallError,
    TenroError,
    UnusedSimulationError,
    ValidationError,
)

__all__ = [
    # Base
    "TenroError",
    # General errors
    "ValidationError",
    "ConfigurationError",
    "AgentRecursionError",
    # Construct harness errors (priority hierarchy)
    "ConstructHarnessError",
    "ConstructConfigurationError",
    "ConstructCoverageError",
    "MissingLLMCallError",
    "UnusedSimulationError",
]
