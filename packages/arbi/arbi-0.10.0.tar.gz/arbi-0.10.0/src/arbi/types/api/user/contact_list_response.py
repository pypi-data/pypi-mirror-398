# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from typing_extensions import Literal, TypeAlias

from ...._models import BaseModel
from ..user_response import UserResponse

__all__ = ["ContactListResponse", "ContactListResponseItem"]


class ContactListResponseItem(BaseModel):
    """Contact record - may or may not be a registered user."""

    created_at: str

    email: str

    external_id: str

    status: Literal["invitation_pending", "invitation_expired", "invitation_accepted", "existing_user"]

    user: Optional[UserResponse] = None
    """Standard user representation used across all endpoints.

    Used for: login response, workspace users, contacts (when registered).
    """


ContactListResponse: TypeAlias = List[ContactListResponseItem]
