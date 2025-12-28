# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from ..._models import BaseModel

__all__ = ["UserChangePasswordResponse"]


class UserChangePasswordResponse(BaseModel):
    detail: str

    workspaces_updated: int
