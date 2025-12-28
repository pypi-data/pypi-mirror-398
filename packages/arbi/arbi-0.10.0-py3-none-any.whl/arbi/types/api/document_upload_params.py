# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Required, Annotated, TypedDict

from ..._types import FileTypes, SequenceNotStr
from ..._utils import PropertyInfo

__all__ = ["DocumentUploadParams"]


class DocumentUploadParams(TypedDict, total=False):
    workspace_ext_id: Required[str]

    files: Required[SequenceNotStr[FileTypes]]
    """Multiple files to upload"""

    config_ext_id: Optional[str]
    """Configuration to use for processing"""

    shared: bool
    """Whether the document should be shared with workspace members"""

    workspace_key: Annotated[str, PropertyInfo(alias="workspace-key")]
