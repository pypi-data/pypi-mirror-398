# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, Optional
from datetime import datetime
from typing_extensions import Literal

from ..._models import BaseModel

__all__ = ["RunRetrieveResponse"]


class RunRetrieveResponse(BaseModel):
    spec_version_id: str

    id: Optional[str] = None

    completed_at: Optional[datetime] = None

    created_at: Optional[datetime] = None

    created_by: Optional[int] = None

    created_by_name: Optional[str] = None

    dataset_id: Optional[str] = None

    dataset_name: Optional[str] = None

    dataset_type: Optional[str] = None

    duration_seconds: Optional[float] = None

    metrics_json: Optional[Dict[str, object]] = None

    number_of_samples: Optional[int] = None

    runtime_params: Optional[Dict[str, object]] = None

    spec_id: Optional[str] = None

    spec_name: Optional[str] = None

    spec_version: Optional[int] = None

    started_at: Optional[datetime] = None

    status: Optional[Literal["PENDING", "RUNNING", "SUCCEEDED", "FAILED", "CANCELED"]] = None

    status_display: Optional[str] = None

    trace: Optional[Dict[str, object]] = None
