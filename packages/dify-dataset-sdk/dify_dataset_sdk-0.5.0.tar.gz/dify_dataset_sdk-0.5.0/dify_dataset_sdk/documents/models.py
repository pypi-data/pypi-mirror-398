"""Models for documents module."""

from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from ..datasets.models import RetrievalModel


# ===== Processing Rules =====
class PreProcessingRule(BaseModel):
    """Preprocessing rule configuration."""

    model_config = ConfigDict(extra="ignore")

    id: Literal["remove_extra_spaces", "remove_urls_emails"] = Field(description="Rule ID")
    enabled: bool = Field(description="Whether the rule is enabled")


class Segmentation(BaseModel):
    """Text segmentation configuration."""

    model_config = ConfigDict(extra="ignore")

    separator: str = Field(default="\n", description="Segment separator")
    max_tokens: int = Field(default=1000, description="Maximum tokens per segment")


class SubchunkSegmentation(BaseModel):
    """Subchunk segmentation configuration for hierarchical mode."""

    model_config = ConfigDict(extra="ignore")

    separator: str = Field(default="***", description="Subchunk separator")
    max_tokens: int = Field(description="Maximum tokens per subchunk")
    chunk_overlap: Optional[int] = Field(None, description="Chunk overlap size")


class ProcessRuleConfig(BaseModel):
    """Custom process rule configuration."""

    model_config = ConfigDict(extra="ignore")

    pre_processing_rules: List[PreProcessingRule] = Field(description="Preprocessing rules")
    segmentation: Segmentation = Field(description="Segmentation configuration")
    parent_mode: Optional[Literal["full-doc", "paragraph"]] = Field(None, description="Parent chunk recall mode")
    subchunk_segmentation: Optional[SubchunkSegmentation] = Field(None, description="Subchunk segmentation config")


class ProcessRule(BaseModel):
    """Processing rules for document indexing."""

    model_config = ConfigDict(extra="ignore")

    mode: Literal["automatic", "custom", "hierarchical"] = Field(description="Processing mode")
    rules: Optional[ProcessRuleConfig] = Field(None, description="Custom processing rules")


# ===== Document Models =====
class DataSourceInfo(BaseModel):
    """Information about the data source for a document."""

    model_config = ConfigDict(extra="ignore")

    upload_file_id: Optional[str] = Field(None, description="ID of uploaded file")


class Document(BaseModel):
    """Document information in a dataset."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="Document ID")
    position: int = Field(description="Document position")
    data_source_type: str = Field(description="Data source type")
    data_source_info: Optional[DataSourceInfo] = Field(None, description="Data source info")
    dataset_process_rule_id: Optional[str] = Field(None, description="Process rule ID")
    name: str = Field(description="Document name")
    created_from: str = Field(description="Creation source")
    created_by: str = Field(description="Creator ID")
    created_at: int = Field(description="Creation timestamp")
    tokens: Optional[int] = Field(None, description="Token count")
    indexing_status: str = Field(description="Indexing status")
    error: Optional[str] = Field(None, description="Error message")
    enabled: bool = Field(description="Whether document is enabled")
    disabled_at: Optional[int] = Field(None, description="Disabled timestamp")
    disabled_by: Optional[str] = Field(None, description="User who disabled")
    archived: bool = Field(description="Whether document is archived")
    display_status: Optional[str] = Field(None, description="Display status")
    word_count: Optional[int] = Field(None, description="Word count")
    hit_count: int = Field(description="Hit count")
    doc_form: str = Field(description="Document form")


class IndexingStatus(BaseModel):
    """Document indexing status information."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="Document ID")
    indexing_status: str = Field(description="Indexing status")
    processing_started_at: Optional[float] = Field(None, description="Processing start time")
    parsing_completed_at: Optional[float] = Field(None, description="Parsing completion time")
    cleaning_completed_at: Optional[float] = Field(None, description="Cleaning completion time")
    splitting_completed_at: Optional[float] = Field(None, description="Splitting completion time")
    completed_at: Optional[float] = Field(None, description="Overall completion time")
    paused_at: Optional[float] = Field(None, description="Pause time")
    error: Optional[str] = Field(None, description="Error message")
    stopped_at: Optional[float] = Field(None, description="Stop time")
    completed_segments: int = Field(description="Number of completed segments")
    total_segments: int = Field(description="Total number of segments")


# ===== Request Models =====
class CreateDocumentByTextRequest(BaseModel):
    """Request model for creating document by text."""

    model_config = ConfigDict(extra="ignore")

    name: str = Field(description="Document name")
    text: str = Field(description="Document content")
    indexing_technique: Optional[Literal["high_quality", "economy"]] = Field("high_quality", description="Indexing technique")
    doc_form: Optional[Literal["text_model", "hierarchical_model", "qa_model"]] = Field(None, description="Document form")
    doc_language: Optional[str] = Field(None, description="Document language for Q&A mode")
    process_rule: Optional[ProcessRule] = Field(None, description="Processing rules")
    retrieval_model: Optional[RetrievalModel] = Field(None, description="Retrieval model config")
    embedding_model: Optional[str] = Field(None, description="Embedding model name")
    embedding_model_provider: Optional[str] = Field(None, description="Embedding model provider")


class CreateDocumentByFileData(BaseModel):
    """Data payload for file upload."""

    model_config = ConfigDict(extra="ignore")

    original_document_id: Optional[str] = Field(None, description="Original document ID for update")
    indexing_technique: Optional[Literal["high_quality", "economy"]] = Field("high_quality", description="Indexing technique")
    doc_form: Optional[Literal["text_model", "hierarchical_model", "qa_model"]] = Field(None, description="Document form")
    doc_language: Optional[str] = Field(None, description="Document language for Q&A mode")
    process_rule: Optional[ProcessRule] = Field(None, description="Processing rules")
    retrieval_model: Optional[RetrievalModel] = Field(None, description="Retrieval model config")
    embedding_model: Optional[str] = Field(None, description="Embedding model name")
    embedding_model_provider: Optional[str] = Field(None, description="Embedding model provider")


class UpdateDocumentByTextRequest(BaseModel):
    """Request model for updating document by text."""

    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = Field(None, description="Document name")
    text: Optional[str] = Field(None, description="Document content")
    process_rule: Optional[ProcessRule] = Field(None, description="Processing rules")


class UpdateDocumentByFileData(BaseModel):
    """Data payload for file update."""

    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = Field(None, description="Document name")
    process_rule: Optional[ProcessRule] = Field(None, description="Processing rules")


class BatchDocumentStatusRequest(BaseModel):
    """Request model for batch document status update."""

    model_config = ConfigDict(extra="ignore")

    document_ids: List[str] = Field(description="Document ID list")


# ===== Response Models =====
class DocumentResponse(BaseModel):
    """Response model for document operations."""

    model_config = ConfigDict(extra="ignore")

    document: Document = Field(description="Document information")
    batch: str = Field(description="Batch ID for tracking")


class IndexingStatusResponse(BaseModel):
    """Response model for indexing status."""

    model_config = ConfigDict(extra="ignore")

    data: List[IndexingStatus] = Field(description="Indexing status list")
