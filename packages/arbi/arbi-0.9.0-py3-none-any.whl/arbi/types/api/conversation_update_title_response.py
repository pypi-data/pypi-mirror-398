# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from ..._models import BaseModel

__all__ = ["ConversationUpdateTitleResponse"]


class ConversationUpdateTitleResponse(BaseModel):
    title: str

    detail: Optional[str] = None
