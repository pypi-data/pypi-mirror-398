"""Tags module for Dify Dataset SDK."""

from .client import TagsClient
from .models import (
    BindDatasetToTagRequest,
    CreateKnowledgeTagRequest,
    DatasetTagsResponse,
    DeleteKnowledgeTagRequest,
    KnowledgeTag,
    UnbindDatasetFromTagRequest,
    UpdateKnowledgeTagRequest,
)

__all__ = [
    "TagsClient",
    "KnowledgeTag",
    "CreateKnowledgeTagRequest",
    "UpdateKnowledgeTagRequest",
    "DeleteKnowledgeTagRequest",
    "BindDatasetToTagRequest",
    "UnbindDatasetFromTagRequest",
    "DatasetTagsResponse",
]
