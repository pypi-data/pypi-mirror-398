# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from pydantic import Field as FieldInfo

from ...._models import BaseModel

__all__ = ["GeneratedFileListResponse", "GeneratedFile"]


class GeneratedFile(BaseModel):
    id: Optional[str] = None

    content: Optional[str] = None

    evaluation_model: Optional[str] = None

    generation_model: Optional[str] = None

    iterations: Optional[int] = None

    name: Optional[str] = None

    path: Optional[str] = None

    s3_key: Optional[str] = None

    size: Optional[int] = None

    status: Optional[str] = None

    status_details: Optional[str] = FieldInfo(alias="statusDetails", default=None)

    termination_reason: Optional[str] = None

    type: Optional[str] = None

    uploaded_at: Optional[str] = FieldInfo(alias="uploadedAt", default=None)

    workflow_id: Optional[str] = None


class GeneratedFileListResponse(BaseModel):
    generated_files: List[GeneratedFile]
    """List of generated files"""

    run_id: str
    """ID of the run"""
