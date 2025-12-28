# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime
from typing_extensions import Literal, TypeAlias

from ..._models import BaseModel

__all__ = ["WorkspaceGetTagsResponse", "WorkspaceGetTagsResponseItem", "WorkspaceGetTagsResponseItemTagType"]


class WorkspaceGetTagsResponseItemTagType(BaseModel):
    """Tag format configuration stored as JSONB.

    Type-specific fields:
    - select: options (list of choices, can be single or multi-select)
    - checkbox, text, number, folder: type only
    """

    options: Optional[List[str]] = None

    type: Optional[Literal["checkbox", "text", "number", "select", "folder"]] = None


class WorkspaceGetTagsResponseItem(BaseModel):
    created_at: datetime

    created_by_ext_id: str

    doctag_count: int

    external_id: str

    name: str

    shared: bool

    tag_type: WorkspaceGetTagsResponseItemTagType
    """Tag format configuration stored as JSONB.

    Type-specific fields:

    - select: options (list of choices, can be single or multi-select)
    - checkbox, text, number, folder: type only
    """

    updated_at: datetime

    workspace_ext_id: str

    parent_ext_id: Optional[str] = None

    updated_by_ext_id: Optional[str] = None


WorkspaceGetTagsResponse: TypeAlias = List[WorkspaceGetTagsResponseItem]
