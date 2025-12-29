# Copyright 2025 Tenro.ai
# SPDX-License-Identifier: Apache-2.0

"""Target resolution utilities for simulation.

Handles validation and resolution of simulation targets (functions, methods, paths).
"""

from __future__ import annotations

import sys
from typing import Any


def validate_and_resolve_target(target: Any, expected_type: str) -> str:
    """Validate callable target and return path for simulation.

    Accepts string paths, unbound class methods, or decorated functions.

    Args:
        target: Target to validate (string path or callable object).
        expected_type: Expected link type ("tool", "agent", "llm").

    Returns:
        String path to use for simulation.

    Raises:
        ValueError: If target is an undecorated module-level function.
    """
    if not callable(target) or isinstance(target, str):
        return str(target)

    # Handle @classmethod (bound method descriptor with __func__)
    if hasattr(target, "__func__"):
        qualname = getattr(target.__func__, "__qualname__", "")
        if _is_class_method(qualname):
            module = getattr(target.__func__, "__module__", None)
            return f"{module}.{qualname}" if module else qualname

    # Handle instance methods and @staticmethod
    qualname = getattr(target, "__qualname__", "")
    if _is_class_method(qualname):
        module = getattr(target, "__module__", None)
        return f"{module}.{qualname}" if module else qualname

    # Decorated function - must have metadata
    if not hasattr(target, "_tenro_linked_type"):
        func_name = getattr(target, "__name__", str(target))
        raise ValueError(_build_undecorated_error_message(func_name, expected_type))

    # Validate decorator type matches
    link_type: str = target._tenro_linked_type

    if link_type != expected_type:
        msg = (
            f"Cannot use simulate_{expected_type}() with @link_{link_type} "
            f"decorated function.\n"
            f"Use construct.simulate_{link_type}() instead."
        )
        raise ValueError(msg)

    # Return full module path for patching
    full_path: str = getattr(target, "_tenro_full_path", "")
    if full_path:
        return full_path

    # Fallback to link_name (shouldn't happen with updated decorators)
    link_name: str = target._tenro_linked_name
    return link_name


def resolve_target_for_verification(target: Any) -> str:
    """Resolve a target to a name string for verification filtering.

    Unlike validate_and_resolve_target, this doesn't require decorators
    and is used for verify_* calls.

    Args:
        target: Target to resolve (string or callable).

    Returns:
        String name to use for filtering.
    """
    if isinstance(target, str):
        return target

    if callable(target):
        # Check for decorated function with full path
        if hasattr(target, "_tenro_full_path"):
            return str(target._tenro_full_path)

        # Check for class method
        qualname = getattr(target, "__qualname__", "")
        if _is_class_method(qualname):
            module = getattr(target, "__module__", None)
            return f"{module}.{qualname}" if module else qualname

        # Fallback to link name if available
        if hasattr(target, "_tenro_linked_name"):
            return str(target._tenro_linked_name)

        # Last resort: use function name
        return getattr(target, "__name__", str(target))

    return str(target)


def _is_class_method(qualname: str) -> bool:
    """Check if qualname indicates a class method."""
    return "." in qualname and "<lambda>" not in qualname and "<locals>" not in qualname


def _build_undecorated_error_message(func_name: str, expected_type: str) -> str:
    """Build helpful error message for undecorated functions."""
    return (
        f"Cannot simulate '{func_name}' - function is not "
        f"decorated with @link_{expected_type}.\n\n"
        f"The Import Trap: Simulating undecorated MODULE-LEVEL functions "
        f"fails silently when imported with 'from module import func'. "
        f"The simulation patches the source module, but your code holds a "
        f"separate reference.\n\n"
        f"Fix: Add @link_{expected_type} decorator to '{func_name}':\n"
        f"  from tenro import link_{expected_type}\n\n"
        f"  @link_{expected_type}('{func_name}')\n"
        f"  def {func_name}(...):\n"
        f"      ...\n\n"
        f"Alternatively, use a module path string:\n"
        f"  construct.simulate_{expected_type}("
        f"'myapp.{func_name}', result=...)\n\n"
        f"Note: CLASS METHODS don't need decorators! Pass them directly:\n"
        f"  from third_party import MyClass\n"
        f"  construct.simulate_{expected_type}(MyClass.method, result=...)"
    )


def parse_dotted_path(path: str) -> tuple[Any, str]:
    """Parse dotted path into (container_object, attribute_name) for patching.

    Handles both module-level functions and class methods:
    - `module.func` -> (module, "func")
    - `module.Class.method` -> (Class, "method")
    - `module.Outer.Inner.method` -> (Inner, "method")

    Args:
        path: Dotted path to parse (e.g., "langchain.chat_models.ChatOpenAI.predict").

    Returns:
        Tuple of (container_object, attribute_name) for patching.

    Raises:
        ValueError: If module not imported.
        AttributeError: If path is invalid.
    """
    if "." not in path:
        raise ValueError(f"Path must contain at least one dot, got: {path}")

    parts = path.split(".")
    module_name = parts[0]
    module = sys.modules.get(module_name)

    if module is None:
        raise ValueError(
            f"Module '{module_name}' not imported. "
            f"Import the module before simulating: import {module_name}"
        )

    container = module
    for part in parts[1:-1]:
        if not hasattr(container, part):
            raise AttributeError(
                f"'{container}' has no attribute '{part}' (while parsing path '{path}')"
            )
        container = getattr(container, part)

    return container, parts[-1]
