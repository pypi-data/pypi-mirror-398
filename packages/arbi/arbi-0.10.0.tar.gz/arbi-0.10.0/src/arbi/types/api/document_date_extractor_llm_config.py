# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["DocumentDateExtractorLlmConfig"]


class DocumentDateExtractorLlmConfig(BaseModel):
    api_type: Optional[Literal["local", "remote"]] = FieldInfo(alias="API_TYPE", default=None)
    """The inference type (local or remote)."""

    max_char_context_to_answer: Optional[int] = FieldInfo(alias="MAX_CHAR_CONTEXT_TO_ANSWER", default=None)
    """Maximum characters in document for context."""

    max_tokens: Optional[int] = FieldInfo(alias="MAX_TOKENS", default=None)
    """Maximum number of tokens allowed."""

    api_model_name: Optional[str] = FieldInfo(alias="MODEL_NAME", default=None)
    """The name of the non-reasoning model to be used."""

    system_instruction: Optional[str] = FieldInfo(alias="SYSTEM_INSTRUCTION", default=None)

    temperature: Optional[float] = FieldInfo(alias="TEMPERATURE", default=None)
    """Temperature value for randomness."""
