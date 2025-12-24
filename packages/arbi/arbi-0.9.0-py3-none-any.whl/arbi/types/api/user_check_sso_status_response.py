# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from ..._models import BaseModel

__all__ = ["UserCheckSSOStatusResponse"]


class UserCheckSSOStatusResponse(BaseModel):
    """SSO status response - indicates user registration state.

    States:
    - new_user: No user exists, show "Set Master Password"
    - local_exists: Local user exists, show "Link SSO Account? Enter your master password"
    - sso_exists: SSO user exists, show "Enter Master Password"
    """

    email: str

    status: str

    last_name: Optional[str] = None

    name: Optional[str] = None
