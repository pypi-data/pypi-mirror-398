"""Utilities for Figlinq statistical analyses.

This module centralizes schema definitions and payload helpers for Figlinq's
statistical analysis features. It is consumed by both the public figlinq SDK
and internal services so that behavior stays consistent.
"""

from __future__ import annotations

from .schemas import ANALYSIS_SCHEMA_LIBRARY, SUPPORTED_TESTS, get_analysis_schema_markdown
from .payloads import build_analysis_payload

__all__ = [
    "ANALYSIS_SCHEMA_LIBRARY",
    "SUPPORTED_TESTS",
    "build_analysis_payload",
    "get_analysis_schema_markdown",
]
