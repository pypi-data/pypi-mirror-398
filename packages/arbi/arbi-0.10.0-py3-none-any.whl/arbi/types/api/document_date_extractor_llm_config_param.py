# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["DocumentDateExtractorLlmConfigParam"]


class DocumentDateExtractorLlmConfigParam(TypedDict, total=False):
    api_type: Annotated[Literal["local", "remote"], PropertyInfo(alias="API_TYPE")]
    """The inference type (local or remote)."""

    max_char_context_to_answer: Annotated[int, PropertyInfo(alias="MAX_CHAR_CONTEXT_TO_ANSWER")]
    """Maximum characters in document for context."""

    max_tokens: Annotated[int, PropertyInfo(alias="MAX_TOKENS")]
    """Maximum number of tokens allowed."""

    model_name: Annotated[str, PropertyInfo(alias="MODEL_NAME")]
    """The name of the non-reasoning model to be used."""

    system_instruction: Annotated[str, PropertyInfo(alias="SYSTEM_INSTRUCTION")]

    temperature: Annotated[float, PropertyInfo(alias="TEMPERATURE")]
    """Temperature value for randomness."""
