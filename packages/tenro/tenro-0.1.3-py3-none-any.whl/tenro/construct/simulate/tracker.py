# Copyright 2025 Tenro.ai
# SPDX-License-Identifier: Apache-2.0

"""Simulation validation tracking.

Validates that simulations are properly used during tests:
- Registered simulations must be triggered
- `@link_llm` decorated functions must make actual HTTP calls
"""

from __future__ import annotations

from tenro.construct.http.builders import ProviderSchemaFactory
from tenro.core.spans import LLMCall, LLMScope
from tenro.errors import MissingLLMCallError, UnusedSimulationError


class SimulationTracker:
    """Validates simulation registration, triggering, and execution.

    Raises `MissingLLMCallError` when `@link_llm` ran but no HTTP call happened.
    Raises `UnusedSimulationError` when simulations were registered but never used.

    Supports optional simulations that won't error if unused.
    """

    def __init__(self) -> None:
        self._registered: set[str] = set()
        self._optional: set[str] = set()
        self._triggered: set[str] = set()

    def register(self, provider: str, *, optional: bool = False) -> None:
        """Record that a simulation was registered for a provider.

        Args:
            provider: Provider name (e.g., "openai", "anthropic").
            optional: If `True`, this simulation won't error if unused.
        """
        self._registered.add(provider)
        if optional:
            self._optional.add(provider)

    def mark_triggered(self, provider: str) -> None:
        """Record that a simulation was actually triggered."""
        self._triggered.add(provider)

    def validate(
        self,
        llm_calls: list[LLMCall],
        supported_providers: list[str],
        llm_scopes: list[LLMScope] | None = None,
    ) -> None:
        """Validate simulation usage and raise errors if invalid.

        Args:
            llm_calls: LLM calls recorded during test execution.
            supported_providers: Providers that support HTTP simulation.
            llm_scopes: LLMScope spans from @link_llm decorator.

        Raises:
            MissingLLMCallError: `@link_llm` ran but no HTTP call was made.
            UnusedSimulationError: Simulation registered but never triggered.
        """
        llm_scopes = llm_scopes or []
        self._check_unused_providers(llm_scopes, supported_providers)
        self._check_missing_http_calls(llm_calls, llm_scopes, supported_providers)

    def _check_unused_providers(
        self,
        llm_scopes: list[LLMScope],
        supported_providers: list[str],
    ) -> None:
        """Check for completely unused providers."""
        unused = self._registered - self._triggered - self._optional
        if not unused:
            return

        provider = sorted(unused)[0]

        # Check for LLMScope spans without matching HTTP calls
        scope_calls = [s for s in llm_scopes if s.provider == provider]
        if scope_calls:
            msg = self._build_missing_call_message(
                provider=provider,
                scopes=scope_calls,
                supported_providers=supported_providers,
            )
            raise MissingLLMCallError(msg)

        msg = self._build_unused_simulation_message(
            provider=provider,
            supported_providers=supported_providers,
        )
        raise UnusedSimulationError(msg)

    def _check_missing_http_calls(
        self,
        llm_calls: list[LLMCall],
        llm_scopes: list[LLMScope],
        supported_providers: list[str],
    ) -> None:
        """Check for @link_llm calls that didn't make HTTP requests."""
        for provider in self._registered - self._optional:
            provider_scopes = [s for s in llm_scopes if s.provider == provider]
            covered_scope_ids = {c.llm_scope_id for c in llm_calls if c.llm_scope_id}
            missing_scopes = [s for s in provider_scopes if s.id not in covered_scope_ids]

            if missing_scopes:
                msg = self._build_missing_call_message(
                    provider=provider,
                    scopes=missing_scopes,
                    supported_providers=supported_providers,
                )
                raise MissingLLMCallError(msg)

    def _build_missing_call_message(
        self,
        provider: str,
        scopes: list[LLMScope],
        supported_providers: list[str],
    ) -> str:
        """Build error message when @link_llm was used but no HTTP call was made."""
        lines = [
            f"@link_llm('{provider}') was called but no LLM HTTP request was made",
            "",
            "Your decorated function returned without hitting the LLM provider API.",
            "This breaks the harness because the simulation never had a chance to activate.",
            "",
            f"  Provider: {provider}",
            f"  @link_llm calls observed: {len(scopes)}",
            "  LLM Provider HTTP calls intercepted: 0",
        ]

        if scopes:
            lines.append("")
            lines.append("Functions that didn't make HTTP calls:")
            seen: set[str] = set()
            for scope in scopes:
                if scope.caller_signature and scope.caller_signature not in seen:
                    seen.add(scope.caller_signature)
                    loc = f" at {scope.caller_location}" if scope.caller_location else ""
                    lines.append(f"  - {scope.caller_signature}{loc}")

        lines.extend(
            [
                "",
                "This usually means your @link_llm function returned a stub",
                "instead of calling the real LLM client.",
                "",
                f"Supported HTTP providers: {', '.join(sorted(supported_providers))}",
                "Note: HTTP interception only works with httpx-based clients "
                "(e.g., openai, anthropic, google-genai).",
            ]
        )

        example = ProviderSchemaFactory.get_code_example(provider)
        if example:
            lines.extend(
                [
                    "",
                    "Fix: Ensure your decorated function makes real HTTP calls:",
                    f"  @link_llm('{provider}')",
                    "  def call_llm(prompt: str) -> str:",
                    f"      {example['client']}",
                    f"      {example['call']}",
                    f"      {example['extract']}",
                ]
            )
        else:
            lines.extend(
                [
                    "",
                    "Fix: Ensure your decorated function makes real HTTP calls",
                    f"to the {provider} API.",
                ]
            )

        return "\n".join(lines)

    def _build_unused_simulation_message(
        self,
        provider: str,
        supported_providers: list[str],
    ) -> str:
        """Build error message for unused simulation."""
        lines = [
            f"HTTP simulation for '{provider}' was never triggered",
            "",
            "Your test configured simulate_llm() for this provider,",
            "but no LLM calls were recorded for it.",
            "",
            f"  Provider: {provider}",
            "  @link_llm calls recorded: 0",
            "  HTTP calls intercepted: 0",
            "",
            "This usually means the code path that would call the LLM",
            "never executed during the test.",
            "",
            f"Supported LLM providers: {', '.join(sorted(supported_providers))}",
            "",
            "Fix: Remove the unused simulation or execute the code path:",
            f"  construct.simulate_llm(provider='{provider}', response='...')",
            "  # ... trigger the LLM call ...",
        ]
        return "\n".join(lines)

    def reset(self) -> None:
        """Clear all tracking state."""
        self._registered.clear()
        self._optional.clear()
        self._triggered.clear()
