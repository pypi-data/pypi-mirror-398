"""Main client for Dify Dataset SDK."""

from typing import Any

from ._base import BaseClient
from .datasets import DatasetsClient
from .documents import DocumentsClient
from .models_api import ModelsClient
from .metadata import MetadataClient
from .segments import SegmentsClient
from .tags import TagsClient


class DifyDatasetClient:
    """Dify Knowledge Base API client for comprehensive knowledge management.

    This client provides access to all Dify Knowledge Base API endpoints including:
    - datasets: Dataset management (CRUD operations, retrieval)
    - documents: Document management (text/file upload, update, delete)
    - segments: Segment management (create, update, delete, query, child chunks)
    - tags: Knowledge tag management
    - metadata: Metadata field management
    - models: Embedding models listing

    Example:
        ```python
        from dify_dataset_sdk import DifyDatasetClient

        client = DifyDatasetClient(api_key="your-api-key")

        # Dataset operations
        dataset = client.datasets.create(name="My Knowledge Base")
        datasets = client.datasets.list()

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

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.dify.ai",
        timeout: float = 30.0,
    ) -> None:
        """Initialize the Dify client.

        Args:
            api_key: Dify API key for authentication
            base_url: Base URL for Dify API (default: https://api.dify.ai)
            timeout: Request timeout in seconds (default: 30.0)

        Raises:
            ValueError: If api_key is empty or None
        """
        self._base = BaseClient(api_key, base_url, timeout)
        self.datasets = DatasetsClient(self._base)
        self.documents = DocumentsClient(self._base)
        self.segments = SegmentsClient(self._base)
        self.tags = TagsClient(self._base)
        self.metadata = MetadataClient(self._base)
        self.models = ModelsClient(self._base)

    def close(self) -> None:
        """Close the HTTP client connection and cleanup resources."""
        self._base.close()

    def __enter__(self) -> "DifyDatasetClient":
        """Enter context manager.

        Returns:
            Self for method chaining
        """
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager and cleanup resources.

        Args:
            exc_type: Exception type
            exc_val: Exception value
            exc_tb: Exception traceback
        """
        self.close()
