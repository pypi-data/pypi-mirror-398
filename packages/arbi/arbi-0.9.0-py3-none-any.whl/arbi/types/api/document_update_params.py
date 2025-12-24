# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union, Iterable, Optional
from datetime import date
from typing_extensions import Required, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["DocumentUpdateParams", "Document", "DocumentDocMetadata"]


class DocumentUpdateParams(TypedDict, total=False):
    documents: Required[Iterable[Document]]

    workspace_key: Annotated[str, PropertyInfo(alias="workspace-key")]


class DocumentDocMetadata(TypedDict, total=False):
    """Structured model for document metadata stored in JSONB column."""

    doc_date: Annotated[Union[str, date, None], PropertyInfo(format="iso8601")]

    doc_summary: Optional[str]

    title: Optional[str]


class Document(TypedDict, total=False):
    """Document update request - identifies doc and fields to update."""

    external_id: Required[str]

    doc_metadata: Optional[DocumentDocMetadata]
    """Structured model for document metadata stored in JSONB column."""

    shared: Optional[bool]
