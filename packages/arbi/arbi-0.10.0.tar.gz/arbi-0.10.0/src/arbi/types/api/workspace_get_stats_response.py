# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from ..._models import BaseModel

__all__ = ["WorkspaceGetStatsResponse"]


class WorkspaceGetStatsResponse(BaseModel):
    private_conversation_count: Optional[int] = None

    private_document_count: Optional[int] = None

    shared_conversation_count: Optional[int] = None

    shared_document_count: Optional[int] = None
