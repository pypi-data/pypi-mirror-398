# Copyright 2025 Tenro.ai
# SPDX-License-Identifier: Apache-2.0

"""Environment utilities for Tenro SDK."""

from __future__ import annotations

import os

from tenro.errors import ValidationError


def get_env_var(name: str, required: bool = False) -> str | None:
    """Get environment variable with optional validation.

    Args:
        name: Environment variable name.
        required: If True, raise ValidationError if not set.

    Returns:
        Environment variable value or None.

    Raises:
        ValidationError: If required=True and variable not set.
    """
    value = os.getenv(name)
    if required and not value:
        raise ValidationError(f"Required environment variable '{name}' is not set")
    return value
