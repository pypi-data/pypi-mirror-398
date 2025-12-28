# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from ..._models import BaseModel

__all__ = ["UserResponse"]


class UserResponse(BaseModel):
    """Standard user representation used across all endpoints.

    Used for: login response, workspace users, contacts (when registered).
    """

    email: str

    encryption_public_key: str

    external_id: str

    family_name: str

    given_name: str

    picture: Optional[str] = None
