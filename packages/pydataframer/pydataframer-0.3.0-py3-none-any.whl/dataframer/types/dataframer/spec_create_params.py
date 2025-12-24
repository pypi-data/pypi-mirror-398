# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, TypedDict

__all__ = ["SpecCreateParams"]


class SpecCreateParams(TypedDict, total=False):
    datasets_id: Required[str]
    """UUID of the dataset this spec is based on"""

    name: Required[str]
    """Unique name for the spec (within dataset and company)"""

    description: str
    """Optional description of the spec"""
