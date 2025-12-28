# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from ..._models import BaseModel
from .user_response import UserResponse

__all__ = ["UserLoginResponse"]


class UserLoginResponse(BaseModel):
    """Login response with access token, session key, and user info.

    Used by: /user/login
    """

    access_token: str

    session_key: str

    user: UserResponse
    """Standard user representation used across all endpoints.

    Used for: login response, workspace users, contacts (when registered).
    """
