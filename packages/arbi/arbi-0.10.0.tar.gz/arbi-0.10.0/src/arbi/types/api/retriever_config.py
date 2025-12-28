# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["RetrieverConfig"]


class RetrieverConfig(BaseModel):
    group_size: Optional[int] = FieldInfo(alias="GROUP_SIZE", default=None)
    """Maximum number of chunks per document for retrieval."""

    max_distinct_documents: Optional[int] = FieldInfo(alias="MAX_DISTINCT_DOCUMENTS", default=None)
    """Maximum number of distinct documents to search for."""

    max_total_chunks_to_retrieve: Optional[int] = FieldInfo(alias="MAX_TOTAL_CHUNKS_TO_RETRIEVE", default=None)
    """Maximum total number of chunks to retrieve for all documents retrieved."""

    min_retrieval_sim_score: Optional[float] = FieldInfo(alias="MIN_RETRIEVAL_SIM_SCORE", default=None)
    """Minimum similarity score for retrieval of a chunk."""
