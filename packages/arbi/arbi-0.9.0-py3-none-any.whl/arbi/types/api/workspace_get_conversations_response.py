# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime
from typing_extensions import TypeAlias

from ..._models import BaseModel

__all__ = ["WorkspaceGetConversationsResponse", "WorkspaceGetConversationsResponseItem"]


class WorkspaceGetConversationsResponseItem(BaseModel):
    created_at: datetime

    external_id: str

    is_creator: bool

    message_count: int

    title: Optional[str] = None

    updated_at: datetime

    is_shared: Optional[bool] = None


WorkspaceGetConversationsResponse: TypeAlias = List[WorkspaceGetConversationsResponseItem]
