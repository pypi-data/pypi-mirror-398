# Copyright 2025 Tenro.ai
# SPDX-License-Identifier: Apache-2.0

"""Decorator-based linking for agents, LLMs, and tools.

Context-aware decorators that register functions with the Tenro system:
- Active Construct: Creates spans for testing and verification.
- No Construct: Executes the function without span tracking.

Features:
- Re-entrancy guard: Internal method delegation creates only one span.
- Multi-method wrapping: Classes get ALL matching entry methods wrapped.
- Framework object support: Patches invoke/run on pre-constructed objects.
- Agent attribution: HTTP interceptor uses span stack for agent correlation.

Examples:
    >>> from tenro import Construct, link_agent
    >>>
    >>> @link_agent("Manager")
    ... def manager_agent(task: str) -> str:
    ...     return worker_agent(task)
    >>>
    >>> @link_agent("WriterAgent")
    ... class WriterAgent:
    ...     async def execute(self, prompt: str) -> str:
    ...         return "result"
    >>>
    >>> with Construct() as construct:
    ...     result = manager_agent("Build feature")
"""

from __future__ import annotations

import inspect
import time
import warnings
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from uuid_utils import uuid7

from tenro.core.spans import AgentRun, LLMScope, ToolCall
from tenro.linking.constants import AGENT_ENTRY_METHODS, TOOL_ENTRY_METHODS
from tenro.linking.context import (
    GuardKey,
    get_active_construct,
    guard_enter,
    guard_exit,
    set_active_construct,
)
from tenro.linking.detection import TargetType, detect_target_type, find_entry_methods
from tenro.linking.generators import wrap_async_generator, wrap_generator

# Type variable for decorated functions
F = TypeVar("F", bound=Callable[..., Any])

# Backward compatibility aliases (used by construct.py)
_get_active_construct = get_active_construct
_set_active_construct = set_active_construct


# =============================================================================
# Agent Wrappers
# =============================================================================


def _wrap_agent_method(method: Callable[..., Any], agent_name: str) -> Callable[..., Any]:
    """Wrap a method with agent span tracking and re-entrancy guard."""
    # Prevent double wrapping
    if getattr(method, "__tenro_wrapped__", False):
        return method

    if inspect.isasyncgenfunction(method):
        # Async generator function - needs async generator wrapper
        @wraps(method)
        async def asyncgen_wrapper(
            self: Any, *args: Any, **kwargs: Any
        ) -> Any:  # Returns AsyncGenerator
            key = GuardKey(kind="agent", target_id=id(self))
            token = guard_enter(key)
            if token is None:
                async for item in method(self, *args, **kwargs):
                    yield item
                return

            construct = get_active_construct()
            if not construct:
                try:
                    async for item in method(self, *args, **kwargs):
                        yield item
                finally:
                    guard_exit(token)
                return

            span = AgentRun(
                id=str(uuid7()),
                trace_id=str(uuid7()),
                start_time=time.time(),
                name=agent_name,
                input_data=args,
            )
            lifecycle = construct._lifecycle
            parent_span_id = lifecycle.start_span_manual(span)

            error: Exception | None = None
            try:
                async for item in method(self, *args, **kwargs):
                    yield item
            except Exception as e:
                error = e
                raise
            finally:
                try:
                    if error is not None:
                        lifecycle.error_span_manual(span, parent_span_id, error)
                    else:
                        lifecycle.end_span_manual(span, parent_span_id)
                finally:
                    guard_exit(token)

        asyncgen_wrapper.__tenro_wrapped__ = True  # type: ignore[attr-defined]
        return asyncgen_wrapper

    if inspect.iscoroutinefunction(method):

        @wraps(method)
        async def async_wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            key = GuardKey(kind="agent", target_id=id(self))
            token = guard_enter(key)
            if token is None:
                return await method(self, *args, **kwargs)  # Re-entry: pass-through

            construct = get_active_construct()
            if not construct:
                try:
                    return await method(self, *args, **kwargs)
                finally:
                    guard_exit(token)

            # Create span and use lifecycle manager directly
            span = AgentRun(
                id=str(uuid7()),
                trace_id=str(uuid7()),
                start_time=time.time(),
                name=agent_name,
                input_data=args,
            )
            lifecycle = construct._lifecycle
            parent_span_id = lifecycle.start_span_manual(span)

            try:
                result = await method(self, *args, **kwargs)
            except Exception as e:
                lifecycle.error_span_manual(span, parent_span_id, e)
                guard_exit(token)
                raise

            # Check for async generator
            if inspect.isasyncgen(result):
                return wrap_async_generator(
                    result, span, parent_span_id, lifecycle, token, guard_exit
                )

            span.output_data = result
            lifecycle.end_span_manual(span, parent_span_id)
            guard_exit(token)
            return result

        async_wrapper.__tenro_wrapped__ = True  # type: ignore[attr-defined]
        return async_wrapper
    else:

        @wraps(method)
        def sync_wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            key = GuardKey(kind="agent", target_id=id(self))
            token = guard_enter(key)
            if token is None:
                return method(self, *args, **kwargs)  # Re-entry: pass-through

            construct = get_active_construct()
            if not construct:
                try:
                    return method(self, *args, **kwargs)
                finally:
                    guard_exit(token)

            # Create span and use lifecycle manager directly
            span = AgentRun(
                id=str(uuid7()),
                trace_id=str(uuid7()),
                start_time=time.time(),
                name=agent_name,
                input_data=args,
            )
            lifecycle = construct._lifecycle
            parent_span_id = lifecycle.start_span_manual(span)

            try:
                result = method(self, *args, **kwargs)
            except Exception as e:
                lifecycle.error_span_manual(span, parent_span_id, e)
                guard_exit(token)
                raise

            # Check for sync generator
            if inspect.isgenerator(result):
                return wrap_generator(result, span, parent_span_id, lifecycle, token, guard_exit)

            span.output_data = result
            lifecycle.end_span_manual(span, parent_span_id)
            guard_exit(token)
            return result

        sync_wrapper.__tenro_wrapped__ = True  # type: ignore[attr-defined]
        return sync_wrapper


def _wrap_agent_function(func: F, agent_name: str) -> F:
    """Wrap a function with agent span tracking and re-entrancy guard."""
    # Prevent double wrapping
    if getattr(func, "__tenro_wrapped__", False):
        return func

    if inspect.isasyncgenfunction(func):
        # Async generator function - needs async generator wrapper
        @wraps(func)
        async def asyncgen_wrapper(*args: Any, **kwargs: Any) -> Any:
            key = GuardKey(kind="agent", target_id=id(func))
            token = guard_enter(key)
            if token is None:
                async for item in func(*args, **kwargs):
                    yield item
                return

            construct = get_active_construct()
            if not construct:
                try:
                    async for item in func(*args, **kwargs):
                        yield item
                finally:
                    guard_exit(token)
                return

            span = AgentRun(
                id=str(uuid7()),
                trace_id=str(uuid7()),
                start_time=time.time(),
                name=agent_name,
                input_data=args,
            )
            lifecycle = construct._lifecycle
            parent_span_id = lifecycle.start_span_manual(span)

            error: Exception | None = None
            try:
                async for item in func(*args, **kwargs):
                    yield item
            except Exception as e:
                error = e
                raise
            finally:
                try:
                    if error is not None:
                        lifecycle.error_span_manual(span, parent_span_id, error)
                    else:
                        lifecycle.end_span_manual(span, parent_span_id)
                finally:
                    guard_exit(token)

        asyncgen_wrapper.__tenro_wrapped__ = True  # type: ignore[attr-defined]
        asyncgen_wrapper._tenro_linked_type = "agent"  # type: ignore[attr-defined]
        asyncgen_wrapper._tenro_linked_name = agent_name  # type: ignore[attr-defined]
        asyncgen_wrapper._tenro_full_path = f"{func.__module__}.{func.__name__}"  # type: ignore[attr-defined]
        asyncgen_wrapper.run = asyncgen_wrapper  # type: ignore[attr-defined]
        return asyncgen_wrapper  # type: ignore[return-value]

    if inspect.iscoroutinefunction(func):

        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            key = GuardKey(kind="agent", target_id=id(func))
            token = guard_enter(key)
            if token is None:
                return await func(*args, **kwargs)  # Re-entry: pass-through

            construct = get_active_construct()
            if not construct:
                try:
                    return await func(*args, **kwargs)
                finally:
                    guard_exit(token)

            # Create span and use lifecycle manager directly
            span = AgentRun(
                id=str(uuid7()),
                trace_id=str(uuid7()),
                start_time=time.time(),
                name=agent_name,
                input_data=args,
            )
            lifecycle = construct._lifecycle
            parent_span_id = lifecycle.start_span_manual(span)

            try:
                result = await func(*args, **kwargs)
            except Exception as e:
                lifecycle.error_span_manual(span, parent_span_id, e)
                guard_exit(token)
                raise

            # Check for async generator
            if inspect.isasyncgen(result):
                return wrap_async_generator(
                    result, span, parent_span_id, lifecycle, token, guard_exit
                )

            span.output_data = result
            lifecycle.end_span_manual(span, parent_span_id)
            guard_exit(token)
            return result

        async_wrapper.__tenro_wrapped__ = True  # type: ignore[attr-defined]
        async_wrapper._tenro_linked_type = "agent"  # type: ignore[attr-defined]
        async_wrapper._tenro_linked_name = agent_name  # type: ignore[attr-defined]
        async_wrapper._tenro_full_path = f"{func.__module__}.{func.__name__}"  # type: ignore[attr-defined]
        async_wrapper.run = async_wrapper  # type: ignore[attr-defined]
        return async_wrapper  # type: ignore[return-value]
    else:

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            key = GuardKey(kind="agent", target_id=id(func))
            token = guard_enter(key)
            if token is None:
                return func(*args, **kwargs)  # Re-entry: pass-through

            construct = get_active_construct()
            if not construct:
                try:
                    return func(*args, **kwargs)
                finally:
                    guard_exit(token)

            # Create span and use lifecycle manager directly
            span = AgentRun(
                id=str(uuid7()),
                trace_id=str(uuid7()),
                start_time=time.time(),
                name=agent_name,
                input_data=args,
            )
            lifecycle = construct._lifecycle
            parent_span_id = lifecycle.start_span_manual(span)

            try:
                result = func(*args, **kwargs)
            except Exception as e:
                lifecycle.error_span_manual(span, parent_span_id, e)
                guard_exit(token)
                raise

            # Check for sync generator
            if inspect.isgenerator(result):
                return wrap_generator(result, span, parent_span_id, lifecycle, token, guard_exit)

            span.output_data = result
            lifecycle.end_span_manual(span, parent_span_id)
            guard_exit(token)
            return result

        sync_wrapper.__tenro_wrapped__ = True  # type: ignore[attr-defined]
        sync_wrapper._tenro_linked_type = "agent"  # type: ignore[attr-defined]
        sync_wrapper._tenro_linked_name = agent_name  # type: ignore[attr-defined]
        sync_wrapper._tenro_full_path = f"{func.__module__}.{func.__name__}"  # type: ignore[attr-defined]
        sync_wrapper.run = sync_wrapper  # type: ignore[attr-defined]
        return sync_wrapper  # type: ignore[return-value]


def _decorate_agent_class(cls: type, agent_name: str, explicit_method: str | None) -> type:
    """Decorate a class by wrapping all matching entry methods."""
    if explicit_method is not None:
        if not hasattr(cls, explicit_method):
            raise ValueError(
                f"@link_agent('{agent_name}', method='{explicit_method}'): "
                f"class has no method '{explicit_method}'"
            )
        methods_to_wrap = [explicit_method]
    else:
        methods_to_wrap = find_entry_methods(cls, AGENT_ENTRY_METHODS)

    if not methods_to_wrap:
        raise ValueError(
            f"@link_agent('{cls.__name__}'): could not find entry method.\n"
            f"Expected one of: {', '.join(sorted(AGENT_ENTRY_METHODS))}\n"
            f"Either add one of these methods or specify explicitly:\n"
            f"  @link_agent('{cls.__name__}', method='your_method')"
        )

    wrapped_methods: list[str] = []
    for method_name in methods_to_wrap:
        original = getattr(cls, method_name)
        wrapped = _wrap_agent_method(original, agent_name)
        try:
            setattr(cls, method_name, wrapped)
            wrapped_methods.append(method_name)
        except (TypeError, AttributeError) as e:
            warnings.warn(
                f"Tenro: Cannot wrap {cls.__name__}.{method_name}: {e}. "
                "Extended tracing unavailable.",
                stacklevel=3,
            )

    cls._tenro_linked_type = "agent"  # type: ignore[attr-defined]
    cls._tenro_linked_name = agent_name  # type: ignore[attr-defined]
    cls._tenro_linked_methods = tuple(wrapped_methods)  # type: ignore[attr-defined]
    return cls


def _patch_agent_object(obj: object, agent_name: str) -> object:
    """Patch entry methods on a framework object instance."""
    patched_any = False
    for method_name in AGENT_ENTRY_METHODS:
        original = getattr(obj, method_name, None)
        if original is None or not callable(original):
            continue

        wrapped = _make_agent_object_wrapper(original, agent_name, obj)
        try:
            setattr(obj, method_name, wrapped)
            patched_any = True
        except (TypeError, AttributeError) as e:
            warnings.warn(
                f"Tenro: Cannot patch {type(obj).__name__}.{method_name}: {e}. "
                "Extended tracing unavailable.",
                stacklevel=3,
            )

    if not patched_any:
        raise ValueError(
            f"@link_agent('{agent_name}'): could not find entry method on {type(obj).__name__}"
        )

    return obj


def _make_agent_object_wrapper(
    original: Callable[..., Any], agent_name: str, obj: object
) -> Callable[..., Any]:
    """Create wrapper for framework object method."""
    # Prevent double wrapping
    if getattr(original, "__tenro_wrapped__", False):
        return original

    if inspect.isasyncgenfunction(original):
        # Async generator function
        @wraps(original)
        async def asyncgen_wrapper(*args: Any, **kwargs: Any) -> Any:
            key = GuardKey(kind="agent", target_id=id(obj))
            token = guard_enter(key)
            if token is None:
                async for item in original(*args, **kwargs):
                    yield item
                return

            construct = get_active_construct()
            if not construct:
                try:
                    async for item in original(*args, **kwargs):
                        yield item
                finally:
                    guard_exit(token)
                return

            span = AgentRun(
                id=str(uuid7()),
                trace_id=str(uuid7()),
                start_time=time.time(),
                name=agent_name,
                input_data=args,
            )
            lifecycle = construct._lifecycle
            parent_span_id = lifecycle.start_span_manual(span)

            error: Exception | None = None
            try:
                async for item in original(*args, **kwargs):
                    yield item
            except Exception as e:
                error = e
                raise
            finally:
                try:
                    if error is not None:
                        lifecycle.error_span_manual(span, parent_span_id, error)
                    else:
                        lifecycle.end_span_manual(span, parent_span_id)
                finally:
                    guard_exit(token)

        asyncgen_wrapper.__tenro_wrapped__ = True  # type: ignore[attr-defined]
        return asyncgen_wrapper

    if inspect.iscoroutinefunction(original):

        @wraps(original)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            key = GuardKey(kind="agent", target_id=id(obj))
            token = guard_enter(key)
            if token is None:
                return await original(*args, **kwargs)

            construct = get_active_construct()
            if not construct:
                try:
                    return await original(*args, **kwargs)
                finally:
                    guard_exit(token)

            # Create span and use lifecycle manager directly
            span = AgentRun(
                id=str(uuid7()),
                trace_id=str(uuid7()),
                start_time=time.time(),
                name=agent_name,
                input_data=args,
            )
            lifecycle = construct._lifecycle
            parent_span_id = lifecycle.start_span_manual(span)

            try:
                result = await original(*args, **kwargs)
            except Exception as e:
                lifecycle.error_span_manual(span, parent_span_id, e)
                guard_exit(token)
                raise

            # Check for async generator
            if inspect.isasyncgen(result):
                return wrap_async_generator(
                    result, span, parent_span_id, lifecycle, token, guard_exit
                )

            span.output_data = result
            lifecycle.end_span_manual(span, parent_span_id)
            guard_exit(token)
            return result

        async_wrapper.__tenro_wrapped__ = True  # type: ignore[attr-defined]
        return async_wrapper
    else:

        @wraps(original)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            key = GuardKey(kind="agent", target_id=id(obj))
            token = guard_enter(key)
            if token is None:
                return original(*args, **kwargs)

            construct = get_active_construct()
            if not construct:
                try:
                    return original(*args, **kwargs)
                finally:
                    guard_exit(token)

            # Create span and use lifecycle manager directly
            span = AgentRun(
                id=str(uuid7()),
                trace_id=str(uuid7()),
                start_time=time.time(),
                name=agent_name,
                input_data=args,
            )
            lifecycle = construct._lifecycle
            parent_span_id = lifecycle.start_span_manual(span)

            try:
                result = original(*args, **kwargs)
            except Exception as e:
                lifecycle.error_span_manual(span, parent_span_id, e)
                guard_exit(token)
                raise

            # Check for sync generator
            if inspect.isgenerator(result):
                return wrap_generator(result, span, parent_span_id, lifecycle, token, guard_exit)

            span.output_data = result
            lifecycle.end_span_manual(span, parent_span_id)
            guard_exit(token)
            return result

        sync_wrapper.__tenro_wrapped__ = True  # type: ignore[attr-defined]
        return sync_wrapper


# =============================================================================
# Tool Wrappers
# =============================================================================


def _wrap_tool_function(func: F, tool_name: str) -> F:
    """Wrap a function with tool span tracking and re-entrancy guard."""
    # Prevent double wrapping
    if getattr(func, "__tenro_wrapped__", False):
        return func

    if inspect.isasyncgenfunction(func):
        # Async generator function
        @wraps(func)
        async def asyncgen_wrapper(*args: Any, **kwargs: Any) -> Any:
            key = GuardKey(kind="tool", target_id=id(func))
            token = guard_enter(key)
            if token is None:
                async for item in func(*args, **kwargs):
                    yield item
                return

            construct = get_active_construct()
            if not construct:
                try:
                    async for item in func(*args, **kwargs):
                        yield item
                finally:
                    guard_exit(token)
                return

            span = ToolCall(
                id=str(uuid7()),
                trace_id=str(uuid7()),
                start_time=time.time(),
                tool_name=tool_name,
                args=args,
                kwargs=kwargs,
            )
            lifecycle = construct._lifecycle
            parent_span_id = lifecycle.start_span_manual(span)

            error: Exception | None = None
            try:
                async for item in func(*args, **kwargs):
                    yield item
            except Exception as e:
                error = e
                raise
            finally:
                try:
                    if error is not None:
                        lifecycle.error_span_manual(span, parent_span_id, error)
                    else:
                        lifecycle.end_span_manual(span, parent_span_id)
                finally:
                    guard_exit(token)

        asyncgen_wrapper.__tenro_wrapped__ = True  # type: ignore[attr-defined]
        asyncgen_wrapper._tenro_linked_type = "tool"  # type: ignore[attr-defined]
        asyncgen_wrapper._tenro_linked_name = tool_name  # type: ignore[attr-defined]
        asyncgen_wrapper._tenro_full_path = f"{func.__module__}.{func.__name__}"  # type: ignore[attr-defined]
        return asyncgen_wrapper  # type: ignore[return-value]

    if inspect.iscoroutinefunction(func):

        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            key = GuardKey(kind="tool", target_id=id(func))
            token = guard_enter(key)
            if token is None:
                return await func(*args, **kwargs)

            construct = get_active_construct()
            if not construct:
                try:
                    return await func(*args, **kwargs)
                finally:
                    guard_exit(token)

            # Create span and use lifecycle manager directly
            span = ToolCall(
                id=str(uuid7()),
                trace_id=str(uuid7()),
                start_time=time.time(),
                tool_name=tool_name,
                args=args,
                kwargs=kwargs,
            )
            lifecycle = construct._lifecycle
            parent_span_id = lifecycle.start_span_manual(span)

            try:
                result = await func(*args, **kwargs)
            except Exception as e:
                lifecycle.error_span_manual(span, parent_span_id, e)
                guard_exit(token)
                raise

            # Check for async generator
            if inspect.isasyncgen(result):
                return wrap_async_generator(
                    result, span, parent_span_id, lifecycle, token, guard_exit
                )

            span.result = result
            lifecycle.end_span_manual(span, parent_span_id)
            guard_exit(token)
            return result

        async_wrapper.__tenro_wrapped__ = True  # type: ignore[attr-defined]
        async_wrapper._tenro_linked_type = "tool"  # type: ignore[attr-defined]
        async_wrapper._tenro_linked_name = tool_name  # type: ignore[attr-defined]
        async_wrapper._tenro_full_path = f"{func.__module__}.{func.__name__}"  # type: ignore[attr-defined]
        return async_wrapper  # type: ignore[return-value]
    else:

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            key = GuardKey(kind="tool", target_id=id(func))
            token = guard_enter(key)
            if token is None:
                return func(*args, **kwargs)

            construct = get_active_construct()
            if not construct:
                try:
                    return func(*args, **kwargs)
                finally:
                    guard_exit(token)

            # Create span and use lifecycle manager directly
            span = ToolCall(
                id=str(uuid7()),
                trace_id=str(uuid7()),
                start_time=time.time(),
                tool_name=tool_name,
                args=args,
                kwargs=kwargs,
            )
            lifecycle = construct._lifecycle
            parent_span_id = lifecycle.start_span_manual(span)

            try:
                result = func(*args, **kwargs)
            except Exception as e:
                lifecycle.error_span_manual(span, parent_span_id, e)
                guard_exit(token)
                raise

            # Check for sync generator
            if inspect.isgenerator(result):
                return wrap_generator(result, span, parent_span_id, lifecycle, token, guard_exit)

            span.result = result
            lifecycle.end_span_manual(span, parent_span_id)
            guard_exit(token)
            return result

        sync_wrapper.__tenro_wrapped__ = True  # type: ignore[attr-defined]
        sync_wrapper._tenro_linked_type = "tool"  # type: ignore[attr-defined]
        sync_wrapper._tenro_linked_name = tool_name  # type: ignore[attr-defined]
        sync_wrapper._tenro_full_path = f"{func.__module__}.{func.__name__}"  # type: ignore[attr-defined]
        return sync_wrapper  # type: ignore[return-value]


def _wrap_tool_method(method: Callable[..., Any], tool_name: str) -> Callable[..., Any]:
    """Wrap a method with tool span tracking and re-entrancy guard."""
    # Prevent double wrapping
    if getattr(method, "__tenro_wrapped__", False):
        return method

    if inspect.isasyncgenfunction(method):
        # Async generator function
        @wraps(method)
        async def asyncgen_wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            key = GuardKey(kind="tool", target_id=id(self))
            token = guard_enter(key)
            if token is None:
                async for item in method(self, *args, **kwargs):
                    yield item
                return

            construct = get_active_construct()
            if not construct:
                try:
                    async for item in method(self, *args, **kwargs):
                        yield item
                finally:
                    guard_exit(token)
                return

            span = ToolCall(
                id=str(uuid7()),
                trace_id=str(uuid7()),
                start_time=time.time(),
                tool_name=tool_name,
                args=args,
                kwargs=kwargs,
            )
            lifecycle = construct._lifecycle
            parent_span_id = lifecycle.start_span_manual(span)

            error: Exception | None = None
            try:
                async for item in method(self, *args, **kwargs):
                    yield item
            except Exception as e:
                error = e
                raise
            finally:
                try:
                    if error is not None:
                        lifecycle.error_span_manual(span, parent_span_id, error)
                    else:
                        lifecycle.end_span_manual(span, parent_span_id)
                finally:
                    guard_exit(token)

        asyncgen_wrapper.__tenro_wrapped__ = True  # type: ignore[attr-defined]
        return asyncgen_wrapper

    if inspect.iscoroutinefunction(method):

        @wraps(method)
        async def async_wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            key = GuardKey(kind="tool", target_id=id(self))
            token = guard_enter(key)
            if token is None:
                return await method(self, *args, **kwargs)

            construct = get_active_construct()
            if not construct:
                try:
                    return await method(self, *args, **kwargs)
                finally:
                    guard_exit(token)

            # Create span and use lifecycle manager directly
            span = ToolCall(
                id=str(uuid7()),
                trace_id=str(uuid7()),
                start_time=time.time(),
                tool_name=tool_name,
                args=args,
                kwargs=kwargs,
            )
            lifecycle = construct._lifecycle
            parent_span_id = lifecycle.start_span_manual(span)

            try:
                result = await method(self, *args, **kwargs)
            except Exception as e:
                lifecycle.error_span_manual(span, parent_span_id, e)
                guard_exit(token)
                raise

            # Check for async generator
            if inspect.isasyncgen(result):
                return wrap_async_generator(
                    result, span, parent_span_id, lifecycle, token, guard_exit
                )

            span.result = result
            lifecycle.end_span_manual(span, parent_span_id)
            guard_exit(token)
            return result

        async_wrapper.__tenro_wrapped__ = True  # type: ignore[attr-defined]
        return async_wrapper
    else:

        @wraps(method)
        def sync_wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            key = GuardKey(kind="tool", target_id=id(self))
            token = guard_enter(key)
            if token is None:
                return method(self, *args, **kwargs)

            construct = get_active_construct()
            if not construct:
                try:
                    return method(self, *args, **kwargs)
                finally:
                    guard_exit(token)

            # Create span and use lifecycle manager directly
            span = ToolCall(
                id=str(uuid7()),
                trace_id=str(uuid7()),
                start_time=time.time(),
                tool_name=tool_name,
                args=args,
                kwargs=kwargs,
            )
            lifecycle = construct._lifecycle
            parent_span_id = lifecycle.start_span_manual(span)

            try:
                result = method(self, *args, **kwargs)
            except Exception as e:
                lifecycle.error_span_manual(span, parent_span_id, e)
                guard_exit(token)
                raise

            # Check for sync generator
            if inspect.isgenerator(result):
                return wrap_generator(result, span, parent_span_id, lifecycle, token, guard_exit)

            span.result = result
            lifecycle.end_span_manual(span, parent_span_id)
            guard_exit(token)
            return result

        sync_wrapper.__tenro_wrapped__ = True  # type: ignore[attr-defined]
        return sync_wrapper


def _decorate_tool_class(cls: type, tool_name: str) -> type:
    """Decorate a class by wrapping all matching tool entry methods."""
    methods_to_wrap = find_entry_methods(cls, TOOL_ENTRY_METHODS)

    if not methods_to_wrap:
        raise ValueError(
            f"@link_tool('{tool_name}'): could not find entry method on "
            f"{cls.__name__}.\nExpected one of: {', '.join(sorted(TOOL_ENTRY_METHODS))}"
        )

    wrapped_methods: list[str] = []
    for method_name in methods_to_wrap:
        original = getattr(cls, method_name)
        wrapped = _wrap_tool_method(original, tool_name)
        try:
            setattr(cls, method_name, wrapped)
            wrapped_methods.append(method_name)
        except (TypeError, AttributeError) as e:
            warnings.warn(
                f"Tenro: Cannot wrap {cls.__name__}.{method_name}: {e}. "
                "Extended tracing unavailable.",
                stacklevel=3,
            )

    cls._tenro_linked_type = "tool"  # type: ignore[attr-defined]
    cls._tenro_linked_name = tool_name  # type: ignore[attr-defined]
    cls._tenro_linked_methods = tuple(wrapped_methods)  # type: ignore[attr-defined]
    return cls


def _patch_tool_object(obj: object, tool_name: str) -> object:
    """Patch entry methods on a framework tool object instance."""
    patched_any = False
    for method_name in TOOL_ENTRY_METHODS:
        original = getattr(obj, method_name, None)
        if original is None or not callable(original):
            continue

        wrapped = _make_tool_object_wrapper(original, tool_name, obj)
        try:
            setattr(obj, method_name, wrapped)
            patched_any = True
        except (TypeError, AttributeError) as e:
            warnings.warn(
                f"Tenro: Cannot patch {type(obj).__name__}.{method_name}: {e}. "
                "Extended tracing unavailable.",
                stacklevel=3,
            )

    if not patched_any:
        raise ValueError(
            f"@link_tool('{tool_name}'): could not find entry method on {type(obj).__name__}"
        )

    return obj


def _make_tool_object_wrapper(
    original: Callable[..., Any], tool_name: str, obj: object
) -> Callable[..., Any]:
    """Create wrapper for framework tool object method."""
    # Prevent double wrapping
    if getattr(original, "__tenro_wrapped__", False):
        return original

    if inspect.isasyncgenfunction(original):
        # Async generator function
        @wraps(original)
        async def asyncgen_wrapper(*args: Any, **kwargs: Any) -> Any:
            key = GuardKey(kind="tool", target_id=id(obj))
            token = guard_enter(key)
            if token is None:
                async for item in original(*args, **kwargs):
                    yield item
                return

            construct = get_active_construct()
            if not construct:
                try:
                    async for item in original(*args, **kwargs):
                        yield item
                finally:
                    guard_exit(token)
                return

            span = ToolCall(
                id=str(uuid7()),
                trace_id=str(uuid7()),
                start_time=time.time(),
                tool_name=tool_name,
                args=args,
                kwargs=kwargs,
            )
            lifecycle = construct._lifecycle
            parent_span_id = lifecycle.start_span_manual(span)

            error: Exception | None = None
            try:
                async for item in original(*args, **kwargs):
                    yield item
            except Exception as e:
                error = e
                raise
            finally:
                try:
                    if error is not None:
                        lifecycle.error_span_manual(span, parent_span_id, error)
                    else:
                        lifecycle.end_span_manual(span, parent_span_id)
                finally:
                    guard_exit(token)

        asyncgen_wrapper.__tenro_wrapped__ = True  # type: ignore[attr-defined]
        return asyncgen_wrapper

    if inspect.iscoroutinefunction(original):

        @wraps(original)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            key = GuardKey(kind="tool", target_id=id(obj))
            token = guard_enter(key)
            if token is None:
                return await original(*args, **kwargs)

            construct = get_active_construct()
            if not construct:
                try:
                    return await original(*args, **kwargs)
                finally:
                    guard_exit(token)

            # Create span and use lifecycle manager directly
            span = ToolCall(
                id=str(uuid7()),
                trace_id=str(uuid7()),
                start_time=time.time(),
                tool_name=tool_name,
                args=args,
                kwargs=kwargs,
            )
            lifecycle = construct._lifecycle
            parent_span_id = lifecycle.start_span_manual(span)

            try:
                result = await original(*args, **kwargs)
            except Exception as e:
                lifecycle.error_span_manual(span, parent_span_id, e)
                guard_exit(token)
                raise

            # Check for async generator
            if inspect.isasyncgen(result):
                return wrap_async_generator(
                    result, span, parent_span_id, lifecycle, token, guard_exit
                )

            span.result = result
            lifecycle.end_span_manual(span, parent_span_id)
            guard_exit(token)
            return result

        async_wrapper.__tenro_wrapped__ = True  # type: ignore[attr-defined]
        return async_wrapper
    else:

        @wraps(original)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            key = GuardKey(kind="tool", target_id=id(obj))
            token = guard_enter(key)
            if token is None:
                return original(*args, **kwargs)

            construct = get_active_construct()
            if not construct:
                try:
                    return original(*args, **kwargs)
                finally:
                    guard_exit(token)

            # Create span and use lifecycle manager directly
            span = ToolCall(
                id=str(uuid7()),
                trace_id=str(uuid7()),
                start_time=time.time(),
                tool_name=tool_name,
                args=args,
                kwargs=kwargs,
            )
            lifecycle = construct._lifecycle
            parent_span_id = lifecycle.start_span_manual(span)

            try:
                result = original(*args, **kwargs)
            except Exception as e:
                lifecycle.error_span_manual(span, parent_span_id, e)
                guard_exit(token)
                raise

            # Check for sync generator
            if inspect.isgenerator(result):
                return wrap_generator(result, span, parent_span_id, lifecycle, token, guard_exit)

            span.result = result
            lifecycle.end_span_manual(span, parent_span_id)
            guard_exit(token)
            return result

        sync_wrapper.__tenro_wrapped__ = True  # type: ignore[attr-defined]
        return sync_wrapper


# =============================================================================
# Public Decorators
# =============================================================================


def link_agent(
    name: str | None = None,
    *,
    method: str | None = None,
) -> Callable[..., Any]:
    """Decorator to register agent functions, classes, or objects with Tenro.

    When a Construct is active, the decorator records an agent span. Otherwise,
    the function/method executes normally.

    Supports:
    - Sync and async functions
    - Classes with auto-detected entry methods (or explicit via method=)
    - Framework objects (patches invoke/run methods)

    For classes, the decorator wraps ALL matching entry methods with a
    re-entrancy guard, so internal delegation (e.g., invoke → stream)
    creates only one span.

    Args:
        name: Agent name for the span. If None, uses function/class name.
        method: For classes only. Explicit method name to wrap. If None,
            auto-detects from AGENT_ENTRY_METHODS.

    Returns:
        Decorated target that registers with active Construct.

    Raises:
        ValueError: If decorating a class and no entry method is found.

    Examples:
        >>> @link_agent("PlannerBot")
        ... def plan_trip(destination: str) -> str:
        ...     return agent.run(destination)
        >>>
        >>> @link_agent("WriterAgent")
        ... class WriterAgent:
        ...     async def execute(self, prompt: str) -> str:
        ...         return "result"
    """

    def decorator(target: Any) -> Any:
        target_type = detect_target_type(target)
        agent_name: str = name if name else getattr(target, "__name__", None) or str(target)

        if target_type == TargetType.CLASS:
            return _decorate_agent_class(target, agent_name, method)
        elif target_type == TargetType.FRAMEWORK_OBJECT:
            return _patch_agent_object(target, agent_name)
        else:
            return _wrap_agent_function(target, agent_name)

    return decorator


def link_llm(provider: str, model: str | None = None) -> Callable[[F], F]:
    """Decorator to mark functions as LLM call boundaries.

    Creates an LLMScope (transparent annotation span) when a Construct is active.
    HTTP interception will create LLMCall spans inside this scope. The scope
    captures caller info for debugging but is transparent for parent attribution.

    Args:
        provider: LLM provider (e.g., "openai", "anthropic").
        model: Model identifier (e.g., "gpt-4", "claude-3").

    Returns:
        Decorated function that creates LLMScope when Construct is active.

    Examples:
        >>> @link_llm("openai", model="gpt-4")
        ... def call_llm(prompt: str) -> str:
        ...     return client.chat.completions.create(...)
    """

    def decorator(func: F) -> F:
        sig = inspect.signature(func)
        caller_signature = f"{func.__qualname__}{sig}"
        try:
            file = inspect.getsourcefile(func) or inspect.getfile(func)
            line = inspect.getsourcelines(func)[1]
            caller_location: str | None = f"{file}:{line}"
        except (OSError, TypeError):
            caller_location = None

        if inspect.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                construct = get_active_construct()
                if not construct:
                    return await func(*args, **kwargs)

                # Create LLMScope - transparent annotation span
                scope = LLMScope(
                    id=str(uuid7()),
                    trace_id=str(uuid7()),
                    start_time=time.time(),
                    provider=provider,
                    model=model,
                    caller_signature=caller_signature,
                    caller_location=caller_location,
                )
                with construct._lifecycle.start_span(scope):
                    return await func(*args, **kwargs)

            return async_wrapper  # type: ignore[return-value]
        else:

            @wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                construct = get_active_construct()
                if not construct:
                    return func(*args, **kwargs)

                # Create LLMScope - transparent annotation span
                scope = LLMScope(
                    id=str(uuid7()),
                    trace_id=str(uuid7()),
                    start_time=time.time(),
                    provider=provider,
                    model=model,
                    caller_signature=caller_signature,
                    caller_location=caller_location,
                )
                with construct._lifecycle.start_span(scope):
                    return func(*args, **kwargs)

            return sync_wrapper  # type: ignore[return-value]

    return decorator


def link_tool(name: str | None = None) -> Callable[..., Any]:
    """Decorator to register tool functions, classes, or objects with Tenro.

    When a Construct is active, the decorator records a tool span. Otherwise,
    the function executes normally.

    Supports:
    - Sync and async functions
    - Classes with auto-detected entry methods
    - Framework objects (patches invoke/run methods)

    Args:
        name: Tool name for the span. If None, uses function/class name.

    Returns:
        Decorated target that registers with active Construct.

    Examples:
        >>> @link_tool("search")
        ... def search(query: str) -> list[str]:
        ...     return ["result1", "result2"]
        >>>
        >>> @link_tool("calculator")
        ... class Calculator:
        ...     def invoke(self, expr: str) -> int:
        ...         return eval(expr)
    """

    def decorator(target: Any) -> Any:
        target_type = detect_target_type(target)
        tool_name: str = name if name else getattr(target, "__name__", None) or str(target)

        if target_type == TargetType.CLASS:
            return _decorate_tool_class(target, tool_name)
        elif target_type == TargetType.FRAMEWORK_OBJECT:
            return _patch_tool_object(target, tool_name)
        else:
            return _wrap_tool_function(target, tool_name)

    return decorator


__all__ = [
    "link_agent",
    "link_llm",
    "link_tool",
    "_get_active_construct",
    "_set_active_construct",
]
