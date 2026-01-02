"""Models for datasets module."""

from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class RerankingModel(BaseModel):
    """Reranking model configuration."""

    model_config = ConfigDict(extra="ignore")

    reranking_provider_name: str = Field(description="Rerank model provider")
    reranking_model_name: str = Field(description="Rerank model name")


class MetadataCondition(BaseModel):
    """Metadata filtering condition."""

    model_config = ConfigDict(extra="ignore")

    name: str = Field(description="Metadata field name")
    comparison_operator: Literal[
        "contains",
        "not contains",
        "start with",
        "end with",
        "is",
        "is not",
        "empty",
        "not empty",
        "=",
        "\u2260",
        "!=",
        ">",
        "<",
        "\u2265",
        ">=",
        "\u2264",
        "<=",
        "before",
        "after",
    ] = Field(description="Comparison operator")
    value: Optional[Union[str, int, float]] = Field(None, description="Comparison value")


class MetadataFilteringConditions(BaseModel):
    """Metadata filtering configuration."""

    model_config = ConfigDict(extra="ignore")

    logical_operator: Literal["and", "or"] = Field(description="Logical operator")
    conditions: List[MetadataCondition] = Field(description="Filtering conditions")


class RetrievalModel(BaseModel):
    """Retrieval model configuration."""

    model_config = ConfigDict(extra="ignore")

    search_method: Literal["hybrid_search", "semantic_search", "full_text_search", "keyword_search"] = Field(description="Search method")
    reranking_enable: Optional[bool] = Field(None, description="Enable reranking")
    reranking_mode: Optional[Literal["weighted_score", "reranking_model"]] = Field(None, description="Reranking mode")
    reranking_model: Optional[RerankingModel] = Field(None, description="Reranking model config")
    weights: Optional[float] = Field(None, description="Semantic search weight")
    top_k: Optional[int] = Field(None, description="Number of results to return")
    score_threshold_enabled: Optional[bool] = Field(None, description="Enable score threshold")
    score_threshold: Optional[float] = Field(None, description="Score threshold")
    metadata_filtering_conditions: Optional[MetadataFilteringConditions] = Field(None, description="Metadata filtering")


class Dataset(BaseModel):
    """Dataset information."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="Dataset ID")
    name: str = Field(description="Dataset name")
    description: Optional[str] = Field(None, description="Dataset description")
    provider: Optional[str] = Field(None, description="Provider type")
    permission: str = Field(description="Permission level")
    data_source_type: Optional[str] = Field(None, description="Data source type")
    indexing_technique: Optional[str] = Field(None, description="Indexing technique")
    app_count: int = Field(description="Number of apps using this dataset")
    document_count: int = Field(description="Number of documents")
    word_count: int = Field(description="Total word count")
    created_by: str = Field(description="Creator ID")
    created_at: int = Field(description="Creation timestamp")
    updated_by: str = Field(description="Updater ID")
    updated_at: int = Field(description="Update timestamp")
    embedding_model: Optional[str] = Field(None, description="Embedding model name")
    embedding_model_provider: Optional[str] = Field(None, description="Embedding model provider")
    embedding_available: Optional[bool] = Field(None, description="Whether embedding is available")
    retrieval_model: Optional[RetrievalModel] = Field(None, description="Retrieval model configuration")
    external_knowledge_api_id: Optional[str] = Field(None, description="External knowledge API ID")
    external_knowledge_id: Optional[str] = Field(None, description="External knowledge ID")


class CreateDatasetRequest(BaseModel):
    """Request model for creating a new dataset."""

    model_config = ConfigDict(extra="ignore")

    name: str = Field(description="Dataset name")
    description: Optional[str] = Field(None, description="Dataset description")
    indexing_technique: Optional[Literal["high_quality", "economy"]] = Field(None, description="Indexing technique")
    permission: Optional[Literal["only_me", "all_team_members", "partial_members"]] = Field("only_me", description="Permission level")
    provider: Optional[Literal["vendor", "external"]] = Field("vendor", description="Provider type")
    external_knowledge_api_id: Optional[str] = Field(None, description="External knowledge API ID")
    external_knowledge_id: Optional[str] = Field(None, description="External knowledge ID")
    embedding_model: Optional[str] = Field(None, description="Embedding model name")
    embedding_model_provider: Optional[str] = Field(None, description="Embedding model provider")
    retrieval_model: Optional[RetrievalModel] = Field(None, description="Retrieval model config")
    partial_member_list: Optional[List[str]] = Field(None, description="Partial member list")


class UpdateDatasetRequest(BaseModel):
    """Request model for updating dataset."""

    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = Field(None, description="Dataset name")
    description: Optional[str] = Field(None, description="Dataset description")
    indexing_technique: Optional[Literal["high_quality", "economy"]] = Field(None, description="Indexing technique")
    permission: Optional[Literal["only_me", "all_team_members", "partial_members"]] = Field(None, description="Permission level")
    embedding_model_provider: Optional[str] = Field(None, description="Embedding model provider")
    embedding_model: Optional[str] = Field(None, description="Embedding model")
    retrieval_model: Optional[RetrievalModel] = Field(None, description="Retrieval parameters")
    partial_member_list: Optional[List[str]] = Field(None, description="Partial member list")


class RetrievalResult(BaseModel):
    """Knowledge base retrieval result."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="Segment ID")
    content: str = Field(description="Segment content")
    score: float = Field(description="Relevance score")
    document_id: str = Field(description="Document ID")
    document_name: str = Field(description="Document name")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata")


class RetrievalRequest(BaseModel):
    """Request model for knowledge base retrieval."""

    model_config = ConfigDict(extra="ignore")

    query: str = Field(description="Search query")
    retrieval_model: Optional[RetrievalModel] = Field(None, description="Retrieval parameters")
    external_retrieval_model: Optional[Dict[str, Any]] = Field(None, description="External retrieval model")


class RetrievalResponse(BaseModel):
    """Response model for retrieval operations."""

    model_config = ConfigDict(extra="ignore")

    query: Dict[str, Any] = Field(description="Search query object")
    retrieval_model: Optional[Dict[str, Any]] = Field(None, description="Retrieval model used")
    records: List[Dict[str, Any]] = Field(description="Retrieved records")


class PaginatedResponse(BaseModel):
    """Generic paginated response model."""

    model_config = ConfigDict(extra="ignore")

    data: List[Any] = Field(description="Response data items")
    has_more: bool = Field(description="Whether more pages are available")
    limit: int = Field(description="Items per page limit")
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number")
