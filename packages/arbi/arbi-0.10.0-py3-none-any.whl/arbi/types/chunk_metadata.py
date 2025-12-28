# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from .._models import BaseModel

__all__ = ["ChunkMetadata"]


class ChunkMetadata(BaseModel):
    chunk_doc_idx: int

    chunk_ext_id: str

    chunk_pg_idx: int

    created_at: str

    page_number: int

    chunk_id: Optional[str] = None

    doc_ext_id: Optional[str] = None

    doc_title: Optional[str] = None

    rerank_score: Optional[float] = None

    score: Optional[float] = None

    tokens: Optional[int] = None
