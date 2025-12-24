# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List
from typing_extensions import TypeAlias

from ..._models import BaseModel

__all__ = ["WorkspaceGetUsersResponse", "WorkspaceGetUsersResponseItem"]


class WorkspaceGetUsersResponseItem(BaseModel):
    email: str

    last_name: str

    name: str

    user_ext_id: str


WorkspaceGetUsersResponse: TypeAlias = List[WorkspaceGetUsersResponseItem]
