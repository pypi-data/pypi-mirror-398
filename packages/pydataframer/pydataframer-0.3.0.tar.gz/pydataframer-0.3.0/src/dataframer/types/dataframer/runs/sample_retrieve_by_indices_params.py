# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable
from typing_extensions import Required, TypedDict

__all__ = ["SampleRetrieveByIndicesParams"]


class SampleRetrieveByIndicesParams(TypedDict, total=False):
    indices: Required[Iterable[int]]
    """List of finish-time positions to retrieve (max 1000)"""
