# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import date, datetime

from ..._models import BaseModel
from .document.doc_tag_response import DocTagResponse

__all__ = ["DocResponse", "DocMetadata"]


class DocMetadata(BaseModel):
    """Structured model for document metadata stored in JSONB column."""

    doc_date: Optional[date] = None

    doc_summary: Optional[str] = None

    title: Optional[str] = None


class DocResponse(BaseModel):
    created_at: datetime

    external_id: str

    updated_at: datetime

    workspace_ext_id: str

    config_ext_id: Optional[str] = None

    created_by_ext_id: Optional[str] = None

    doc_metadata: Optional[DocMetadata] = None
    """Structured model for document metadata stored in JSONB column."""

    doctags: Optional[List[DocTagResponse]] = None

    file_name: Optional[str] = None

    file_size: Optional[int] = None

    file_type: Optional[str] = None

    n_chunks: Optional[int] = None

    n_pages: Optional[int] = None

    re_ocred: Optional[bool] = None

    shared: Optional[bool] = None

    status: Optional[str] = None

    storage_type: Optional[str] = None

    storage_uri: Optional[str] = None

    tokens: Optional[int] = None
