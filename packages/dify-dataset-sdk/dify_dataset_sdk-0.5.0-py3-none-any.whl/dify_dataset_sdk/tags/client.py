"""Tags client for Dify API."""

from typing import Any, Dict, List, Union

from .._base import BaseClient
from .models import (
    BindDatasetToTagRequest,
    CreateKnowledgeTagRequest,
    DatasetTagsResponse,
    DeleteKnowledgeTagRequest,
    KnowledgeTag,
    UnbindDatasetFromTagRequest,
    UpdateKnowledgeTagRequest,
)


class TagsClient:
    """Client for tag management operations."""

    def __init__(self, base_client: BaseClient) -> None:
        """Initialize the tags client.

        Args:
            base_client: Base HTTP client for making API requests
        """
        self._client = base_client

    # ===== Knowledge Tag Operations =====
    def create(self, name: str) -> KnowledgeTag:
        """Create a new knowledge type tag.

        Args:
            name: Tag name (max 50 characters)

        Returns:
            Created tag information

        Raises:
            DifyValidationError: If name is invalid or too long
            DifyAPIError: For other API errors
        """
        request = CreateKnowledgeTagRequest(name=name)
        response = self._client.post("/v1/datasets/tags", json=request.model_dump())
        return KnowledgeTag(**response)

    def list(self) -> List[KnowledgeTag]:
        """Get list of knowledge type tags.

        Returns:
            List of knowledge tags

        Raises:
            DifyAPIError: For API errors
        """
        response = self._client.get("/v1/datasets/tags")
        # Handle both list and dict response formats
        if isinstance(response, list):
            return [KnowledgeTag(**tag) for tag in response]
        else:
            return [KnowledgeTag(**tag) for tag in response.get("data", [])]

    def update(self, tag_id: str, name: str) -> KnowledgeTag:
        """Update knowledge type tag name.

        Args:
            tag_id: Tag ID
            name: New tag name (max 50 characters)

        Returns:
            Updated tag information

        Raises:
            DifyNotFoundError: If tag not found
            DifyValidationError: If name is invalid
            DifyAPIError: For other API errors
        """
        request = UpdateKnowledgeTagRequest(name=name, tag_id=tag_id)
        response = self._client.patch("/v1/datasets/tags", json=request.model_dump())
        return KnowledgeTag(**response)

    def delete(self, tag_id: str) -> Dict[str, Any]:
        """Delete a knowledge type tag.

        Args:
            tag_id: Tag ID

        Returns:
            Success response

        Raises:
            DifyNotFoundError: If tag not found
            DifyAPIError: For other API errors
        """
        request = DeleteKnowledgeTagRequest(tag_id=tag_id)
        return self._client.delete("/v1/datasets/tags", json=request.model_dump())

    def bind_to_dataset(
        self,
        dataset_id: str,
        tag_ids: List[str],
    ) -> Dict[str, Any]:
        """Bind dataset to knowledge type tags.

        Args:
            dataset_id: Dataset ID
            tag_ids: List of tag IDs

        Returns:
            Success response

        Raises:
            DifyNotFoundError: If dataset or tags not found
            DifyValidationError: If tag IDs are invalid
            DifyAPIError: For other API errors
        """
        request = BindDatasetToTagRequest(tag_ids=tag_ids, target_id=dataset_id)
        return self._client.post("/v1/datasets/tags/binding", json=request.model_dump())

    def unbind_from_dataset(
        self,
        dataset_id: str,
        tag_id: str,
    ) -> Dict[str, Any]:
        """Unbind dataset from knowledge type tag.

        Args:
            dataset_id: Dataset ID
            tag_id: Tag ID

        Returns:
            Success response

        Raises:
            DifyNotFoundError: If dataset or tag not found
            DifyAPIError: For other API errors
        """
        request = UnbindDatasetFromTagRequest(tag_id=tag_id, target_id=dataset_id)
        return self._client.post("/v1/datasets/tags/unbinding", json=request.model_dump())

    def get_dataset_tags(
        self,
        dataset_id: str,
        return_detail: bool = False,
    ) -> Union[List[KnowledgeTag], DatasetTagsResponse]:
        """Get tags bound to a dataset.

        Args:
            dataset_id: Dataset ID
            return_detail: Whether to return full response with total count

        Returns:
            List of bound tags, or full response when return_detail is True

        Raises:
            DifyNotFoundError: If dataset not found
            DifyAPIError: For other API errors
        """
        response = self._client.post(f"/v1/datasets/{dataset_id}/tags", json={})
        # Handle both list and dict response formats
        if return_detail:
            if isinstance(response, list):
                tags = [KnowledgeTag(**tag) for tag in response]
                return DatasetTagsResponse(data=tags, total=len(tags))
            return DatasetTagsResponse(**response)

        if isinstance(response, list):
            return [KnowledgeTag(**tag) for tag in response]
        return [KnowledgeTag(**tag) for tag in response.get("data", [])]

