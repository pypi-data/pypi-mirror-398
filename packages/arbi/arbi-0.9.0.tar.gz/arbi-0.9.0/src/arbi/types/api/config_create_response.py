# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from ..._models import BaseModel

__all__ = ["ConfigCreateResponse"]


class ConfigCreateResponse(BaseModel):
    """Response model for configuration save endpoint"""

    created_at: str

    external_id: str

    title: Optional[str] = None
