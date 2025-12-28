# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, Union, Optional
from typing_extensions import Literal, TypeAlias

from pydantic import Field as FieldInfo

from ..._models import BaseModel
from .embedder_config import EmbedderConfig
from .reranker_config import RerankerConfig
from .query_llm_config import QueryLlmConfig
from .retriever_config import RetrieverConfig
from .title_llm_config import TitleLlmConfig
from .model_citation_config import ModelCitationConfig
from .document_date_extractor_llm_config import DocumentDateExtractorLlmConfig

__all__ = [
    "ConfigRetrieveResponse",
    "AllConfigs",
    "AllConfigsAgentLlm",
    "AllConfigsAgents",
    "AllConfigsDocumentSummaryExtractorLlm",
    "AllConfigsEvaluatorLlm",
    "NonDeveloperConfig",
]


class AllConfigsAgentLlm(BaseModel):
    api_type: Optional[Literal["local", "remote"]] = FieldInfo(alias="API_TYPE", default=None)
    """The inference type (local or remote)."""

    enabled: Optional[bool] = FieldInfo(alias="ENABLED", default=None)
    """Whether to use agent mode for queries."""

    max_char_size_to_answer: Optional[int] = FieldInfo(alias="MAX_CHAR_SIZE_TO_ANSWER", default=None)
    """Maximum character size for history."""

    max_context_tokens: Optional[int] = FieldInfo(alias="MAX_CONTEXT_TOKENS", default=None)
    """
    Maximum tokens for gathered context (applies to evidence buffer and final
    query).
    """

    max_iterations: Optional[int] = FieldInfo(alias="MAX_ITERATIONS", default=None)
    """Maximum agent loop iterations."""

    max_tokens: Optional[int] = FieldInfo(alias="MAX_TOKENS", default=None)
    """Maximum tokens for planning decisions."""

    api_model_name: Optional[str] = FieldInfo(alias="MODEL_NAME", default=None)
    """The name of the model to be used."""

    show_interim_steps: Optional[bool] = FieldInfo(alias="SHOW_INTERIM_STEPS", default=None)
    """Whether to show agent's intermediate steps."""

    system_instruction: Optional[str] = FieldInfo(alias="SYSTEM_INSTRUCTION", default=None)
    """The system instruction for agent planning."""

    temperature: Optional[float] = FieldInfo(alias="TEMPERATURE", default=None)
    """Temperature for agent decisions."""


class AllConfigsAgents(BaseModel):
    agent_model_name: Optional[str] = FieldInfo(alias="AGENT_MODEL_NAME", default=None)
    """The name of the model to be used for the agent."""

    agent_prompt: Optional[str] = FieldInfo(alias="AGENT_PROMPT", default=None)

    enabled: Optional[bool] = FieldInfo(alias="ENABLED", default=None)
    """Whether to use agents mode for queries."""

    llm_agent_temperature: Optional[float] = FieldInfo(alias="LLM_AGENT_TEMPERATURE", default=None)
    """Temperature value for randomness."""

    llm_page_filter_model_name: Optional[str] = FieldInfo(alias="LLM_PAGE_FILTER_MODEL_NAME", default=None)
    """The name of the model to be used for the llm page filter model."""

    llm_page_filter_prompt: Optional[str] = FieldInfo(alias="LLM_PAGE_FILTER_PROMPT", default=None)

    llm_page_filter_temperature: Optional[float] = FieldInfo(alias="LLM_PAGE_FILTER_TEMPERATURE", default=None)
    """Temperature value for randomness."""

    llm_summarise_model_name: Optional[str] = FieldInfo(alias="LLM_SUMMARISE_MODEL_NAME", default=None)
    """The name of the model to be used for the llm summarise model."""

    llm_summarise_prompt: Optional[str] = FieldInfo(alias="LLM_SUMMARISE_PROMPT", default=None)

    llm_summarise_temperature: Optional[float] = FieldInfo(alias="LLM_SUMMARISE_TEMPERATURE", default=None)
    """Temperature value for randomness."""


class AllConfigsDocumentSummaryExtractorLlm(BaseModel):
    api_type: Optional[Literal["local", "remote"]] = FieldInfo(alias="API_TYPE", default=None)
    """The inference type (local or remote)."""

    max_char_context_to_answer: Optional[int] = FieldInfo(alias="MAX_CHAR_CONTEXT_TO_ANSWER", default=None)
    """Maximum characters in document for context."""

    max_tokens: Optional[int] = FieldInfo(alias="MAX_TOKENS", default=None)
    """Maximum number of tokens allowed."""

    api_model_name: Optional[str] = FieldInfo(alias="MODEL_NAME", default=None)
    """The name of the non-reasoning model to be used."""

    system_instruction: Optional[str] = FieldInfo(alias="SYSTEM_INSTRUCTION", default=None)

    temperature: Optional[float] = FieldInfo(alias="TEMPERATURE", default=None)
    """Temperature value for randomness."""


class AllConfigsEvaluatorLlm(BaseModel):
    api_type: Optional[Literal["local", "remote"]] = FieldInfo(alias="API_TYPE", default=None)
    """The inference type (local or remote)."""

    max_char_size_to_answer: Optional[int] = FieldInfo(alias="MAX_CHAR_SIZE_TO_ANSWER", default=None)
    """Maximum character size for evaluation context."""

    max_tokens: Optional[int] = FieldInfo(alias="MAX_TOKENS", default=None)
    """Maximum tokens for evaluation response."""

    api_model_name: Optional[str] = FieldInfo(alias="MODEL_NAME", default=None)
    """The name of the non-reasoning model to be used."""

    system_instruction: Optional[str] = FieldInfo(alias="SYSTEM_INSTRUCTION", default=None)
    """The system instruction for chunk evaluation."""

    temperature: Optional[float] = FieldInfo(alias="TEMPERATURE", default=None)
    """Low temperature for consistent evaluation."""


class AllConfigs(BaseModel):
    agent_llm: Optional[AllConfigsAgentLlm] = FieldInfo(alias="AgentLLM", default=None)

    agents: Optional[AllConfigsAgents] = FieldInfo(alias="Agents", default=None)

    chunker: Optional[object] = FieldInfo(alias="Chunker", default=None)

    document_date_extractor_llm: Optional[DocumentDateExtractorLlmConfig] = FieldInfo(
        alias="DocumentDateExtractorLLM", default=None
    )

    document_summary_extractor_llm: Optional[AllConfigsDocumentSummaryExtractorLlm] = FieldInfo(
        alias="DocumentSummaryExtractorLLM", default=None
    )

    embedder: Optional[EmbedderConfig] = FieldInfo(alias="Embedder", default=None)

    evaluator_llm: Optional[AllConfigsEvaluatorLlm] = FieldInfo(alias="EvaluatorLLM", default=None)

    api_model_citation: Optional[ModelCitationConfig] = FieldInfo(alias="ModelCitation", default=None)

    parser: Optional[object] = FieldInfo(alias="Parser", default=None)

    query_llm: Optional[QueryLlmConfig] = FieldInfo(alias="QueryLLM", default=None)

    reranker: Optional[RerankerConfig] = FieldInfo(alias="Reranker", default=None)

    retriever: Optional[RetrieverConfig] = FieldInfo(alias="Retriever", default=None)

    title_llm: Optional[TitleLlmConfig] = FieldInfo(alias="TitleLLM", default=None)


class NonDeveloperConfig(BaseModel):
    """Limited configuration response for non-developer users"""

    agent_llm: Dict[str, bool] = FieldInfo(alias="AgentLLM")

    query_llm: Dict[str, str] = FieldInfo(alias="QueryLLM")


ConfigRetrieveResponse: TypeAlias = Union[AllConfigs, NonDeveloperConfig]
