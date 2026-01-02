"""Models API client for Dify API."""

from .._base import BaseClient
from .models import EmbeddingModelResponse


class ModelsClient:
    """Client for model-related operations.

    Provides methods for listing available embedding models.
    """

    def __init__(self, base_client: BaseClient) -> None:
        """Initialize the models client.

        Args:
            base_client: Base HTTP client for making API requests
        """
        self._client = base_client

    def list_embedding_models(self) -> EmbeddingModelResponse:
        """Get list of available text embedding models.

        Returns:
            List of available embedding models

        Raises:
            DifyAPIError: For API errors
        """
        response = self._client.get("/v1/workspaces/current/models/model-types/text-embedding")
        return EmbeddingModelResponse(**response)
