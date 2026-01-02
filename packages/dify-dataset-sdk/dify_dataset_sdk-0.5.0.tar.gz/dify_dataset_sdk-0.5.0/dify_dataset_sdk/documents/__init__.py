"""Documents module for Dify Dataset SDK."""

from .client import DocumentsClient
from .models import (
    BatchDocumentStatusRequest,
    CreateDocumentByFileData,
    CreateDocumentByTextRequest,
    DataSourceInfo,
    Document,
    DocumentResponse,
    IndexingStatus,
    IndexingStatusResponse,
    PreProcessingRule,
    ProcessRule,
    ProcessRuleConfig,
    Segmentation,
    SubchunkSegmentation,
    UpdateDocumentByFileData,
    UpdateDocumentByTextRequest,
)

__all__ = [
    "DocumentsClient",
    "Document",
    "DocumentResponse",
    "DataSourceInfo",
    "IndexingStatus",
    "IndexingStatusResponse",
    "ProcessRule",
    "ProcessRuleConfig",
    "PreProcessingRule",
    "Segmentation",
    "SubchunkSegmentation",
    "CreateDocumentByTextRequest",
    "CreateDocumentByFileData",
    "UpdateDocumentByTextRequest",
    "UpdateDocumentByFileData",
    "BatchDocumentStatusRequest",
]
