# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Required, TypedDict

__all__ = ["ChunkMetadataParam"]


class ChunkMetadataParam(TypedDict, total=False):
    chunk_doc_idx: Required[int]

    chunk_ext_id: Required[str]

    chunk_pg_idx: Required[int]

    created_at: Required[str]

    page_number: Required[int]

    chunk_id: Optional[str]

    doc_ext_id: Optional[str]

    doc_title: Optional[str]

    rerank_score: Optional[float]

    score: Optional[float]

    tokens: Optional[int]
