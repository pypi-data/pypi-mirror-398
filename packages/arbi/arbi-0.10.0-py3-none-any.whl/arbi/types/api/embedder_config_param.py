# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["EmbedderConfigParam"]


class EmbedderConfigParam(TypedDict, total=False):
    api_type: Annotated[Literal["local", "remote"], PropertyInfo(alias="API_TYPE")]
    """The inference type (local or remote)."""

    batch_size: Annotated[int, PropertyInfo(alias="BATCH_SIZE")]
    """Smaller batch size for better parallelization."""

    embed_prefix: Annotated[str, PropertyInfo(alias="EMBED_PREFIX")]
    """How to embed the sentence for retrieval."""

    max_concurrent_requests: Annotated[int, PropertyInfo(alias="MAX_CONCURRENT_REQUESTS")]
    """Adjust concurrency level as needed."""

    model_name: Annotated[str, PropertyInfo(alias="MODEL_NAME")]
    """The name of the embedder model."""

    query_prefix: Annotated[str, PropertyInfo(alias="QUERY_PREFIX")]
    """How to embed the sentence for query."""
