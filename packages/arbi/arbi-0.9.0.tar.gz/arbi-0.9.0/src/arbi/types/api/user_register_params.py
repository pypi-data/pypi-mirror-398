# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Required, TypedDict

__all__ = ["UserRegisterParams"]


class UserRegisterParams(TypedDict, total=False):
    email: Required[str]

    public_key: Required[str]

    verification_credential: Required[str]

    last_name: Optional[str]

    name: Optional[str]
