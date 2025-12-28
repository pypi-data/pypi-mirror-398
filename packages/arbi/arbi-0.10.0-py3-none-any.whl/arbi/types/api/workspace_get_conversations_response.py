# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime
from typing_extensions import TypeAlias

from ..._models import BaseModel

__all__ = ["WorkspaceGetConversationsResponse", "WorkspaceGetConversationsResponseItem"]


class WorkspaceGetConversationsResponseItem(BaseModel):
    created_at: datetime

    created_by_ext_id: str

    external_id: str

    message_count: int

    title: Optional[str] = None

    updated_at: datetime

    is_shared: Optional[bool] = None

    updated_by_ext_id: Optional[str] = None


WorkspaceGetConversationsResponse: TypeAlias = List[WorkspaceGetConversationsResponseItem]
