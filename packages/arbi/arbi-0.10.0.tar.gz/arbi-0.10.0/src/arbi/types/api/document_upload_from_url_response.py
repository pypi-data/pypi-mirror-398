# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List

from ..._models import BaseModel

__all__ = ["DocumentUploadFromURLResponse"]


class DocumentUploadFromURLResponse(BaseModel):
    """Response for document upload operations.

    Returns array of document IDs in the same order as uploaded files.
    """

    doc_ext_ids: List[str]
