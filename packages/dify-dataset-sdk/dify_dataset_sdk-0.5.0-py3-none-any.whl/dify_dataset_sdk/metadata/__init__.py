"""Metadata module for Dify Dataset SDK."""

from .client import MetadataClient
from .models import (
    CreateMetadataRequest,
    DocumentMetadata,
    Metadata,
    MetadataListResponse,
    MetadataValue,
    UpdateDocumentMetadataRequest,
    UpdateMetadataRequest,
)

__all__ = [
    "MetadataClient",
    "Metadata",
    "MetadataValue",
    "DocumentMetadata",
    "MetadataListResponse",
    "CreateMetadataRequest",
    "UpdateMetadataRequest",
    "UpdateDocumentMetadataRequest",
]
