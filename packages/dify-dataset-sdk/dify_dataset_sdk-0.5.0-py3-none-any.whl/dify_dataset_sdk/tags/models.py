"""Models for tags module."""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ===== Knowledge Tag Models =====
class KnowledgeTag(BaseModel):
    """Knowledge base tag information."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="Tag ID")
    name: str = Field(description="Tag name")
    color: Optional[str] = Field(None, description="Tag color")
    created_at: Optional[int] = Field(None, description="Creation timestamp")
    updated_at: Optional[int] = Field(None, description="Update timestamp")
    binding_count: Optional[int] = Field(None, description="Number of bindings")


class DatasetTagsResponse(BaseModel):
    """Response model for dataset tag list."""

    model_config = ConfigDict(extra="ignore")

    data: List[KnowledgeTag] = Field(description="Tag list")
    total: Optional[int] = Field(None, description="Total tag count")


class CreateKnowledgeTagRequest(BaseModel):
    """Request model for creating knowledge tag."""

    model_config = ConfigDict(extra="ignore")

    name: str = Field(description="Tag name", max_length=50)


class UpdateKnowledgeTagRequest(BaseModel):
    """Request model for updating knowledge tag."""

    model_config = ConfigDict(extra="ignore")

    name: str = Field(description="Tag name", max_length=50)
    tag_id: str = Field(description="Tag ID")


class DeleteKnowledgeTagRequest(BaseModel):
    """Request model for deleting knowledge tag."""

    model_config = ConfigDict(extra="ignore")

    tag_id: str = Field(description="Tag ID")


class BindDatasetToTagRequest(BaseModel):
    """Request model for binding dataset to knowledge tag."""

    model_config = ConfigDict(extra="ignore")

    tag_ids: List[str] = Field(description="Tag ID list")
    target_id: str = Field(description="Dataset ID")


class UnbindDatasetFromTagRequest(BaseModel):
    """Request model for unbinding dataset from knowledge tag."""

    model_config = ConfigDict(extra="ignore")

    tag_id: str = Field(description="Tag ID")
    target_id: str = Field(description="Dataset ID")


 
