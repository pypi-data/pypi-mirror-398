# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime
from typing_extensions import Literal, TypeAlias

from ..._models import BaseModel
from ..spec_version import SpecVersion

__all__ = ["SpecListResponse", "SpecListResponseItem"]


class SpecListResponseItem(BaseModel):
    datasets_id: str

    name: str

    id: Optional[str] = None

    company_id: Optional[str] = None

    company_name: Optional[str] = None

    created_at: Optional[datetime] = None

    created_by: Optional[int] = None

    created_by_name: Optional[str] = None

    data_property_variations: Optional[str] = None

    dataset_name: Optional[str] = None

    description: Optional[str] = None

    latest_version: Optional[int] = None

    latest_version_data: Optional[str] = None

    status: Optional[Literal["PROCESSING", "READY", "FAILED"]] = None

    updated_at: Optional[datetime] = None

    version_count: Optional[int] = None

    versions: Optional[List[SpecVersion]] = None


SpecListResponse: TypeAlias = List[SpecListResponseItem]
