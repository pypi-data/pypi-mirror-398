# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict
from typing_extensions import Required, TypedDict

__all__ = ["UserChangePasswordParams"]


class UserChangePasswordParams(TypedDict, total=False):
    current_public_key: Required[str]

    new_public_key: Required[str]

    rewrapped_workspace_keys: Required[Dict[str, str]]
