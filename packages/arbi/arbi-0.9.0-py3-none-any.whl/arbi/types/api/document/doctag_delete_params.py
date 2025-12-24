# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, TypedDict

from ...._types import SequenceNotStr

__all__ = ["DoctagDeleteParams"]


class DoctagDeleteParams(TypedDict, total=False):
    doc_ext_ids: Required[SequenceNotStr[str]]

    tag_ext_id: Required[str]
