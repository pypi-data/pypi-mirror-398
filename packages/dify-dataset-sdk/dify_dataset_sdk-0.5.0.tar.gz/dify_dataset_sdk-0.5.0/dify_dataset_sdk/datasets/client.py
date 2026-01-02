"""Datasets client for Dify API."""

from typing import Any, Dict, List, Literal, Optional

from .._base import BaseClient
from .models import (
    CreateDatasetRequest,
    Dataset,
    PaginatedResponse,
    RetrievalModel,
    RetrievalRequest,
    RetrievalResponse,
    UpdateDatasetRequest,
)


class DatasetsClient:
    """Client for dataset management operations.

    Provides methods for creating, listing, updating, and deleting datasets,
    as well as knowledge base retrieval.
    """

    def __init__(self, base_client: BaseClient) -> None:
        """Initialize the datasets client.

        Args:
            base_client: Base HTTP client for making API requests
        """
        self._client = base_client

    def create(
        self,
        name: str,
        description: Optional[str] = None,
        indexing_technique: Optional[Literal["high_quality", "economy"]] = None,
        permission: Optional[Literal["only_me", "all_team_members", "partial_members"]] = "only_me",
        provider: Optional[Literal["vendor", "external"]] = "vendor",
        external_knowledge_api_id: Optional[str] = None,
        external_knowledge_id: Optional[str] = None,
        embedding_model: Optional[str] = None,
        embedding_model_provider: Optional[str] = None,
        retrieval_model: Optional[RetrievalModel] = None,
        partial_member_list: Optional[List[str]] = None,
    ) -> Dataset:
        """Create an empty dataset.

        Args:
            name: Dataset name (required)
            description: Dataset description (optional)
            indexing_technique: Indexing mode - 'high_quality' or 'economy' (optional)
            permission: Permission level (optional, default: 'only_me')
            provider: Provider type (optional, default: 'vendor')
            external_knowledge_api_id: External knowledge API ID (optional)
            external_knowledge_id: External knowledge ID (optional)
            embedding_model: Embedding model name (optional)
            embedding_model_provider: Embedding model provider (optional)
            retrieval_model: Retrieval model configuration (optional)
            partial_member_list: Partial member list (optional)

        Returns:
            Created dataset information

        Raises:
            DifyAPIError: For API errors
        """
        request = CreateDatasetRequest(
            name=name,
            description=description,
            indexing_technique=indexing_technique,
            permission=permission,
            provider=provider,
            external_knowledge_api_id=external_knowledge_api_id,
            external_knowledge_id=external_knowledge_id,
            embedding_model=embedding_model,
            embedding_model_provider=embedding_model_provider,
            retrieval_model=retrieval_model,
            partial_member_list=partial_member_list,
        )
        response = self._client.post("/v1/datasets", json=request.model_dump(exclude_none=True))
        return Dataset(**response)

    def list(
        self,
        keyword: Optional[str] = None,
        tag_ids: Optional[List[str]] = None,
        page: int = 1,
        limit: int = 20,
        include_all: bool = False,
    ) -> PaginatedResponse:
        """Get paginated list of datasets.

        Args:
            keyword: Search keyword (optional)
            tag_ids: Tag ID list (optional)
            page: Page number, starting from 1 (default: 1)
            limit: Items per page, max 100 (default: 20)
            include_all: Include all datasets (only for owners) (default: False)

        Returns:
            Paginated response containing dataset list

        Raises:
            DifyAPIError: For API errors
        """
        params: Dict[str, Any] = {
            "page": page,
            "limit": limit,
            "include_all": include_all,
        }
        if keyword:
            params["keyword"] = keyword
        if tag_ids:
            params["tag_ids"] = tag_ids

        response = self._client.get("/v1/datasets", params=params)
        return PaginatedResponse(**response)

    def get(self, dataset_id: str) -> Dataset:
        """Get dataset details.

        Args:
            dataset_id: Dataset ID

        Returns:
            Dataset information

        Raises:
            DifyNotFoundError: If dataset not found
            DifyAPIError: For other API errors
        """
        response = self._client.get(f"/v1/datasets/{dataset_id}")
        return Dataset(**response)

    def update(
        self,
        dataset_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        indexing_technique: Optional[Literal["high_quality", "economy"]] = None,
        permission: Optional[Literal["only_me", "all_team_members", "partial_members"]] = None,
        embedding_model_provider: Optional[str] = None,
        embedding_model: Optional[str] = None,
        retrieval_model: Optional[RetrievalModel] = None,
        partial_member_list: Optional[List[str]] = None,
    ) -> Dataset:
        """Update dataset details.

        Args:
            dataset_id: Dataset ID
            name: Dataset name (optional)
            description: Dataset description (optional)
            indexing_technique: Indexing mode (optional)
            permission: Permission level (optional)
            embedding_model_provider: Embedding model provider (optional)
            embedding_model: Embedding model (optional)
            retrieval_model: Retrieval parameters (optional)
            partial_member_list: Partial member list (optional)

        Returns:
            Updated dataset information

        Raises:
            DifyNotFoundError: If dataset not found
            DifyAPIError: For other API errors
        """
        request = UpdateDatasetRequest(
            name=name,
            description=description,
            indexing_technique=indexing_technique,
            permission=permission,
            embedding_model_provider=embedding_model_provider,
            embedding_model=embedding_model,
            retrieval_model=retrieval_model,
            partial_member_list=partial_member_list,
        )
        response = self._client.patch(f"/v1/datasets/{dataset_id}", json=request.model_dump(exclude_none=True))
        return Dataset(**response)

    def delete(self, dataset_id: str) -> Dict[str, Any]:
        """Delete a dataset.

        Args:
            dataset_id: Dataset ID

        Returns:
            Success response

        Raises:
            DifyNotFoundError: If dataset not found
            DifyAPIError: For other API errors
        """
        return self._client.delete(f"/v1/datasets/{dataset_id}")

    def retrieve(
        self,
        dataset_id: str,
        query: str,
        retrieval_model: Optional[RetrievalModel] = None,
        external_retrieval_model: Optional[Dict[str, Any]] = None,
    ) -> RetrievalResponse:
        """Retrieve knowledge base content.

        Args:
            dataset_id: Dataset ID
            query: Search query
            retrieval_model: Retrieval parameters (optional)
            external_retrieval_model: External retrieval model (optional)

        Returns:
            Retrieval results

        Raises:
            DifyNotFoundError: If dataset not found
            DifyValidationError: If query is invalid
            DifyAPIError: For other API errors
        """
        request = RetrievalRequest(
            query=query,
            retrieval_model=retrieval_model,
            external_retrieval_model=external_retrieval_model,
        )
        response = self._client.post(
            f"/v1/datasets/{dataset_id}/retrieve",
            json=request.model_dump(exclude_none=True),
        )
        return RetrievalResponse(**response)
