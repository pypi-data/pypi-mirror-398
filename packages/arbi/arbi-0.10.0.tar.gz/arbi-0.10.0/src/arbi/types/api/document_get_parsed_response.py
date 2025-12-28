# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Optional

from ..chunk import Chunk
from ..._models import BaseModel

__all__ = ["DocumentGetParsedResponse", "Metadata"]


class Metadata(BaseModel):
    doc_ext_id: Optional[str] = None

    file_name: Optional[str] = None

    re_ocred: Optional[bool] = None

    total_number_of_pages: Optional[int] = None


class DocumentGetParsedResponse(BaseModel):
    metadata: Metadata

    chunks: Optional[List[Chunk]] = None

    footnotes: Optional[Dict[str, str]] = None
