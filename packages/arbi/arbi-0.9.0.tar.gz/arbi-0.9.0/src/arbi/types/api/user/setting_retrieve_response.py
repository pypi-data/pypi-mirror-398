# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import TYPE_CHECKING, Dict, List, Optional

from pydantic import Field as FieldInfo

from ...._models import BaseModel

__all__ = ["SettingRetrieveResponse", "Subscription", "Tableview"]


class Subscription(BaseModel):
    """Subscription info exposed to frontend in user settings.

    Note: stripe_customer_id is deliberately excluded for security.
    This is a minimal model used in UserSettingsResponse.
    For full subscription details, use GET /subscription endpoint.
    """

    status: Optional[str] = None

    trial_expires: Optional[int] = None


class Tableview(BaseModel):
    """Saved column configuration for the document table.

    Column ID formats:
    - Standard columns: "doc_date", "title", "file_name", "status", "n_pages", "created_at"
    - Tags: tag external ID (e.g., "tag-a1b2c3d4")
    """

    columns: List[str]

    name: str

    workspace: str


class SettingRetrieveResponse(BaseModel):
    """User settings response."""

    ai_mode: Optional[str] = None

    developer: Optional[bool] = None

    last_workspace: Optional[str] = None

    pinned_workspaces: Optional[List[str]] = None

    show_document_navigator: Optional[bool] = None

    show_help_page: Optional[bool] = None

    show_invite_tab: Optional[bool] = None

    show_security_settings: Optional[bool] = None

    show_smart_search: Optional[bool] = None

    show_templates: Optional[bool] = None

    show_thread_visualization: Optional[bool] = None

    subscription: Optional[Subscription] = None
    """Subscription info exposed to frontend in user settings.

    Note: stripe_customer_id is deliberately excluded for security. This is a
    minimal model used in UserSettingsResponse. For full subscription details, use
    GET /subscription endpoint.
    """

    tableviews: Optional[List[Tableview]] = None

    if TYPE_CHECKING:
        # Some versions of Pydantic <2.8.0 have a bug and don’t allow assigning a
        # value to this field, so for compatibility we avoid doing it at runtime.
        __pydantic_extra__: Dict[str, object] = FieldInfo(init=False)  # pyright: ignore[reportIncompatibleVariableOverride]

        # Stub to indicate that arbitrary properties are accepted.
        # To access properties that are not valid identifiers you can use `getattr`, e.g.
        # `getattr(obj, '$type')`
        def __getattr__(self, attr: str) -> object: ...
    else:
        __pydantic_extra__: Dict[str, object]
