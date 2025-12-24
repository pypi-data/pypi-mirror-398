# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Literal, Required, Annotated, TypedDict

from ..._types import SequenceNotStr
from ..._utils import PropertyInfo

__all__ = ["TagCreateParams", "TagType"]


class TagCreateParams(TypedDict, total=False):
    name: Required[str]

    workspace_ext_id: Required[str]

    parent_ext_id: Optional[str]

    shared: Optional[bool]

    tag_type: TagType
    """Tag format configuration stored as JSONB.

    Type-specific fields:

    - select: options (list of choices, can be single or multi-select)
    - checkbox, text, number, folder: type only
    """

    workspace_key: Annotated[str, PropertyInfo(alias="workspace-key")]


class TagType(TypedDict, total=False):
    """Tag format configuration stored as JSONB.

    Type-specific fields:
    - select: options (list of choices, can be single or multi-select)
    - checkbox, text, number, folder: type only
    """

    options: SequenceNotStr[str]

    type: Literal["checkbox", "text", "number", "select", "folder"]
