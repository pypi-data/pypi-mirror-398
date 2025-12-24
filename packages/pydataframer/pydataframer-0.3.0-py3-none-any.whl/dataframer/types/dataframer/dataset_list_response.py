# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime
from typing_extensions import Literal, TypeAlias

from ..._models import BaseModel

__all__ = ["DatasetListResponse", "DatasetListResponseItem", "DatasetListResponseItemShortSampleCompatibility"]


class DatasetListResponseItemShortSampleCompatibility(BaseModel):
    is_long_samples_compatible: Optional[bool] = None
    """Whether the dataset is compatible with long sample generation"""

    is_short_samples_compatible: Optional[bool] = None
    """Whether the dataset is compatible with short sample generation"""

    reason: Optional[str] = None
    """Reason for incompatibility if applicable"""


class DatasetListResponseItem(BaseModel):
    dataset_type: Literal["SINGLE_FILE", "MULTI_FILE", "MULTI_FOLDER"]

    name: str

    id: Optional[str] = None

    created_at: Optional[datetime] = None

    created_by_name: Optional[str] = None

    dataset_type_display: Optional[str] = None

    description: Optional[str] = None

    file_count: Optional[int] = None

    folder_count: Optional[int] = None

    short_sample_compatibility: Optional[DatasetListResponseItemShortSampleCompatibility] = None

    updated_at: Optional[datetime] = None


DatasetListResponse: TypeAlias = List[DatasetListResponseItem]
