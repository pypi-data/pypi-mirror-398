# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, Optional
from datetime import datetime

from .._models import BaseModel

__all__ = ["SampleClassification"]


class SampleClassification(BaseModel):
    classifications: Dict[str, object]
    """JSON mapping axis names to classified property values"""

    evaluation_id: str

    sample_identifier: str
    """Identifier for the sample (file name, folder name, or row number)"""

    id: Optional[str] = None

    created_at: Optional[datetime] = None

    sub_file_classifications: Optional[Dict[str, object]] = None
    """For multi-file samples, classification of each file within the sample"""
