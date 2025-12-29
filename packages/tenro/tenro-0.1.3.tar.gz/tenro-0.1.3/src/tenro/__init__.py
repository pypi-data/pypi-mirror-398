# Copyright 2025 Tenro.ai
# SPDX-License-Identifier: Apache-2.0

"""Tenro Python SDK for local AI agent testing and evaluation.

Provides tools for local agent testing, tracing, and evaluation.
"""

from __future__ import annotations

# Import evals submodule for `import tenro.evals`
from tenro import evals
from tenro.client import Tenro, init
from tenro.construct import Construct
from tenro.core.eval_types import EvalResult
from tenro.errors import (
    ConfigurationError,
    ConstructConfigurationError,
    ConstructCoverageError,
    ConstructHarnessError,
    MissingLLMCallError,
    TenroError,
    UnusedSimulationError,
    ValidationError,
)
from tenro.linking import link_agent, link_llm, link_tool

__version__ = "0.1.0"

__all__ = [
    # Main initialization
    "init",
    # Client instance type
    "Tenro",
    # Decorators for linking agents to Construct or production
    "link_agent",
    "link_llm",
    "link_tool",
    # Evaluation utilities
    "evals",
    # Construct
    "Construct",
    # Types
    "EvalResult",
    # Base exceptions
    "TenroError",
    "ValidationError",
    "ConfigurationError",
    # Construct harness errors (priority hierarchy)
    "ConstructHarnessError",
    "ConstructConfigurationError",
    "ConstructCoverageError",
    "MissingLLMCallError",
    "UnusedSimulationError",
]
