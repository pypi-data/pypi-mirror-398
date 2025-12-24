# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime

from ..._models import BaseModel

__all__ = ["WorkspaceResponse", "User"]


class User(BaseModel):
    email: str

    last_name: str

    name: str

    user_ext_id: str


class WorkspaceResponse(BaseModel):
    created_at: datetime

    created_by_ext_id: str

    description: Optional[str] = None

    external_id: str

    is_public: bool

    name: str

    updated_at: datetime

    updated_by_ext_id: Optional[str] = None

    private_conversation_count: Optional[int] = None

    private_document_count: Optional[int] = None

    shared_conversation_count: Optional[int] = None

    shared_document_count: Optional[int] = None

    user_files_mb: Optional[float] = None

    users: Optional[List[User]] = None

    wrapped_key: Optional[str] = None
