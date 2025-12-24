# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, TypedDict

from .chunk_metadata_param import ChunkMetadataParam

__all__ = ["ChunkParam"]


class ChunkParam(TypedDict, total=False):
    content: Required[str]

    metadata: Required[ChunkMetadataParam]
