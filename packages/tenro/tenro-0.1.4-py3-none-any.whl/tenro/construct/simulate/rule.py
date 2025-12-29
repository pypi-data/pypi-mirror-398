# Copyright 2025 Tenro.ai
# SPDX-License-Identifier: Apache-2.0

"""Simulation rule model for Construct simulation."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, model_validator


class SimulationRule(BaseModel):
    """Validated rule for simulation responses.

    Enforces mutual exclusivity between static return values and side effects.

    Attributes:
        returns_value: Value to return when simulated function is called.
        side_effect: Exception, callable, or list for sequential responses.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    returns_value: object | None = None
    side_effect: object | None = None

    @model_validator(mode="before")
    @classmethod
    def check_exclusive_fields(cls, values: dict[str, object]) -> dict[str, object]:
        """Ensure return values and side effects are mutually exclusive.

        Args:
            values: Raw field values for validation.

        Returns:
            The validated field mapping.

        Raises:
            ValueError: If both returns_value and side_effect are provided.

        Examples:
            >>> SimulationRule(returns_value="ok")
            SimulationRule(returns_value='ok', side_effect=`None`)
        """
        if values.get("returns_value") is not None and values.get("side_effect") is not None:
            raise ValueError("Cannot set both 'returns_value' and 'side_effect'")
        return values
