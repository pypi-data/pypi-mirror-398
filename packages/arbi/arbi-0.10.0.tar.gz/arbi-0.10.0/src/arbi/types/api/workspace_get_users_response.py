# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List
from typing_extensions import TypeAlias

from .user_response import UserResponse

__all__ = ["WorkspaceGetUsersResponse"]

WorkspaceGetUsersResponse: TypeAlias = List[UserResponse]
