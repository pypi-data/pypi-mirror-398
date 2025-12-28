# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["WorkspaceUpdateParams"]


class WorkspaceUpdateParams(TypedDict, total=False):
    description: Optional[str]

    is_public: Optional[bool]

    name: Optional[str]

    workspace_key: Annotated[str, PropertyInfo(alias="workspace-key")]
