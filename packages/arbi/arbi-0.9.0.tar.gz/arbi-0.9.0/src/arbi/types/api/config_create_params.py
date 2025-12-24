# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Literal, Annotated, TypedDict

from ..._utils import PropertyInfo
from .parser_config_param import ParserConfigParam
from .chunker_config_param import ChunkerConfigParam
from .embedder_config_param import EmbedderConfigParam
from .reranker_config_param import RerankerConfigParam
from .query_llm_config_param import QueryLlmConfigParam
from .retriever_config_param import RetrieverConfigParam
from .title_llm_config_param import TitleLlmConfigParam
from .model_citation_config_param import ModelCitationConfigParam
from .document_date_extractor_llm_config_param import DocumentDateExtractorLlmConfigParam

__all__ = ["ConfigCreateParams", "AgentLlm", "Agents"]


class ConfigCreateParams(TypedDict, total=False):
    agent_llm: Annotated[Optional[AgentLlm], PropertyInfo(alias="AgentLLM")]

    agents: Annotated[Optional[Agents], PropertyInfo(alias="Agents")]

    chunker: Annotated[Optional[ChunkerConfigParam], PropertyInfo(alias="Chunker")]

    document_date_extractor_llm: Annotated[
        Optional[DocumentDateExtractorLlmConfigParam], PropertyInfo(alias="DocumentDateExtractorLLM")
    ]

    embedder: Annotated[Optional[EmbedderConfigParam], PropertyInfo(alias="Embedder")]

    model_citation: Annotated[Optional[ModelCitationConfigParam], PropertyInfo(alias="ModelCitation")]

    parent_message_ext_id: Optional[str]

    parser: Annotated[Optional[ParserConfigParam], PropertyInfo(alias="Parser")]

    query_llm: Annotated[Optional[QueryLlmConfigParam], PropertyInfo(alias="QueryLLM")]

    reranker: Annotated[Optional[RerankerConfigParam], PropertyInfo(alias="Reranker")]

    retriever: Annotated[Optional[RetrieverConfigParam], PropertyInfo(alias="Retriever")]

    title: str

    title_llm: Annotated[Optional[TitleLlmConfigParam], PropertyInfo(alias="TitleLLM")]


class AgentLlm(TypedDict, total=False):
    api_type: Annotated[Literal["local", "remote"], PropertyInfo(alias="API_TYPE")]
    """The inference type (local or remote)."""

    enabled: Annotated[bool, PropertyInfo(alias="ENABLED")]
    """Whether to use agent mode for queries."""

    max_char_size_to_answer: Annotated[int, PropertyInfo(alias="MAX_CHAR_SIZE_TO_ANSWER")]
    """Maximum character size for history."""

    max_context_tokens: Annotated[int, PropertyInfo(alias="MAX_CONTEXT_TOKENS")]
    """
    Maximum tokens for gathered context (applies to evidence buffer and final
    query).
    """

    max_iterations: Annotated[int, PropertyInfo(alias="MAX_ITERATIONS")]
    """Maximum agent loop iterations."""

    max_tokens: Annotated[int, PropertyInfo(alias="MAX_TOKENS")]
    """Maximum tokens for planning decisions."""

    model_name: Annotated[str, PropertyInfo(alias="MODEL_NAME")]
    """The name of the model to be used."""

    show_interim_steps: Annotated[bool, PropertyInfo(alias="SHOW_INTERIM_STEPS")]
    """Whether to show agent's intermediate steps."""

    system_instruction: Annotated[str, PropertyInfo(alias="SYSTEM_INSTRUCTION")]
    """The system instruction for agent planning."""

    temperature: Annotated[float, PropertyInfo(alias="TEMPERATURE")]
    """Temperature for agent decisions."""


class Agents(TypedDict, total=False):
    agent_model_name: Annotated[str, PropertyInfo(alias="AGENT_MODEL_NAME")]
    """The name of the model to be used for the agent."""

    agent_prompt: Annotated[str, PropertyInfo(alias="AGENT_PROMPT")]

    enabled: Annotated[bool, PropertyInfo(alias="ENABLED")]
    """Whether to use agents mode for queries."""

    llm_agent_temperature: Annotated[float, PropertyInfo(alias="LLM_AGENT_TEMPERATURE")]
    """Temperature value for randomness."""

    llm_page_filter_model_name: Annotated[str, PropertyInfo(alias="LLM_PAGE_FILTER_MODEL_NAME")]
    """The name of the model to be used for the llm page filter model."""

    llm_page_filter_prompt: Annotated[str, PropertyInfo(alias="LLM_PAGE_FILTER_PROMPT")]

    llm_page_filter_temperature: Annotated[float, PropertyInfo(alias="LLM_PAGE_FILTER_TEMPERATURE")]
    """Temperature value for randomness."""

    llm_summarise_model_name: Annotated[str, PropertyInfo(alias="LLM_SUMMARISE_MODEL_NAME")]
    """The name of the model to be used for the llm summarise model."""

    llm_summarise_prompt: Annotated[str, PropertyInfo(alias="LLM_SUMMARISE_PROMPT")]

    llm_summarise_temperature: Annotated[float, PropertyInfo(alias="LLM_SUMMARISE_TEMPERATURE")]
    """Temperature value for randomness."""
