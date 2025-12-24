# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Optional
from datetime import datetime
from typing_extensions import Literal

from .folder import Folder
from ..._models import BaseModel

__all__ = ["DatasetUpdateResponse", "ShortSampleCompatibility"]


class ShortSampleCompatibility(BaseModel):
    is_long_samples_compatible: Optional[bool] = None
    """Whether the dataset is compatible with long sample generation"""

    is_short_samples_compatible: Optional[bool] = None
    """Whether the dataset is compatible with short sample generation"""

    reason: Optional[str] = None
    """Reason for incompatibility if applicable"""


class DatasetUpdateResponse(BaseModel):
    dataset_type: Literal["SINGLE_FILE", "MULTI_FILE", "MULTI_FOLDER"]

    name: str

    id: Optional[str] = None

    company: Optional[str] = None

    company_name: Optional[str] = None

    config_json: Optional[Dict[str, object]] = None

    created_at: Optional[datetime] = None

    created_by: Optional[int] = None

    created_by_name: Optional[str] = None

    dataset_type_display: Optional[str] = None

    description: Optional[str] = None

    file_count: Optional[int] = None

    folder_count: Optional[int] = None

    folders: Optional[List[Folder]] = None

    short_sample_compatibility: Optional[ShortSampleCompatibility] = None

    updated_at: Optional[datetime] = None
