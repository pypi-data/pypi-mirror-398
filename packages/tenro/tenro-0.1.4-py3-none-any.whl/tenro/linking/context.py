# Copyright 2025 Tenro.ai
# SPDX-License-Identifier: Apache-2.0

"""ContextVars for linking decorators.

Consolidates linking-related context: active construct and re-entrancy guards.
Agent attribution uses span stack in core/context.py (get_current_agent_name).
Kept separate from core/context.py to avoid circular imports.

See docs-private/linking.md for design rationale.
"""

from __future__ import annotations

from contextvars import ContextVar, Token
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tenro.construct.construct import Construct

# Active construct for decorator access
_active_construct: ContextVar[Construct | None] = ContextVar("active_construct", default=None)


@dataclass(frozen=True)
class GuardKey:
    """Key for re-entrancy guard.

    Uses target_id (id of self for methods, id of func for functions) plus
    kind to ensure different decorator types don't interfere.

    Example: Agent.invoke() internally calls Agent.stream() - same GuardKey
    so stream() becomes a pass-through (no duplicate span).
    """

    kind: str  # "agent" | "tool"
    target_id: int  # id(self) for methods, id(func) for functions


# Keyed guard: only suppresses same-boundary re-entry
_active_guards: ContextVar[frozenset[GuardKey]] = ContextVar("tenro_guards", default=frozenset())


def guard_enter(key: GuardKey) -> Token[frozenset[GuardKey]] | None:
    """Attempt to acquire re-entrancy guard.

    Args:
        key: Guard key identifying the re-entrancy boundary.

    Returns:
        Token if guard acquired (caller should create span).
        None if already active (re-entry, caller should pass-through).
    """
    guards = _active_guards.get()
    if key in guards:
        return None  # Re-entry: suppress
    return _active_guards.set(guards | {key})


def guard_exit(token: Token[frozenset[GuardKey]] | None) -> None:
    """Release a re-entrancy guard.

    Args:
        token: Guard token from `guard_enter`, or None if guard was not acquired.
    """
    if token is not None:
        try:  # noqa: SIM105
            _active_guards.reset(token)
        except ValueError:
            pass  # Token invalid in this context (async generator cleanup)


def get_active_construct() -> Construct | None:
    """Get the currently active construct from context."""
    return _active_construct.get()


def set_active_construct(construct: Construct | None) -> None:
    """Set the active construct in context."""
    _active_construct.set(construct)


__all__ = [
    "GuardKey",
    "guard_enter",
    "guard_exit",
    "get_active_construct",
    "set_active_construct",
]
