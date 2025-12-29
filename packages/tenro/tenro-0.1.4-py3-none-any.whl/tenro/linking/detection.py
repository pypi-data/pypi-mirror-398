# Copyright 2025 Tenro.ai
# SPDX-License-Identifier: Apache-2.0

"""Target type detection for linking decorators.

Classifies decorator targets as FUNCTION, CLASS, or FRAMEWORK_OBJECT
to determine the appropriate wrapping strategy.

See docs-private/linking.md for detection flow diagrams.
"""

from __future__ import annotations

import inspect
from enum import Enum, auto
from typing import Any


class TargetType(Enum):
    """Classification of decorator target."""

    FUNCTION = auto()
    CLASS = auto()
    FRAMEWORK_OBJECT = auto()


def detect_target_type(target: Any) -> TargetType:
    """Detect the type of decorator target.

    Detection priority:
    1. isclass -> CLASS
    2. Has callable invoke/run method -> FRAMEWORK_OBJECT
    3. callable -> FUNCTION

    Args:
        target: The decorated target (function, class, or object).

    Returns:
        TargetType classification.

    Raises:
        TypeError: If target is not callable.
    """
    if inspect.isclass(target):
        return TargetType.CLASS

    if _is_framework_object(target):
        return TargetType.FRAMEWORK_OBJECT

    if callable(target):
        return TargetType.FUNCTION

    raise TypeError(f"Cannot decorate {type(target).__name__}: not callable")


def _is_framework_object(target: Any) -> bool:
    """Check if target is a framework object (e.g., LangChain StructuredTool).

    Framework objects are instances (not classes) that have callable
    invoke/run methods, indicating they're pre-constructed tools/agents.
    """
    # Must not be a class itself
    if inspect.isclass(target):
        return False

    # Check for common entry methods that indicate a framework tool/agent
    for method_name in ("invoke", "run", "_run"):
        method = getattr(target, method_name, None)
        if method is not None and callable(method):
            return True
    return False


def find_entry_methods(cls: type, entry_methods: frozenset[str]) -> list[str]:
    """Find all entry methods on a class from the given set.

    Uses getattr to follow MRO (finds inherited methods).
    Only returns methods that are callable.

    Args:
        cls: The class to search.
        entry_methods: Set of method names to look for.

    Returns:
        List of found method names (may be empty).
    """
    found: list[str] = []
    for method_name in entry_methods:
        attr = getattr(cls, method_name, None)
        if attr is not None and callable(attr):
            # Skip inherited object.__call__ if not explicitly defined
            if method_name == "__call__" and not _is_explicitly_defined(cls, method_name):
                continue
            found.append(method_name)
    return found


def _is_explicitly_defined(cls: type, method_name: str) -> bool:
    """Check if a method is explicitly defined (not inherited from object/type)."""
    for klass in cls.__mro__:
        if method_name in klass.__dict__:
            return klass is cls or klass not in (object, type)
    return False


__all__ = [
    "TargetType",
    "detect_target_type",
    "find_entry_methods",
]
