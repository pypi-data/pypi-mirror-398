# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from .._models import BaseModel
from .chunk_metadata import ChunkMetadata

__all__ = ["Chunk"]


class Chunk(BaseModel):
    content: str

    metadata: ChunkMetadata
