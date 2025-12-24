# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["RerankerConfigParam"]


class RerankerConfigParam(TypedDict, total=False):
    api_type: Annotated[Literal["local", "remote"], PropertyInfo(alias="API_TYPE")]
    """The inference type (local or remote)."""

    max_numb_of_chunks: Annotated[int, PropertyInfo(alias="MAX_NUMB_OF_CHUNKS")]
    """Maximum number of chunks to return after reranking."""

    model_name: Annotated[str, PropertyInfo(alias="MODEL_NAME")]
    """Name of the reranking model to use."""
