# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["TagUpdateParams"]


class TagUpdateParams(TypedDict, total=False):
    name: Optional[str]

    parent_ext_id: Optional[str]

    shared: Optional[bool]

    workspace_key: Annotated[str, PropertyInfo(alias="workspace-key")]
