# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, TypedDict

from ..._types import FileTypes

__all__ = ["DatasetCreateFromZipParams"]


class DatasetCreateFromZipParams(TypedDict, total=False):
    name: Required[str]
    """Dataset name (unique within company)"""

    zip_file: Required[FileTypes]
    """ZIP file containing dataset files"""

    description: str
    """Optional dataset description"""
