# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from ..._types import SequenceNotStr
from ..._utils import PropertyInfo

__all__ = ["WorkspaceCopyParams"]


class WorkspaceCopyParams(TypedDict, total=False):
    items: Required[SequenceNotStr[str]]
    """List of document external IDs to copy (e.g., ['doc-a1b2c3d4', 'doc-e5f6g7h8'])"""

    target_workspace_ext_id: Required[str]

    target_workspace_key: Annotated[str, PropertyInfo(alias="target-workspace-key")]

    workspace_key: Annotated[str, PropertyInfo(alias="workspace-key")]
