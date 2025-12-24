# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime

from ..._models import BaseModel

__all__ = ["ChatSendMessageResponse"]


class ChatSendMessageResponse(BaseModel):
    assistant_message: str
    """Assistant's response"""

    evaluation_id: str

    user_message: str
    """User's question/query"""

    id: Optional[str] = None

    created_at: Optional[datetime] = None

    user: Optional[int] = None

    user_email: Optional[str] = None
