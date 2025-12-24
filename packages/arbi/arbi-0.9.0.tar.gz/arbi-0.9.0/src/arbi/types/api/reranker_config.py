# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["RerankerConfig"]


class RerankerConfig(BaseModel):
    api_type: Optional[Literal["local", "remote"]] = FieldInfo(alias="API_TYPE", default=None)
    """The inference type (local or remote)."""

    max_numb_of_chunks: Optional[int] = FieldInfo(alias="MAX_NUMB_OF_CHUNKS", default=None)
    """Maximum number of chunks to return after reranking."""

    api_model_name: Optional[str] = FieldInfo(alias="MODEL_NAME", default=None)
    """Name of the reranking model to use."""
