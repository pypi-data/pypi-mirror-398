# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from ..._models import BaseModel

__all__ = ["ConfigGetVersionsResponse", "Version"]


class Version(BaseModel):
    created_at: str

    external_id: str

    title: Optional[str] = None


class ConfigGetVersionsResponse(BaseModel):
    versions: List[Version]
