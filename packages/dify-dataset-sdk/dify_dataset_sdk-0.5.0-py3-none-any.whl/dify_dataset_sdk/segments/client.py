"""Segments client for Dify API."""

from typing import Any, Dict, List, Optional

from .._base import BaseClient
from .models import (
    ChildChunkResponse,
    CreateChildChunkRequest,
    CreateSegmentRequest,
    SegmentResponse,
    UpdateChildChunkRequest,
    UpdateSegmentRequest,
)


class SegmentsClient:
    """Client for segment and child chunk management operations.

    Provides methods for creating, listing, updating, and deleting segments
    and their child chunks.
    """

    def __init__(self, base_client: BaseClient) -> None:
        """Initialize the segments client.

        Args:
            base_client: Base HTTP client for making API requests
        """
        self._client = base_client

    # ===== Segment Operations =====
    def create(
        self,
        dataset_id: str,
        document_id: str,
        segments: List[Dict[str, Any]],
    ) -> SegmentResponse:
        """Create new segments for a document.

        Args:
            dataset_id: Dataset ID
            document_id: Document ID
            segments: List of segment data, each containing:
                - content (str): Text content/question content (required)
                - answer (str): Answer content (optional, for Q&A mode)
                - keywords (list): Keywords (optional)

        Returns:
            Created segments information

        Raises:
            DifyNotFoundError: If dataset or document not found
            DifyValidationError: If segment data is invalid
            DifyAPIError: For other API errors
        """
        request = CreateSegmentRequest(segments=segments)
        response = self._client.post(
            f"/v1/datasets/{dataset_id}/documents/{document_id}/segments",
            json=request.model_dump(),
        )
        return SegmentResponse(**response)

    def list(
        self,
        dataset_id: str,
        document_id: str,
        keyword: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> SegmentResponse:
        """Get list of segments in a document.

        Args:
            dataset_id: Dataset ID
            document_id: Document ID
            keyword: Search keyword (optional)
            status: Search status, e.g., 'completed' (optional)
            page: Page number (default: 1)
            limit: Items per page, range 1-100 (default: 20)

        Returns:
            List of segments

        Raises:
            DifyNotFoundError: If dataset or document not found
            DifyAPIError: For other API errors
        """
        params: Dict[str, Any] = {"page": page, "limit": limit}
        if keyword:
            params["keyword"] = keyword
        if status:
            params["status"] = status

        response = self._client.get(
            f"/v1/datasets/{dataset_id}/documents/{document_id}/segments",
            params=params,
        )
        return SegmentResponse(**response)

    def get(
        self,
        dataset_id: str,
        document_id: str,
        segment_id: str,
    ) -> Dict[str, Any]:
        """Get document segment details.

        Args:
            dataset_id: Dataset ID
            document_id: Document ID
            segment_id: Segment ID

        Returns:
            Segment details

        Raises:
            DifyNotFoundError: If dataset, document, or segment not found
            DifyAPIError: For other API errors
        """
        return self._client.get(f"/v1/datasets/{dataset_id}/documents/{document_id}/segments/{segment_id}")

    def update(
        self,
        dataset_id: str,
        document_id: str,
        segment_id: str,
        segment_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update a document segment.

        Args:
            dataset_id: Dataset ID
            document_id: Document ID
            segment_id: Segment ID
            segment_data: Updated segment data containing:
                - content (str): Text content/question content (required)
                - answer (str): Answer content (optional, for Q&A mode)
                - keywords (list): Keywords (optional)
                - enabled (bool): Whether segment is enabled (optional)
                - regenerate_child_chunks (bool): Whether to regenerate child segments (optional)

        Returns:
            Updated segment information

        Raises:
            DifyNotFoundError: If dataset, document, or segment not found
            DifyValidationError: If segment data is invalid
            DifyAPIError: For other API errors
        """
        request = UpdateSegmentRequest(segment=segment_data)
        response = self._client.post(
            f"/v1/datasets/{dataset_id}/documents/{document_id}/segments/{segment_id}",
            json=request.model_dump(),
        )
        return response

    def delete(
        self,
        dataset_id: str,
        document_id: str,
        segment_id: str,
    ) -> Dict[str, Any]:
        """Delete a document segment.

        Args:
            dataset_id: Dataset ID
            document_id: Document ID
            segment_id: Segment ID

        Returns:
            Success response

        Raises:
            DifyNotFoundError: If dataset, document, or segment not found
            DifyAPIError: For other API errors
        """
        return self._client.delete(f"/v1/datasets/{dataset_id}/documents/{document_id}/segments/{segment_id}")

    # ===== Child Chunk Operations =====
    def create_child_chunk(
        self,
        dataset_id: str,
        document_id: str,
        segment_id: str,
        content: str,
    ) -> Dict[str, Any]:
        """Create a new child chunk for a document segment.

        Args:
            dataset_id: Dataset ID
            document_id: Document ID
            segment_id: Parent segment ID
            content: Child chunk content

        Returns:
            Created child chunk information

        Raises:
            DifyNotFoundError: If dataset, document, or segment not found
            DifyValidationError: If content is invalid
            DifyAPIError: For other API errors
        """
        request = CreateChildChunkRequest(content=content)
        return self._client.post(
            f"/v1/datasets/{dataset_id}/documents/{document_id}/segments/{segment_id}/child_chunks",
            json=request.model_dump(),
        )

    def list_child_chunks(
        self,
        dataset_id: str,
        document_id: str,
        segment_id: str,
        keyword: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> ChildChunkResponse:
        """Get list of child chunks for a document segment.

        Args:
            dataset_id: Dataset ID
            document_id: Document ID
            segment_id: Parent segment ID
            keyword: Search keyword (optional)
            page: Page number (default: 1)
            limit: Items per page, max 100 (default: 20)

        Returns:
            List of child chunks

        Raises:
            DifyNotFoundError: If dataset, document, or segment not found
            DifyAPIError: For other API errors
        """
        params: Dict[str, Any] = {"page": page, "limit": limit}
        if keyword:
            params["keyword"] = keyword

        response = self._client.get(
            f"/v1/datasets/{dataset_id}/documents/{document_id}/segments/{segment_id}/child_chunks",
            params=params,
        )
        return ChildChunkResponse(**response)

    def update_child_chunk(
        self,
        dataset_id: str,
        document_id: str,
        segment_id: str,
        child_chunk_id: str,
        content: str,
    ) -> Dict[str, Any]:
        """Update a document child chunk.

        Args:
            dataset_id: Dataset ID
            document_id: Document ID
            segment_id: Parent segment ID
            child_chunk_id: Child chunk ID
            content: Updated child chunk content

        Returns:
            Updated child chunk information

        Raises:
            DifyNotFoundError: If dataset, document, segment, or child chunk not found
            DifyValidationError: If content is invalid
            DifyAPIError: For other API errors
        """
        request = UpdateChildChunkRequest(content=content)
        return self._client.patch(
            f"/v1/datasets/{dataset_id}/documents/{document_id}/segments/{segment_id}/child_chunks/{child_chunk_id}",
            json=request.model_dump(),
        )

    def delete_child_chunk(
        self,
        dataset_id: str,
        document_id: str,
        segment_id: str,
        child_chunk_id: str,
    ) -> Dict[str, Any]:
        """Delete a document child chunk.

        Args:
            dataset_id: Dataset ID
            document_id: Document ID
            segment_id: Parent segment ID
            child_chunk_id: Child chunk ID

        Returns:
            Success response

        Raises:
            DifyNotFoundError: If dataset, document, segment, or child chunk not found
            DifyAPIError: For other API errors
        """
        return self._client.delete(f"/v1/datasets/{dataset_id}/documents/{document_id}/segments/{segment_id}/child_chunks/{child_chunk_id}")
