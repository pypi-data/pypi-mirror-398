# Copyright 2025 Tenro.ai
# SPDX-License-Identifier: Apache-2.0

"""Prompt models for Tenro SDK."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from tenro.core.model_base import BaseModel


class PromptObject(BaseModel):
    """A versioned prompt template.

    Attributes:
        name: Prompt name.
        text: Prompt content.
        version: Prompt version identifier.
        metadata: Optional prompt metadata.
    """

    name: str
    text: str
    version: str
    metadata: dict[str, Any] = Field(default_factory=dict)
