# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["RetrieverConfigParam"]


class RetrieverConfigParam(TypedDict, total=False):
    group_size: Annotated[int, PropertyInfo(alias="GROUP_SIZE")]
    """Maximum number of chunks per document for retrieval."""

    max_distinct_documents: Annotated[int, PropertyInfo(alias="MAX_DISTINCT_DOCUMENTS")]
    """Maximum number of distinct documents to search for."""

    max_total_chunks_to_retrieve: Annotated[int, PropertyInfo(alias="MAX_TOTAL_CHUNKS_TO_RETRIEVE")]
    """Maximum total number of chunks to retrieve for all documents retrieved."""

    min_retrieval_sim_score: Annotated[float, PropertyInfo(alias="MIN_RETRIEVAL_SIM_SCORE")]
    """Minimum similarity score for retrieval of a chunk."""
