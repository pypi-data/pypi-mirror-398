# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from ..._models import BaseModel

__all__ = ["WorkspaceCopyResponse", "Result"]


class Result(BaseModel):
    source_doc_ext_id: str

    success: bool

    error: Optional[str] = None

    new_doc_ext_id: Optional[str] = None


class WorkspaceCopyResponse(BaseModel):
    detail: str

    documents_copied: Optional[int] = None

    results: Optional[List[Result]] = None
