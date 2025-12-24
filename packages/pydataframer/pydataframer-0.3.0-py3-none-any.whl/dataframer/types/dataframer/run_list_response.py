# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Optional
from datetime import datetime
from typing_extensions import Literal, TypeAlias

from ..._models import BaseModel

__all__ = ["RunListResponse", "RunListResponseItem"]


class RunListResponseItem(BaseModel):
    id: Optional[str] = None

    completed_at: Optional[datetime] = None

    created_at: Optional[datetime] = None

    created_by_name: Optional[str] = None

    dataset_id: Optional[str] = None

    dataset_name: Optional[str] = None

    duration_seconds: Optional[float] = None

    number_of_samples: Optional[int] = None

    spec_id: Optional[str] = None

    spec_name: Optional[str] = None

    spec_version: Optional[int] = None

    started_at: Optional[datetime] = None

    status: Optional[Literal["PENDING", "RUNNING", "SUCCEEDED", "FAILED", "CANCELED"]] = None

    status_display: Optional[str] = None

    trace: Optional[Dict[str, object]] = None


RunListResponse: TypeAlias = List[RunListResponseItem]
