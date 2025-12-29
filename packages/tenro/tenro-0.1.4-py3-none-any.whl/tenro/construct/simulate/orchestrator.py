# Copyright 2025 Tenro.ai
# SPDX-License-Identifier: Apache-2.0

"""Simulation orchestrator for Construct testing harness.

Manages simulation rules, patching, and lifecycle integration for
tool, agent, and LLM simulations.
"""

from __future__ import annotations

import functools
import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from uuid_utils import uuid7

from tenro.construct.http.builders import ProviderSchemaFactory
from tenro.construct.simulate.helpers import (
    execute_simulation_logic,
    get_response_by_index,
    normalize_result_sequence,
    validate_simulation_params,
)
from tenro.construct.simulate.llm import (
    normalize_response_sequence,
    resolve_provider_from_target,
    should_use_http_interception,
    validate_llm_simulation_params,
)
from tenro.construct.simulate.rule import SimulationRule
from tenro.construct.simulate.target_resolution import (
    parse_dotted_path,
    validate_and_resolve_target,
)
from tenro.construct.simulate.tracker import SimulationTracker
from tenro.core import context
from tenro.core.response_types import ProviderResponse
from tenro.core.spans import AgentRun, LLMCall, ToolCall

if TYPE_CHECKING:
    from tenro.construct.http import HttpInterceptor
    from tenro.core.lifecycle_manager import LifecycleManager


class SimulationOrchestrator:
    """Orchestrates simulation rules and patching for Construct.

    Manages the lifecycle of simulations including:
    - Storing simulation rules
    - Applying/restoring patches
    - Tracking simulation state
    - Coordinating with HTTP interceptor for LLM simulations
    """

    def __init__(
        self,
        lifecycle: LifecycleManager,
        http_interceptor: HttpInterceptor,
    ) -> None:
        """Initialize orchestrator with dependencies.

        Args:
            lifecycle: Lifecycle manager for span tracking.
            http_interceptor: HTTP interceptor for LLM simulations.
        """
        self._lifecycle = lifecycle
        self._http_interceptor = http_interceptor
        self._simulations: dict[str, SimulationRule] = {}
        self._originals: dict[str, Any] = {}
        self._active: bool = False
        self._http_simulation_enabled: bool = False
        self._simulation_tracker = SimulationTracker()

    @property
    def simulation_tracker(self) -> SimulationTracker:
        """Get the simulation tracker for validation."""
        return self._simulation_tracker

    @property
    def http_simulation_enabled(self) -> bool:
        """Check if HTTP simulation is enabled."""
        return self._http_simulation_enabled

    def activate(self) -> None:
        """Activate simulations and apply all pending patches."""
        self._active = True
        if self._http_simulation_enabled:
            self._http_interceptor.start()
        for target_path in self._simulations:
            self._apply_patch(target_path)

    def deactivate(self) -> None:
        """Deactivate simulations and restore originals."""
        self._active = False
        self._stop_http_interceptor()
        self._stop_patches()
        self._restore_originals()
        self._clear_state()

    def handle_http_call(
        self,
        provider: str,
        messages: list[dict[str, Any]],
        model: str | None,
        response_text: str,
        agent: str | None,
    ) -> None:
        """Handle HTTP interception callback by creating LLMCall span.

        Always creates a new LLMCall. LLMScope (from @link_llm decorator) is
        transparent for parent attribution - the LLMCall references it via
        llm_scope_id for grouping but gets its parent_span_id from structural
        spans (Agent, Tool).

        Args:
            provider: LLM provider name (e.g., "anthropic", "openai").
            messages: List of message dicts from the request body.
            model: Model identifier from the request.
            response_text: The simulated response text.
            agent: Name of the agent that made this call, or None.
        """
        self._simulation_tracker.mark_triggered(provider)

        span = self._create_llm_span(
            provider=provider,
            messages=messages,
            model=model,
            response=response_text,
            agent_name=agent,
        )
        with self._lifecycle.start_span(span):
            pass

    def simulate_tool(
        self,
        target: str | Callable[..., Any],
        result: Any = None,
        results: list[Any] | None = None,
        side_effect: Callable[..., Any] | None = None,
    ) -> None:
        """Simulate a tool with lifecycle tracking.

        Args:
            target: Tool path or function object.
            result: Single static value to return.
            results: List of values for sequential calls.
            side_effect: Callable for dynamic behavior.

        Raises:
            ValueError: If multiple result parameters are provided.
        """
        validate_simulation_params(result, results, side_effect)
        function_path = validate_and_resolve_target(target, "tool")
        result_sequence = normalize_result_sequence(result, results)

        def _lifecycle_wrapper(*args: Any, **kwargs: Any) -> Any:
            span = ToolCall(
                id=str(uuid7()),
                trace_id=str(uuid7()),
                start_time=time.time(),
                tool_name=function_path,
                args=args,
                kwargs=kwargs,
            )
            with self._lifecycle.start_span(span):
                value = execute_simulation_logic(
                    side_effect, result_sequence, function_path, args, kwargs
                )
                span.result = value
                return value

        rule = SimulationRule(side_effect=_lifecycle_wrapper)
        self._simulations[function_path] = rule

        if self._active:
            self._apply_patch(function_path)

    def simulate_agent(
        self,
        target: str | Callable[..., Any],
        result: Any = None,
        results: list[Any] | None = None,
        side_effect: Callable[..., Any] | None = None,
    ) -> None:
        """Simulate an agent with lifecycle tracking.

        Args:
            target: Agent path or function object.
            result: Single static value to return.
            results: List of values for sequential calls.
            side_effect: Callable for dynamic behavior.

        Raises:
            ValueError: If multiple result parameters are provided.
        """
        validate_simulation_params(result, results, side_effect)
        agent_path = validate_and_resolve_target(target, "agent")
        result_sequence = normalize_result_sequence(result, results)

        def _lifecycle_wrapper(*args: Any, **kwargs: Any) -> Any:
            span = AgentRun(
                id=str(uuid7()),
                trace_id=str(uuid7()),
                start_time=time.time(),
                name=agent_path,
                input_data=kwargs if kwargs else (args[0] if args else None),
                kwargs=kwargs if kwargs else {},
            )
            with self._lifecycle.start_span(span):
                value = execute_simulation_logic(
                    side_effect, result_sequence, agent_path, args, kwargs
                )
                span.output_data = value
                return value

        rule = SimulationRule(side_effect=_lifecycle_wrapper)
        self._simulations[agent_path] = rule

        if self._active:
            self._apply_patch(agent_path)

    def simulate_llm(
        self,
        target: str | Callable[..., Any] | None = None,
        provider: str | None = None,
        *,
        response: str | None = None,
        responses: str | list[str | Exception] | None = None,
        model: str | None = None,
        tools: list[str | dict[str, Any]] | None = None,
        use_http: bool | None = None,
        optional: bool = False,
        **response_kwargs: Any,
    ) -> None:
        """Simulate LLM calls with provider detection and lifecycle tracking.

        Args:
            target: Optional Python function path to simulate.
            provider: LLM provider name.
            response: Single string response.
            responses: List of responses for sequential calls.
            model: Model identifier override.
            tools: Tool calls to include in response.
            use_http: Force HTTP interception or setattr patching.
            optional: If True, won't raise if unused.
            **response_kwargs: Provider-specific options.

        Raises:
            ValueError: If response parameters are invalid.
        """
        from tenro.construct.http.interceptor import PROVIDER_ENDPOINTS

        validate_llm_simulation_params(response, responses)
        response_sequence = normalize_response_sequence(response, responses)

        provider = resolve_provider_from_target(target, provider, self._detect_provider)
        custom_target_provided = target is not None
        use_http = should_use_http_interception(
            use_http, custom_target_provided, provider, set(PROVIDER_ENDPOINTS.keys())
        )

        if use_http and provider in PROVIDER_ENDPOINTS:
            self._simulate_llm_http(
                provider=provider,
                response_sequence=response_sequence,
                model=model,
                tools=tools,
                optional=optional,
                **response_kwargs,
            )
        else:
            self._simulate_llm_setattr(
                target=target,
                provider=provider,
                response_sequence=response_sequence,
                model=model,
                tools=tools,
                **response_kwargs,
            )

    def _detect_provider(self, target: str) -> str:
        """Auto-detect provider from target path."""
        return ProviderSchemaFactory.detect_provider(target)

    def _create_provider_response(
        self, provider: str, content: str, **kwargs: Any
    ) -> ProviderResponse:
        """Create a provider-specific response object."""
        return ProviderSchemaFactory.create_response(provider, content, **kwargs)

    def _create_llm_span(
        self,
        provider: str,
        messages: list[dict[str, Any]],
        model: str | None = None,
        response: str | None = None,
        agent_name: str | None = None,
    ) -> LLMCall:
        """Create LLMCall with proper context linking.

        Centralizes LLMCall creation to ensure consistent llm_scope_id
        and caller info propagation from @link_llm decorator.

        Args:
            provider: LLM provider name.
            messages: Request messages.
            model: Model identifier.
            response: Response text.
            agent_name: Agent that made this call.

        Returns:
            LLMCall span with context properly linked.
        """
        llm_scope = context.get_nearest_llm_scope()
        return LLMCall(
            id=str(uuid7()),
            trace_id=str(uuid7()),
            start_time=time.time(),
            provider=provider,
            model=model,
            messages=messages,
            response=response,
            agent_name=agent_name,
            llm_scope_id=llm_scope.id if llm_scope else None,
            caller_signature=llm_scope.caller_signature if llm_scope else None,
            caller_location=llm_scope.caller_location if llm_scope else None,
        )

    def _simulate_llm_http(
        self,
        provider: str,
        response_sequence: list[str | Exception],
        model: str | None = None,
        tools: list[str | dict[str, Any]] | None = None,
        optional: bool = False,
        **response_kwargs: Any,
    ) -> None:
        """Simulate LLM using HTTP interception."""
        text_responses = [r for r in response_sequence if isinstance(r, str)]

        if not text_responses:
            raise ValueError("HTTP simulation requires at least one string response")

        if model is not None:
            response_kwargs["model"] = model

        if tools is not None:
            response_kwargs["tool_calls"] = ProviderSchemaFactory.create_tool_calls(provider, tools)

        self._http_simulation_enabled = True
        self._simulation_tracker.register(provider, optional=optional)
        self._http_interceptor.simulate_provider(provider, text_responses, **response_kwargs)

        if self._active:
            self._http_interceptor.start()

    def _simulate_llm_setattr(
        self,
        target: str | Callable[..., Any] | None,
        provider: str,
        response_sequence: list[str | Exception],
        model: str | None = None,
        tools: list[str | dict[str, Any]] | None = None,
        **response_kwargs: Any,
    ) -> None:
        """Simulate LLM using setattr patching."""
        if target is None:
            target = ProviderSchemaFactory.get_default_target(provider)
            if target is None:
                available = list(ProviderSchemaFactory._default_targets.keys())
                raise ValueError(
                    f"Provider '{provider}' has no default target.\n"
                    f"Available providers with defaults: {', '.join(available)}"
                )

        if callable(target) and not isinstance(target, str):
            try:
                llm_path = validate_and_resolve_target(target, "llm")
            except ValueError:
                qualname = getattr(target, "__qualname__", "")
                module = getattr(target, "__module__", "")
                llm_path = f"{module}.{qualname}" if module and qualname else str(target)
        else:
            llm_path = str(target)

        if model is not None:
            response_kwargs["model"] = model

        if tools is not None:
            response_kwargs["tool_calls"] = ProviderSchemaFactory.create_tool_calls(provider, tools)

        response_index = {"current": 0}

        def _lifecycle_wrapper(*args: Any, **kwargs: Any) -> ProviderResponse:
            span = self._create_llm_span(
                provider=provider,
                messages=kwargs.get("messages", []),
                model=model,
            )
            with self._lifecycle.start_span(span):
                idx = response_index["current"]
                response_index["current"] += 1
                response_content = get_response_by_index(response_sequence, idx, llm_path)
                response_dict = self._create_provider_response(
                    provider, response_content, **response_kwargs
                )
                span.response = response_content
                return response_dict

        rule = SimulationRule(side_effect=_lifecycle_wrapper)
        self._simulations[llm_path] = rule

        if self._active:
            self._apply_patch(llm_path)

    def _apply_patch(self, target_path: str) -> None:
        """Apply a single patch for a simulation target."""
        if target_path in self._originals:
            return

        container, attr_name = parse_dotted_path(target_path)

        if not hasattr(container, attr_name):
            msg = f"'{container}' has no attribute '{attr_name}'"
            raise AttributeError(msg)

        original = getattr(container, attr_name)
        self._originals[target_path] = original

        rule = self._simulations[target_path]

        def make_wrapper(sim_rule: SimulationRule) -> Callable[..., Any]:
            @functools.wraps(original)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                if sim_rule.side_effect:
                    side_effect = sim_rule.side_effect
                    if callable(side_effect):
                        return side_effect(*args, **kwargs)
                    elif isinstance(side_effect, list):
                        if side_effect:
                            return side_effect[0](*args, **kwargs)
                    elif isinstance(side_effect, BaseException):
                        raise side_effect
                    elif isinstance(side_effect, type) and issubclass(side_effect, BaseException):
                        raise side_effect()
                    else:
                        raise TypeError("side_effect must be callable, list, or exception")
                return sim_rule.returns_value

            # Preserve Tenro metadata for verification
            if hasattr(original, "_tenro_full_path"):
                wrapper._tenro_full_path = original._tenro_full_path  # type: ignore[attr-defined]
            if hasattr(original, "_tenro_linked_name"):
                wrapper._tenro_linked_name = original._tenro_linked_name  # type: ignore[attr-defined]
            if hasattr(original, "_tenro_linked_type"):
                wrapper._tenro_linked_type = original._tenro_linked_type  # type: ignore[attr-defined]

            return wrapper

        setattr(container, attr_name, make_wrapper(rule))

    def _stop_http_interceptor(self) -> None:
        """Stop HTTP interception."""
        if not self._http_simulation_enabled:
            return
        self._http_interceptor.stop()
        self._http_simulation_enabled = False

    def _stop_patches(self) -> None:
        """Stop active patches.

        Patches are restored in `_restore_originals`, not here.
        """
        pass

    def _restore_originals(self) -> None:
        """Restore patched functions."""
        for tool_name, original in self._originals.items():
            container, attr_name = parse_dotted_path(tool_name)
            setattr(container, attr_name, original)

    def _clear_state(self) -> None:
        """Clear patching state while preserving trace data."""
        self._originals.clear()


__all__ = ["SimulationOrchestrator"]
