# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from ..._models import BaseModel

__all__ = ["WorkspaceShareResponse", "Notifications"]


class Notifications(BaseModel):
    recipient: str

    sender: str


class WorkspaceShareResponse(BaseModel):
    detail: str

    notifications: Notifications

    shared_with: str

    workspace_ext_id: str
