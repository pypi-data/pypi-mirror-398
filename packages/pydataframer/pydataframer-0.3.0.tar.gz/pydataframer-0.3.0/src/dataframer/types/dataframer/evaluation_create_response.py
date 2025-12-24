# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Optional
from datetime import datetime
from typing_extensions import Literal

from ..._models import BaseModel
from ..sample_classification import SampleClassification

__all__ = ["EvaluationCreateResponse"]


class EvaluationCreateResponse(BaseModel):
    run_id: str

    id: Optional[str] = None

    company_id: Optional[str] = None

    completed_at: Optional[datetime] = None

    conformance_explanation: Optional[str] = None
    """Explanation of the conformance score"""

    conformance_score: Optional[float] = None
    """Score between 0-100 indicating conformance to requirements"""

    conformant_areas: Optional[str] = None

    created_at: Optional[datetime] = None

    created_by: Optional[int] = None

    created_by_name: Optional[str] = None

    distribution_analysis: Optional[Dict[str, object]] = None
    """JSON containing observed vs expected distributions for each axis"""

    duration_seconds: Optional[float] = None

    error_message: Optional[str] = None

    non_conformant_areas: Optional[str] = None

    sample_classifications: Optional[List[SampleClassification]] = None

    started_at: Optional[datetime] = None

    status: Optional[Literal["PENDING", "RUNNING", "COMPLETED", "FAILED"]] = None

    status_display: Optional[str] = None

    trace: Optional[Dict[str, object]] = None
    """Trace information for debugging"""

    updated_at: Optional[datetime] = None
