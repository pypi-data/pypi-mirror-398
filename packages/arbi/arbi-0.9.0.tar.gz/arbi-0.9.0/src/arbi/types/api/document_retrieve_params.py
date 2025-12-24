# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from ..._types import SequenceNotStr
from ..._utils import PropertyInfo

__all__ = ["DocumentRetrieveParams"]


class DocumentRetrieveParams(TypedDict, total=False):
    external_ids: Required[SequenceNotStr[str]]

    workspace_key: Annotated[str, PropertyInfo(alias="workspace-key")]
