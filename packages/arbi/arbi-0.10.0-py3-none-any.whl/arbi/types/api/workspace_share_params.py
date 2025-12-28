# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["WorkspaceShareParams"]


class WorkspaceShareParams(TypedDict, total=False):
    recipient_email: Required[str]

    workspace_key: Annotated[str, PropertyInfo(alias="workspace-key")]
