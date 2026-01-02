"""Models for segments module."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class Segment(BaseModel):
    """Document segment information."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="Segment ID")
    position: int = Field(description="Segment position")
    document_id: str = Field(description="Document ID")
    content: str = Field(description="Segment content")
    answer: Optional[str] = Field(None, description="Answer content for Q&A mode")
    word_count: int = Field(description="Word count")
    tokens: int = Field(description="Token count")
    keywords: Optional[List[str]] = Field(None, description="Keywords")
    index_node_id: str = Field(description="Index node ID")
    index_node_hash: str = Field(description="Index node hash")
    hit_count: int = Field(description="Hit count")
    enabled: bool = Field(description="Whether segment is enabled")
    disabled_at: Optional[int] = Field(None, description="Disabled timestamp")
    disabled_by: Optional[str] = Field(None, description="User who disabled")
    status: str = Field(description="Segment status")
    created_by: str = Field(description="Creator ID")
    created_at: int = Field(description="Creation timestamp")
    indexing_at: int = Field(description="Indexing timestamp")
    completed_at: Optional[int] = Field(None, description="Completion timestamp")
    error: Optional[str] = Field(None, description="Error message")
    stopped_at: Optional[int] = Field(None, description="Stop timestamp")


class ChildChunk(BaseModel):
    """Child chunk information for hierarchical segments."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="Child chunk ID")
    content: str = Field(description="Child chunk content")
    position: int = Field(description="Position in parent segment")
    word_count: int = Field(description="Word count")
    tokens: Optional[int] = Field(None, description="Token count")
    created_at: int = Field(description="Creation timestamp")
    updated_at: int = Field(description="Update timestamp")


# ===== Request Models =====
class CreateSegmentRequest(BaseModel):
    """Request model for creating segments."""

    model_config = ConfigDict(extra="ignore")

    segments: List[Dict[str, Any]] = Field(description="Segment data list")


class UpdateSegmentRequest(BaseModel):
    """Request model for updating segment."""

    model_config = ConfigDict(extra="ignore")

    segment: Dict[str, Any] = Field(description="Segment data")


class CreateChildChunkRequest(BaseModel):
    """Request model for creating child chunk."""

    model_config = ConfigDict(extra="ignore")

    content: str = Field(description="Child chunk content")


class UpdateChildChunkRequest(BaseModel):
    """Request model for updating child chunk."""

    model_config = ConfigDict(extra="ignore")

    content: str = Field(description="Child chunk content")


# ===== Response Models =====
class SegmentResponse(BaseModel):
    """Response model for segment operations."""

    model_config = ConfigDict(extra="ignore")

    data: List[Segment] = Field(description="Segment list")
    doc_form: str = Field(description="Document form")


class ChildChunkResponse(BaseModel):
    """Response model for child chunk operations."""

    model_config = ConfigDict(extra="ignore")

    data: List[ChildChunk] = Field(description="Child chunk list")
