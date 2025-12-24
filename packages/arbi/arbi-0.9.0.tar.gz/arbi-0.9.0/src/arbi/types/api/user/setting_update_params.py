# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable, Optional
from typing_extensions import Required, TypedDict

from ...._types import SequenceNotStr

__all__ = ["SettingUpdateParams", "Subscription", "Tableview"]


class SettingUpdateParams(TypedDict, total=False):
    ai_mode: Optional[str]

    pinned_workspaces: Optional[SequenceNotStr[str]]

    show_document_navigator: Optional[bool]

    show_help_page: Optional[bool]

    show_invite_tab: Optional[bool]

    show_security_settings: Optional[bool]

    show_smart_search: Optional[bool]

    show_templates: Optional[bool]

    show_thread_visualization: Optional[bool]

    subscription: Optional[Subscription]
    """Trial update - only trial_expires can be set, and only if currently null."""

    tableviews: Optional[Iterable[Tableview]]


class Subscription(TypedDict, total=False):
    """Trial update - only trial_expires can be set, and only if currently null."""

    trial_expires: Optional[int]


class Tableview(TypedDict, total=False):
    """Saved column configuration for the document table.

    Column ID formats:
    - Standard columns: "doc_date", "title", "file_name", "status", "n_pages", "created_at"
    - Tags: tag external ID (e.g., "tag-a1b2c3d4")
    """

    columns: Required[SequenceNotStr[str]]

    name: Required[str]

    workspace: Required[str]
