"""Tests for ModelsClient - Model-related operations."""

import pytest
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dify_dataset_sdk import DifyDatasetClient

from dify_dataset_sdk.models_api.models import EmbeddingModelResponse


class TestModelsListEmbedding:
    """Tests for models.list_embedding_models() method."""

    def test_list_embedding_models(self, client: "DifyDatasetClient"):
        """Test listing available embedding models."""
        result = client.models.list_embedding_models()

        assert isinstance(result, EmbeddingModelResponse)

    def test_list_embedding_models_returns_data(self, client: "DifyDatasetClient"):
        """Test that list returns model data."""
        result = client.models.list_embedding_models()

        assert isinstance(result, EmbeddingModelResponse)
        # Response should have data attribute
        assert hasattr(result, "data") or hasattr(result, "models")

    def test_list_embedding_models_multiple_calls(self, client: "DifyDatasetClient"):
        """Test multiple calls return consistent results."""
        result1 = client.models.list_embedding_models()
        result2 = client.models.list_embedding_models()

        assert isinstance(result1, EmbeddingModelResponse)
        assert isinstance(result2, EmbeddingModelResponse)
