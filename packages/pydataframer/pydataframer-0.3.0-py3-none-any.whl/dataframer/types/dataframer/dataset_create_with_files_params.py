# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Required, TypedDict

from ..._types import FileTypes, SequenceNotStr

__all__ = ["DatasetCreateWithFilesParams"]


class DatasetCreateWithFilesParams(TypedDict, total=False):
    dataset_type: Required[Literal["SINGLE_FILE", "MULTI_FILE", "MULTI_FOLDER"]]
    """Dataset type: SINGLE_FILE, MULTI_FILE, or MULTI_FOLDER"""

    name: Required[str]
    """Dataset name (unique within company)"""

    config_json: str
    """Optional configuration JSON as string"""

    csv_headers: str
    """Optional CSV headers as JSON array for SINGLE_FILE CSV files"""

    description: str
    """Optional dataset description"""

    file: FileTypes
    """Single file for SINGLE_FILE dataset type"""

    files: SequenceNotStr[FileTypes]
    """Multiple files for MULTI_FILE or MULTI_FOLDER dataset types.

    Each file will be sent as a separate form field named 'files'. For MULTI_FOLDER:
    minimum 2 files required (at least 1 file per folder, across at least 2
    folders).
    """

    folder_names: SequenceNotStr[str]
    """Folder names for MULTI_FOLDER (parallel array with files).

    Each folder name is sent as a separate 'folder_names' form field. Minimum 2
    unique folder names required.
    """
