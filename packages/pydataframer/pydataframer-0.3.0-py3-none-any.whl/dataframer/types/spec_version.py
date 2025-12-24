# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, Optional
from datetime import datetime

from .._models import BaseModel

__all__ = ["SpecVersion"]


class SpecVersion(BaseModel):
    config_yaml: str

    orig_results_yaml: str

    results_yaml: str

    spec_id: str

    version: int

    id: Optional[str] = None

    created_at: Optional[datetime] = None

    runtime_params: Optional[Dict[str, object]] = None

    spec_name: Optional[str] = None
