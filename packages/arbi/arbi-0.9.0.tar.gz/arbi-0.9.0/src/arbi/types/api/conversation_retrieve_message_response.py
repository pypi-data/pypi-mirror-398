# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Union, Optional
from datetime import datetime
from typing_extensions import Literal, Annotated, TypeAlias

from ..chunk import Chunk
from ..._utils import PropertyInfo
from ..._models import BaseModel

__all__ = [
    "ConversationRetrieveMessageResponse",
    "Tools",
    "ToolsModelCitationTool",
    "ToolsModelCitationToolToolResponses",
    "ToolsRetrievalChunkToolOutput",
    "ToolsRetrievalFullContextToolOutput",
    "ToolsTraceTool",
]


class ToolsModelCitationToolToolResponses(BaseModel):
    """Data for a single citation"""

    chunk_ids: List[str]

    offset_end: int

    offset_start: int

    statement: str


class ToolsModelCitationTool(BaseModel):
    description: Optional[str] = None

    name: Optional[Literal["model_citation"]] = None

    tool_responses: Optional[Dict[str, ToolsModelCitationToolToolResponses]] = None


class ToolsRetrievalChunkToolOutput(BaseModel):
    description: Optional[str] = None

    name: Optional[Literal["retrieval_chunk"]] = None

    tool_args: Optional[Dict[str, List[str]]] = None

    tool_responses: Optional[Dict[str, List[Chunk]]] = None


class ToolsRetrievalFullContextToolOutput(BaseModel):
    description: Optional[str] = None

    name: Optional[Literal["retrieval_full_context"]] = None

    tool_args: Optional[Dict[str, object]] = None

    tool_responses: Optional[Dict[str, List[Chunk]]] = None


class ToolsTraceTool(BaseModel):
    """Execution trace tool that captures the full execution history of a request."""

    description: Optional[str] = None

    duration_seconds: Optional[float] = None

    name: Optional[Literal["trace"]] = None

    start_time: Optional[float] = None

    steps: Optional[List[Dict[str, object]]] = None

    trace_id: Optional[str] = None


Tools: TypeAlias = Annotated[
    Union[ToolsModelCitationTool, ToolsRetrievalChunkToolOutput, ToolsRetrievalFullContextToolOutput, ToolsTraceTool],
    PropertyInfo(discriminator="name"),
]


class ConversationRetrieveMessageResponse(BaseModel):
    """DTO for API responses to frontend - all fields guaranteed to be present"""

    content: str

    conversation_ext_id: str

    created_at: datetime

    created_by_ext_id: str

    external_id: str

    role: Literal["user", "assistant", "system"]

    config_ext_id: Optional[str] = None

    parent_message_ext_id: Optional[str] = None

    shared: Optional[bool] = None

    tools: Optional[Dict[str, Tools]] = None
