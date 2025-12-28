# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["EmbedderConfig"]


class EmbedderConfig(BaseModel):
    api_type: Optional[Literal["local", "remote"]] = FieldInfo(alias="API_TYPE", default=None)
    """The inference type (local or remote)."""

    batch_size: Optional[int] = FieldInfo(alias="BATCH_SIZE", default=None)
    """Smaller batch size for better parallelization."""

    embed_prefix: Optional[str] = FieldInfo(alias="EMBED_PREFIX", default=None)
    """How to embed the sentence for retrieval."""

    max_concurrent_requests: Optional[int] = FieldInfo(alias="MAX_CONCURRENT_REQUESTS", default=None)
    """Adjust concurrency level as needed."""

    api_model_name: Optional[str] = FieldInfo(alias="MODEL_NAME", default=None)
    """The name of the embedder model."""

    query_prefix: Optional[str] = FieldInfo(alias="QUERY_PREFIX", default=None)
    """How to embed the sentence for query."""
