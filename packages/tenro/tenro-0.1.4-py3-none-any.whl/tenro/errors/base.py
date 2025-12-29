# Copyright 2025 Tenro.ai
# SPDX-License-Identifier: Apache-2.0

"""Base exceptions for Tenro SDK."""

from __future__ import annotations


class TenroError(Exception):
    """Base exception for all Tenro errors."""


class ValidationError(TenroError):
    """Raised when validation fails."""


class ConfigurationError(TenroError):
    """Raised when configuration is invalid."""


class AgentRecursionError(TenroError):
    """Raised when agent exceeds maximum nesting depth.

    This usually indicates an infinite loop between agents
    (e.g., Agent A calls Agent B, which calls Agent A again).
    """


class ConstructHarnessError(TenroError):
    """Base exception for Construct test harness errors."""


class ConstructConfigurationError(ConstructHarnessError):
    """Raised when the test harness is misconfigured.

    Configuration errors are always raised, even when the test body fails.
    """


class ConstructCoverageError(ConstructHarnessError):
    """Raised when a registered simulation was never triggered.

    Coverage errors are suppressed when the test body fails, since fixing
    the test logic often resolves coverage issues.
    """


class MissingLLMCallError(ConstructConfigurationError):
    """Raised when a linked LLM function doesn't call the provider.

    The decorated function executed but no HTTP request was made to the
    LLM provider, so the configured simulation was never used.

    Examples:
        >>> @link_llm("openai")
        ... def call_llm(prompt: str) -> str:
        ...     return "stub"  # Should call openai.chat.completions.create()
    """


class UnusedSimulationError(ConstructCoverageError):
    """Raised when a simulation was registered but never triggered.

    The `simulate_llm()` call set up a simulation, but the code path that would
    trigger it was never executed.

    Examples:
        >>> construct.simulate_llm(provider="anthropic", response="Hello")
        >>> # ... test code that never calls anthropic ...
    """
