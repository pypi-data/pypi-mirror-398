# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, Optional
from datetime import datetime

from ..._models import BaseModel

__all__ = ["HumanLabelRetrieveResponse"]


class HumanLabelRetrieveResponse(BaseModel):
    file_identifier: str
    """Identifier for the file (filename or folder/filename path)"""

    labels: Dict[str, object]
    """JSON object mapping label keys to values"""

    run_id: str

    id: Optional[str] = None

    company_id: Optional[str] = None

    created_at: Optional[datetime] = None

    created_by: Optional[int] = None

    created_by_name: Optional[str] = None

    sample_identifier: Optional[str] = None
    """Optional: row identifier for structured files (e.g., "sample_0")"""

    updated_at: Optional[datetime] = None

    updated_by: Optional[int] = None

    updated_by_name: Optional[str] = None
