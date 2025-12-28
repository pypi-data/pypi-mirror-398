# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["ConversationUpdateTitleParams"]


class ConversationUpdateTitleParams(TypedDict, total=False):
    title: Required[str]
    """New conversation title (1-60 characters)"""

    workspace_key: Annotated[str, PropertyInfo(alias="workspace-key")]
