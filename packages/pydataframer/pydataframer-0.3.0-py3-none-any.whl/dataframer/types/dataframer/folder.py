# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime

from .file import File
from ..._models import BaseModel

__all__ = ["Folder"]


class Folder(BaseModel):
    name: str

    id: Optional[str] = None

    created_at: Optional[datetime] = None

    description: Optional[str] = None

    file_count: Optional[int] = None

    files: Optional[List[File]] = None
