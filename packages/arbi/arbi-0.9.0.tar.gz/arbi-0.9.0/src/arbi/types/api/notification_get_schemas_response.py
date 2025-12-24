# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Union, Optional
from typing_extensions import Literal, TypeAlias

from ..._models import BaseModel

__all__ = [
    "NotificationGetSchemasResponse",
    "NotificationGetSchemasResponseItem",
    "NotificationGetSchemasResponseItemAuthResultMessage",
    "NotificationGetSchemasResponseItemConnectionClosedMessage",
    "NotificationGetSchemasResponseItemPongMessage",
    "NotificationGetSchemasResponseItemTaskUpdateMessage",
    "NotificationGetSchemasResponseItemNotificationMessage",
    "NotificationGetSchemasResponseItemWorkspaceShareMessage",
    "NotificationGetSchemasResponseItemContactAcceptedMessage",
]


class NotificationGetSchemasResponseItemAuthResultMessage(BaseModel):
    """Sent by server after authentication attempt."""

    success: bool

    reason: Optional[str] = None

    type: Optional[Literal["auth_result"]] = None


class NotificationGetSchemasResponseItemConnectionClosedMessage(BaseModel):
    """Sent when connection is being closed due to another active connection."""

    message: str

    type: Optional[Literal["connection_closed"]] = None


class NotificationGetSchemasResponseItemPongMessage(BaseModel):
    """Response to ping message."""

    type: Optional[Literal["pong"]] = None


class NotificationGetSchemasResponseItemTaskUpdateMessage(BaseModel):
    """Document processing task update."""

    doc_ext_id: str

    file_name: str

    progress: int

    status: Literal["queued", "processing", "completed", "failed"]

    workspace_ext_id: str

    type: Optional[Literal["task_update"]] = None


class NotificationGetSchemasResponseItemNotificationMessage(BaseModel):
    """Generic notification message."""

    message: str

    type: Optional[Literal["notification"]] = None


class NotificationGetSchemasResponseItemWorkspaceShareMessage(BaseModel):
    """Notification when a workspace is shared with you."""

    message: str

    type: Optional[Literal["workspace_share"]] = None


class NotificationGetSchemasResponseItemContactAcceptedMessage(BaseModel):
    """Notification when someone accepts your invitation."""

    contact_email: str

    contact_id: str

    message: str

    type: Optional[Literal["contact_accepted"]] = None


NotificationGetSchemasResponseItem: TypeAlias = Union[
    NotificationGetSchemasResponseItemAuthResultMessage,
    NotificationGetSchemasResponseItemConnectionClosedMessage,
    NotificationGetSchemasResponseItemPongMessage,
    NotificationGetSchemasResponseItemTaskUpdateMessage,
    NotificationGetSchemasResponseItemNotificationMessage,
    NotificationGetSchemasResponseItemWorkspaceShareMessage,
    NotificationGetSchemasResponseItemContactAcceptedMessage,
]

NotificationGetSchemasResponse: TypeAlias = List[NotificationGetSchemasResponseItem]
