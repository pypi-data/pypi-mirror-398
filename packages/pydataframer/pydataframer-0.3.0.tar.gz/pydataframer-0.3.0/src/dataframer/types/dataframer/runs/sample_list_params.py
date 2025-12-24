# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import TypedDict

__all__ = ["SampleListParams"]


class SampleListParams(TypedDict, total=False):
    limit: int
    """Maximum samples to return (default: all, max: 1000)"""

    offset: int
    """Starting position in finish-time-ordered list (default: 0)"""
