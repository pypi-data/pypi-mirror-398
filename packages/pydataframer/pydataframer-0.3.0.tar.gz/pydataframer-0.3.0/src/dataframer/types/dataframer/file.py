# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime
from typing_extensions import Literal

from ..._models import BaseModel

__all__ = ["File"]


class File(BaseModel):
    file_name: str

    file_type: Literal["JSON", "JSONL", "CSV", "MD", "TXT", "PDF"]

    storage_uri: str

    id: Optional[str] = None

    bytes_size: Optional[int] = None

    created_at: Optional[datetime] = None

    datasets_id: Optional[str] = None

    file_type_display: Optional[str] = None

    folder_id: Optional[str] = None

    sha256: Optional[str] = None
