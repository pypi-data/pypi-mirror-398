# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from typing_extensions import Literal, TypeAlias

from ...._models import BaseModel

__all__ = ["ContactCreateResponse", "ContactCreateResponseItem"]


class ContactCreateResponseItem(BaseModel):
    """Response model for contact records.

    Matches WorkspaceUserResponse structure for consistency.
    """

    created_at: str

    email: str

    external_id: str

    status: Literal["invitation_pending", "invitation_expired", "invitation_accepted", "existing_user"]

    last_name: Optional[str] = None

    name: Optional[str] = None

    user_ext_id: Optional[str] = None


ContactCreateResponse: TypeAlias = List[ContactCreateResponseItem]
