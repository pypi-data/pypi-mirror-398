# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Required, TypedDict

__all__ = ["UserLoginParams"]


class UserLoginParams(TypedDict, total=False):
    email: Required[str]

    public_key: Required[str]

    sso_token: Optional[str]
