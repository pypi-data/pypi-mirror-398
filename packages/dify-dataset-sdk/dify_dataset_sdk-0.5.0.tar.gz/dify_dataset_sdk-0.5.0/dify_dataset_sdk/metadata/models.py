"""Models for metadata module."""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class Metadata(BaseModel):
    """Metadata field information."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="Metadata field ID")
    type: str = Field(description="Field type")
    name: str = Field(description="Field name")
    use_count: Optional[int] = Field(None, description="Usage count")


class MetadataValue(BaseModel):
    """Metadata value information."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="Metadata field ID")
    value: str = Field(description="Metadata value")
    name: str = Field(description="Field name")


class DocumentMetadata(BaseModel):
    """Document metadata association."""

    model_config = ConfigDict(extra="ignore")

    document_id: str = Field(description="Document ID")
    metadata_list: List[MetadataValue] = Field(description="Metadata values")


class CreateMetadataRequest(BaseModel):
    """Request model for creating metadata field."""

    model_config = ConfigDict(extra="ignore")

    type: str = Field(description="Metadata type")
    name: str = Field(description="Metadata name")


class UpdateMetadataRequest(BaseModel):
    """Request model for updating metadata field."""

    model_config = ConfigDict(extra="ignore")

    name: str = Field(description="Metadata name")


class UpdateDocumentMetadataRequest(BaseModel):
    """Request model for updating document metadata."""

    model_config = ConfigDict(extra="ignore")

    operation_data: List[DocumentMetadata] = Field(description="Document metadata operations")


class MetadataListResponse(BaseModel):
    """Response model for metadata list."""

    model_config = ConfigDict(extra="ignore")

    doc_metadata: List[Metadata] = Field(description="Metadata fields")
    built_in_field_enabled: bool = Field(description="Built-in field enabled status")
