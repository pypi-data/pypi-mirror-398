# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing_extensions import Literal

from ..._models import BaseModel

__all__ = ["GenerateCreateResponse"]


class GenerateCreateResponse(BaseModel):
    run_id: str
    """Run ID for retrieving results"""

    status: Literal["ACCEPTED", "PENDING", "RUNNING"]
    """Initial status of the generation task"""

    task_id: str
    """Task ID for tracking generation progress"""
