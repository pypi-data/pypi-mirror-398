# Copyright 2025 Tenro.ai
# SPDX-License-Identifier: Apache-2.0

"""Lifecycle management for Construct spans."""

from tenro.construct.lifecycle.linker import SpanLinker
from tenro.construct.lifecycle.span_accessor import SpanAccessor

__all__ = ["SpanAccessor", "SpanLinker"]
