"""Documents client for Dify API."""

from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union

from .._base import BaseClient
from ..datasets.models import PaginatedResponse, RetrievalModel
from .models import (
    BatchDocumentStatusRequest,
    CreateDocumentByFileData,
    CreateDocumentByTextRequest,
    Document,
    DocumentResponse,
    IndexingStatusResponse,
    ProcessRule,
    UpdateDocumentByFileData,
    UpdateDocumentByTextRequest,
)


class DocumentsClient:
    """Client for document management operations.

    Provides methods for creating, listing, updating, and deleting documents,
    as well as monitoring indexing status.
    """

    def __init__(self, base_client: BaseClient) -> None:
        """Initialize the documents client.

        Args:
            base_client: Base HTTP client for making API requests
        """
        self._client = base_client

    def create_by_text(
        self,
        dataset_id: str,
        name: str,
        text: str,
        indexing_technique: Optional[Literal["high_quality", "economy"]] = "high_quality",
        doc_form: Optional[Literal["text_model", "hierarchical_model", "qa_model"]] = None,
        doc_language: Optional[str] = None,
        process_rule: Optional[ProcessRule] = None,
        retrieval_model: Optional[RetrievalModel] = None,
        embedding_model: Optional[str] = None,
        embedding_model_provider: Optional[str] = None,
    ) -> DocumentResponse:
        """Create a document from text content.

        Args:
            dataset_id: Dataset ID
            name: Document name
            text: Document text content
            indexing_technique: Indexing technique (default: 'high_quality')
            doc_form: Document form (optional)
            doc_language: Document language for Q&A mode (optional)
            process_rule: Processing rules (optional)
            retrieval_model: Retrieval model config (optional)
            embedding_model: Embedding model name (optional)
            embedding_model_provider: Embedding model provider (optional)

        Returns:
            Created document information with batch ID

        Raises:
            DifyValidationError: If parameters are invalid
            DifyAPIError: For other API errors
        """
        request = CreateDocumentByTextRequest(
            name=name,
            text=text,
            indexing_technique=indexing_technique,
            doc_form=doc_form,
            doc_language=doc_language,
            process_rule=process_rule,
            retrieval_model=retrieval_model,
            embedding_model=embedding_model,
            embedding_model_provider=embedding_model_provider,
        )
        response = self._client.post(
            f"/v1/datasets/{dataset_id}/document/create-by-text",
            json=request.model_dump(exclude_none=True),
        )
        return DocumentResponse(**response)

    def create_by_file(
        self,
        dataset_id: str,
        file_path: Union[str, Path],
        original_document_id: Optional[str] = None,
        indexing_technique: Optional[Literal["high_quality", "economy"]] = "high_quality",
        doc_form: Optional[Literal["text_model", "hierarchical_model", "qa_model"]] = None,
        doc_language: Optional[str] = None,
        process_rule: Optional[ProcessRule] = None,
        retrieval_model: Optional[RetrievalModel] = None,
        embedding_model: Optional[str] = None,
        embedding_model_provider: Optional[str] = None,
    ) -> DocumentResponse:
        """Create a document from file upload.

        Args:
            dataset_id: Dataset ID
            file_path: Path to the file to upload
            original_document_id: Original document ID for update (optional)
            indexing_technique: Indexing technique (default: 'high_quality')
            doc_form: Document form (optional)
            doc_language: Document language for Q&A mode (optional)
            process_rule: Processing rules (optional)
            retrieval_model: Retrieval model config (optional)
            embedding_model: Embedding model name (optional)
            embedding_model_provider: Embedding model provider (optional)

        Returns:
            Created document information with batch ID

        Raises:
            FileNotFoundError: If file doesn't exist
            DifyValidationError: If file type not supported or too large
            DifyAPIError: For other API errors
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        data_payload = CreateDocumentByFileData(
            original_document_id=original_document_id,
            indexing_technique=indexing_technique,
            doc_form=doc_form,
            doc_language=doc_language,
            process_rule=process_rule,
            retrieval_model=retrieval_model,
            embedding_model=embedding_model,
            embedding_model_provider=embedding_model_provider,
        )

        json_data = data_payload.model_dump_json(exclude_none=True)

        with open(file_path, "rb") as file_handle:
            files = {
                "file": (file_path.name, file_handle, "application/octet-stream"),
                "data": ("", json_data, "application/json"),
            }
            response = self._client.post(f"/v1/datasets/{dataset_id}/document/create-by-file", files=files)

        return DocumentResponse(**response)

    def list(
        self,
        dataset_id: str,
        keyword: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> PaginatedResponse:
        """Get list of documents in a dataset.

        Args:
            dataset_id: Dataset ID
            keyword: Search keyword for document names (optional)
            page: Page number (default: 1)
            limit: Items per page, range 1-100 (default: 20)

        Returns:
            Paginated list of documents

        Raises:
            DifyNotFoundError: If dataset not found
            DifyAPIError: For other API errors
        """
        params: Dict[str, Any] = {"page": page, "limit": limit}
        if keyword:
            params["keyword"] = keyword

        response = self._client.get(f"/v1/datasets/{dataset_id}/documents", params=params)
        return PaginatedResponse(**response)

    def get(
        self,
        dataset_id: str,
        document_id: str,
        metadata: Literal["all", "only", "without"] = "all",
    ) -> Document:
        """Get document details.

        Args:
            dataset_id: Dataset ID
            document_id: Document ID
            metadata: Metadata filter condition (default: 'all')

        Returns:
            Document information

        Raises:
            DifyNotFoundError: If dataset or document not found
            DifyAPIError: For other API errors
        """
        params = {"metadata": metadata}
        response = self._client.get(f"/v1/datasets/{dataset_id}/documents/{document_id}", params=params)
        return Document(**response)

    def update_by_text(
        self,
        dataset_id: str,
        document_id: str,
        name: Optional[str] = None,
        text: Optional[str] = None,
        process_rule: Optional[ProcessRule] = None,
    ) -> DocumentResponse:
        """Update a document with text content.

        Args:
            dataset_id: Dataset ID
            document_id: Document ID
            name: Updated document name (optional)
            text: Updated document text content (optional)
            process_rule: Processing rules (optional)

        Returns:
            Updated document information

        Raises:
            DifyNotFoundError: If dataset or document not found
            DifyAPIError: For other API errors
        """
        request = UpdateDocumentByTextRequest(
            name=name,
            text=text,
            process_rule=process_rule,
        )
        response = self._client.post(
            f"/v1/datasets/{dataset_id}/documents/{document_id}/update-by-text",
            json=request.model_dump(exclude_none=True),
        )
        return DocumentResponse(**response)

    def update_by_file(
        self,
        dataset_id: str,
        document_id: str,
        file_path: Union[str, Path],
        name: Optional[str] = None,
        process_rule: Optional[ProcessRule] = None,
    ) -> DocumentResponse:
        """Update a document with file content.

        Args:
            dataset_id: Dataset ID
            document_id: Document ID
            file_path: Path to the new file
            name: Updated document name (optional)
            process_rule: Processing rules (optional)

        Returns:
            Updated document information

        Raises:
            FileNotFoundError: If file doesn't exist
            DifyNotFoundError: If dataset or document not found
            DifyValidationError: If file type not supported or too large
            DifyAPIError: For other API errors
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        data_payload = UpdateDocumentByFileData(
            name=name,
            process_rule=process_rule,
        )

        json_data = data_payload.model_dump_json(exclude_none=True)

        with open(file_path, "rb") as file_handle:
            files = {
                "file": (file_path.name, file_handle, "application/octet-stream"),
                "data": ("", json_data, "application/json"),
            }
            response = self._client.post(
                f"/v1/datasets/{dataset_id}/documents/{document_id}/update-by-file",
                files=files,
            )

        return DocumentResponse(**response)

    def delete(self, dataset_id: str, document_id: str) -> Dict[str, Any]:
        """Delete a document.

        Args:
            dataset_id: Dataset ID
            document_id: Document ID

        Returns:
            Success response

        Raises:
            DifyNotFoundError: If dataset or document not found
            DifyAPIError: For other API errors
        """
        return self._client.delete(f"/v1/datasets/{dataset_id}/documents/{document_id}")

    def get_indexing_status(self, dataset_id: str, batch: str) -> IndexingStatusResponse:
        """Get document indexing status (progress).

        Args:
            dataset_id: Dataset ID
            batch: Upload batch number from document creation

        Returns:
            Indexing status information

        Raises:
            DifyNotFoundError: If dataset or batch not found
            DifyAPIError: For other API errors
        """
        response = self._client.get(f"/v1/datasets/{dataset_id}/documents/{batch}/indexing-status")
        return IndexingStatusResponse(**response)

    def batch_update_status(
        self,
        dataset_id: str,
        action: Literal["enable", "disable", "archive", "un_archive"],
        document_ids: List[str],
    ) -> Dict[str, Any]:
        """Update status of multiple documents.

        Args:
            dataset_id: Dataset ID
            action: Action to perform - 'enable', 'disable', 'archive', 'un_archive'
            document_ids: List of document IDs

        Returns:
            Success response

        Raises:
            DifyValidationError: If action is invalid
            DifyNotFoundError: If dataset not found
            DifyAPIError: For other API errors
        """
        request = BatchDocumentStatusRequest(document_ids=document_ids)
        response = self._client.patch(
            f"/v1/datasets/{dataset_id}/documents/status/{action}",
            json=request.model_dump(),
        )
        return response

    def get_upload_file(
        self,
        dataset_id: str,
        document_id: str,
    ) -> Dict[str, Any]:
        """Get uploaded file information.

        Args:
            dataset_id: Dataset ID
            document_id: Document ID

        Returns:
            File information

        Raises:
            DifyNotFoundError: If dataset or document not found
            DifyAPIError: For other API errors
        """
        return self._client.get(f"/v1/datasets/{dataset_id}/documents/{document_id}/upload-file")
