# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict
from typing_extensions import Required, TypedDict

__all__ = ["SpecUpdateParams"]


class SpecUpdateParams(TypedDict, total=False):
    config_yaml: Required[str]
    """YAML configuration for the spec (required)"""

    description: str
    """Update the spec description (optional)"""

    name: str
    """Update the spec name (optional)"""

    orig_results_yaml: str
    """Original results YAML (optional)"""

    results_yaml: str
    """Results YAML from analysis (optional)"""

    runtime_params: Dict[str, object]
    """Runtime parameters for generation (optional)"""
