"""Dify Dataset SDK - Python SDK for Dify Dataset API.

This SDK provides a modular interface to the Dify Knowledge Base API with
separate clients for different resource types:

- DifyDatasetClient: Main client with access to all sub-clients
- datasets: Dataset management (create, list, update, delete, retrieve)
- documents: Document management (text/file upload, update, delete)
- segments: Segment and child chunk management
- tags: Knowledge tag management
- metadata: Metadata field management
- models: Embedding model listing

Example:
    ```python
    from dify_dataset_sdk import DifyDatasetClient

    client = DifyDatasetClient(api_key="your-api-key")

    # Dataset operations
    dataset = client.datasets.create(name="My Knowledge Base")

    # Document operations
    doc = client.documents.create_by_text(
        dataset_id=dataset.id,
        name="My Document",
        text="Document content..."
    )

    # Segment operations
    segments = client.segments.list(dataset.id, doc.document.id)

    # Tag operations
    tag = client.tags.create(name="Important")
    client.tags.bind_to_dataset(dataset.id, tag_ids=[tag.id])

    # Metadata operations
    fields = client.metadata.list(dataset.id)

    # Model operations
    models = client.models.list_embedding_models()
    ```
"""

# Exceptions
from ._exceptions import (
    ERROR_CODE_MAPPING,
    DifyAPIError,
    DifyAuthenticationError,
    DifyConflictError,
    DifyConnectionError,
    DifyError,
    DifyNotFoundError,
    DifyServerError,
    DifyTimeoutError,
    DifyValidationError,
)
from .client import DifyDatasetClient

# Dataset models
from .datasets import (
    CreateDatasetRequest,
    Dataset,
    MetadataCondition,
    MetadataFilteringConditions,
    PaginatedResponse,
    RerankingModel,
    RetrievalModel,
    RetrievalRequest,
    RetrievalResponse,
    RetrievalResult,
    UpdateDatasetRequest,
)

# Document models
from .documents import (
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

# Model API models
from .models_api import EmbeddingModelResponse

# Segment models
from .segments import (
    ChildChunk,
    ChildChunkResponse,
    CreateChildChunkRequest,
    CreateSegmentRequest,
    Segment,
    SegmentResponse,
    UpdateChildChunkRequest,
    UpdateSegmentRequest,
)

# Metadata models
from .metadata import (
    CreateMetadataRequest,
    DocumentMetadata,
    Metadata,
    MetadataListResponse,
    MetadataValue,
    UpdateDocumentMetadataRequest,
    UpdateMetadataRequest,
)

# Tag models
from .tags import (
    BindDatasetToTagRequest,
    CreateKnowledgeTagRequest,
    DatasetTagsResponse,
    DeleteKnowledgeTagRequest,
    KnowledgeTag,
    UnbindDatasetFromTagRequest,
    UpdateKnowledgeTagRequest,
)

__version__ = "0.5.0"

__all__ = [
    # Main client
    "DifyDatasetClient",
    # Exceptions
    "DifyError",
    "DifyAPIError",
    "DifyAuthenticationError",
    "DifyValidationError",
    "DifyNotFoundError",
    "DifyConflictError",
    "DifyServerError",
    "DifyConnectionError",
    "DifyTimeoutError",
    "ERROR_CODE_MAPPING",
    # Dataset models
    "Dataset",
    "CreateDatasetRequest",
    "UpdateDatasetRequest",
    "RetrievalModel",
    "RerankingModel",
    "MetadataCondition",
    "MetadataFilteringConditions",
    "RetrievalRequest",
    "RetrievalResponse",
    "RetrievalResult",
    "PaginatedResponse",
    # Document models
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
    # Segment models
    "Segment",
    "SegmentResponse",
    "ChildChunk",
    "ChildChunkResponse",
    "CreateSegmentRequest",
    "UpdateSegmentRequest",
    "CreateChildChunkRequest",
    "UpdateChildChunkRequest",
    # Tag models
    "KnowledgeTag",
    "CreateKnowledgeTagRequest",
    "UpdateKnowledgeTagRequest",
    "DeleteKnowledgeTagRequest",
    "BindDatasetToTagRequest",
    "UnbindDatasetFromTagRequest",
    "DatasetTagsResponse",
    # Metadata models
    "Metadata",
    "MetadataValue",
    "DocumentMetadata",
    "MetadataListResponse",
    "CreateMetadataRequest",
    "UpdateMetadataRequest",
    "UpdateDocumentMetadataRequest",
    # Model API models
    "EmbeddingModelResponse",
]
