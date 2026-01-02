"""Metadata client for Dify API."""

from typing import Any, Dict, List, Literal, Union

from .._base import BaseClient
from .models import (
    CreateMetadataRequest,
    DocumentMetadata,
    Metadata,
    MetadataListResponse,
    UpdateDocumentMetadataRequest,
    UpdateMetadataRequest,
)


class MetadataClient:
    """Client for metadata management operations."""

    def __init__(self, base_client: BaseClient) -> None:
        """Initialize the metadata client.

        Args:
            base_client: Base HTTP client for making API requests
        """
        self._client = base_client

    def create(
        self,
        dataset_id: str,
        field_type: str,
        name: str,
    ) -> Metadata:
        """Create a metadata field for a dataset.

        Args:
            dataset_id: Dataset ID
            field_type: Metadata type (string, number, time)
            name: Field name

        Returns:
            Created metadata field information

        Raises:
            DifyNotFoundError: If dataset not found
            DifyValidationError: If field data is invalid
            DifyAPIError: For other API errors
        """
        request = CreateMetadataRequest(type=field_type, name=name)
        response = self._client.post(
            f"/v1/datasets/{dataset_id}/metadata",
            json=request.model_dump(),
        )
        return Metadata(**response)

    def update(
        self,
        dataset_id: str,
        metadata_id: str,
        name: str,
    ) -> Metadata:
        """Update a metadata field.

        Args:
            dataset_id: Dataset ID
            metadata_id: Metadata field ID
            name: Updated field name

        Returns:
            Updated metadata field information

        Raises:
            DifyNotFoundError: If dataset or metadata field not found
            DifyValidationError: If field data is invalid
            DifyAPIError: For other API errors
        """
        request = UpdateMetadataRequest(name=name)
        response = self._client.patch(
            f"/v1/datasets/{dataset_id}/metadata/{metadata_id}",
            json=request.model_dump(),
        )
        return Metadata(**response)

    def delete(
        self,
        dataset_id: str,
        metadata_id: str,
    ) -> Dict[str, Any]:
        """Delete a metadata field.

        Args:
            dataset_id: Dataset ID
            metadata_id: Metadata field ID

        Returns:
            Success response

        Raises:
            DifyNotFoundError: If dataset or metadata field not found
            DifyAPIError: For other API errors
        """
        return self._client.delete(f"/v1/datasets/{dataset_id}/metadata/{metadata_id}")

    def toggle_built_in(
        self,
        dataset_id: str,
        action: Literal["disable", "enable"],
    ) -> Dict[str, Any]:
        """Enable or disable built-in metadata fields.

        Args:
            dataset_id: Dataset ID
            action: Action to perform - 'disable' or 'enable'

        Returns:
            Success response

        Raises:
            DifyNotFoundError: If dataset not found
            DifyValidationError: If action is invalid
            DifyAPIError: For other API errors
        """
        return self._client.post(f"/v1/datasets/{dataset_id}/metadata/built-in/{action}")

    def update_document_metadata(
        self,
        dataset_id: str,
        operation_data: Union[List[DocumentMetadata], List[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        """Update document metadata values.

        Args:
            dataset_id: Dataset ID
            operation_data: List of document metadata operations, each containing:
                - document_id (str): Document ID
                - metadata_list (list): Metadata list with id, value, name

        Returns:
            Success response

        Raises:
            DifyNotFoundError: If dataset not found
            DifyValidationError: If metadata is invalid
            DifyAPIError: For other API errors
        """
        converted_data: List[DocumentMetadata] = []
        for item in operation_data:
            if isinstance(item, dict):
                converted_data.append(DocumentMetadata(**item))
            else:
                converted_data.append(item)
        request = UpdateDocumentMetadataRequest(operation_data=converted_data)
        result: Dict[str, Any] = self._client.post(
            f"/v1/datasets/{dataset_id}/documents/metadata",
            json=request.model_dump(),
        )
        return result

    def list(self, dataset_id: str) -> MetadataListResponse:
        """Get list of metadata fields for a dataset.

        Args:
            dataset_id: Dataset ID

        Returns:
            List of metadata fields

        Raises:
            DifyNotFoundError: If dataset not found
            DifyAPIError: For other API errors
        """
        response = self._client.get(f"/v1/datasets/{dataset_id}/metadata")
        return MetadataListResponse(**response)
