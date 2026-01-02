"""Tests for DocumentsClient - Document management operations."""

import pytest
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dify_dataset_sdk import DifyDatasetClient

from dify_dataset_sdk.documents.models import (
    Document,
    DocumentResponse,
    IndexingStatusResponse,
    ProcessRule,
    ProcessRuleConfig,
    PreProcessingRule,
    Segmentation,
)
from dify_dataset_sdk.datasets.models import PaginatedResponse


class TestDocumentsCreateByText:
    """Tests for documents.create_by_text() method."""

    def test_create_by_text_minimal(self, client: "DifyDatasetClient", test_dataset: dict):
        """Test creating document with minimal required parameters."""
        response = client.documents.create_by_text(
            dataset_id=test_dataset["id"],
            name="MinimalDoc",
            text="This is minimal document content.",
        )

        assert isinstance(response, DocumentResponse)
        assert response.document.id is not None
        assert response.document.name == "MinimalDoc"
        assert response.batch is not None

    def test_create_by_text_with_high_quality_indexing(self, client: "DifyDatasetClient", test_dataset: dict):
        """Test creating document with high_quality indexing technique."""
        response = client.documents.create_by_text(
            dataset_id=test_dataset["id"],
            name="HighQualityDoc",
            text="High quality indexed document content.",
            indexing_technique="high_quality",
        )

        assert isinstance(response, DocumentResponse)
        assert response.document.id is not None

    def test_create_by_text_with_economy_indexing(self, client: "DifyDatasetClient", test_dataset: dict):
        """Test creating document with economy indexing technique."""
        response = client.documents.create_by_text(
            dataset_id=test_dataset["id"],
            name="EconomyDoc",
            text="Economy indexed document content.",
            indexing_technique="economy",
        )

        assert isinstance(response, DocumentResponse)
        assert response.document.id is not None

    def test_create_by_text_with_text_model_form(self, client: "DifyDatasetClient", test_dataset: dict):
        """Test creating document with text_model doc form."""
        response = client.documents.create_by_text(
            dataset_id=test_dataset["id"],
            name="TextModelDoc",
            text="Document using text model form.",
            doc_form="text_model",
        )

        assert isinstance(response, DocumentResponse)
        assert response.document.doc_form == "text_model"

    def test_create_by_text_with_qa_model_form(self, client: "DifyDatasetClient", test_dataset: dict):
        """Test creating document with qa_model doc form."""
        response = client.documents.create_by_text(
            dataset_id=test_dataset["id"],
            name="QAModelDoc",
            text="Question and answer document content.",
            doc_form="qa_model",
            doc_language="English",
        )

        assert isinstance(response, DocumentResponse)
        assert response.document.doc_form == "qa_model"

    def test_create_by_text_with_automatic_process_rule(self, client: "DifyDatasetClient", test_dataset: dict):
        """Test creating document with automatic processing rules."""
        process_rule = ProcessRule(mode="automatic")

        response = client.documents.create_by_text(
            dataset_id=test_dataset["id"],
            name="AutoProcessDoc",
            text="Document with automatic processing.",
            process_rule=process_rule,
        )

        assert isinstance(response, DocumentResponse)
        assert response.document.id is not None

    def test_create_by_text_with_custom_process_rule(self, client: "DifyDatasetClient", test_dataset: dict):
        """Test creating document with custom processing rules."""
        process_rule = ProcessRule(
            mode="custom",
            rules=ProcessRuleConfig(
                pre_processing_rules=[
                    PreProcessingRule(id="remove_extra_spaces", enabled=True),
                    PreProcessingRule(id="remove_urls_emails", enabled=False),
                ],
                segmentation=Segmentation(separator="\n", max_tokens=500),
            ),
        )

        response = client.documents.create_by_text(
            dataset_id=test_dataset["id"],
            name="CustomProcessDoc",
            text="Document with custom processing rules.\nSecond paragraph here.",
            process_rule=process_rule,
        )

        assert isinstance(response, DocumentResponse)
        assert response.document.id is not None

    def test_create_by_text_with_long_content(self, client: "DifyDatasetClient", test_dataset: dict):
        """Test creating document with long text content."""
        long_text = "This is a test paragraph. " * 100

        response = client.documents.create_by_text(
            dataset_id=test_dataset["id"],
            name="LongContentDoc",
            text=long_text,
        )

        assert isinstance(response, DocumentResponse)
        assert response.document.id is not None


class TestDocumentsCreateByFile:
    """Tests for documents.create_by_file() method."""

    def test_create_by_file_txt(self, client: "DifyDatasetClient", test_dataset: dict, test_file: Path):
        """Test creating document by uploading a text file."""
        response = client.documents.create_by_file(
            dataset_id=test_dataset["id"],
            file_path=test_file,
            process_rule=ProcessRule(mode="automatic"),
        )

        assert isinstance(response, DocumentResponse)
        assert response.document.id is not None
        assert response.batch is not None

    def test_create_by_file_with_indexing_technique(self, client: "DifyDatasetClient", test_dataset: dict, test_file: Path):
        """Test creating document by file with indexing technique."""
        response = client.documents.create_by_file(
            dataset_id=test_dataset["id"],
            file_path=test_file,
            indexing_technique="high_quality",
            process_rule=ProcessRule(mode="automatic"),
        )

        assert isinstance(response, DocumentResponse)
        assert response.document.id is not None

    def test_create_by_file_with_doc_form(self, client: "DifyDatasetClient", test_dataset: dict, test_file: Path):
        """Test creating document by file with doc form."""
        response = client.documents.create_by_file(
            dataset_id=test_dataset["id"],
            file_path=test_file,
            doc_form="text_model",
            process_rule=ProcessRule(mode="automatic"),
        )

        assert isinstance(response, DocumentResponse)
        assert response.document.doc_form == "text_model"

    def test_create_by_file_with_process_rule(self, client: "DifyDatasetClient", test_dataset: dict, test_file: Path):
        """Test creating document by file with processing rules."""
        process_rule = ProcessRule(mode="automatic")

        response = client.documents.create_by_file(
            dataset_id=test_dataset["id"],
            file_path=test_file,
            process_rule=process_rule,
        )

        assert isinstance(response, DocumentResponse)
        assert response.document.id is not None

    def test_create_by_file_nonexistent_file(self, client: "DifyDatasetClient", test_dataset: dict):
        """Test creating document with non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            client.documents.create_by_file(
                dataset_id=test_dataset["id"],
                file_path="/nonexistent/path/file.txt",
            )

    def test_create_by_file_string_path(self, client: "DifyDatasetClient", test_dataset: dict, test_file: Path):
        """Test creating document by file using string path."""
        response = client.documents.create_by_file(
            dataset_id=test_dataset["id"],
            file_path=str(test_file),
            process_rule=ProcessRule(mode="automatic"),
        )

        assert isinstance(response, DocumentResponse)
        assert response.document.id is not None


class TestDocumentsList:
    """Tests for documents.list() method."""

    def test_list_default_params(self, client: "DifyDatasetClient", test_document: dict):
        """Test listing documents with default parameters."""
        result = client.documents.list(dataset_id=test_document["dataset_id"])

        assert isinstance(result, PaginatedResponse)
        assert isinstance(result.data, list)
        assert result.page == 1
        assert result.limit == 20

    def test_list_with_page(self, client: "DifyDatasetClient", test_document: dict):
        """Test listing documents with specific page number."""
        result = client.documents.list(
            dataset_id=test_document["dataset_id"],
            page=1,
        )

        assert isinstance(result, PaginatedResponse)
        assert result.page == 1

    def test_list_with_limit(self, client: "DifyDatasetClient", test_document: dict):
        """Test listing documents with custom limit."""
        result = client.documents.list(
            dataset_id=test_document["dataset_id"],
            limit=5,
        )

        assert isinstance(result, PaginatedResponse)
        assert result.limit == 5
        assert len(result.data) <= 5

    def test_list_with_keyword(self, client: "DifyDatasetClient", test_document: dict):
        """Test listing documents with keyword filter."""
        result = client.documents.list(
            dataset_id=test_document["dataset_id"],
            keyword="Test",
        )

        assert isinstance(result, PaginatedResponse)

    def test_list_with_pagination(self, client: "DifyDatasetClient", test_document: dict):
        """Test listing documents with full pagination parameters."""
        result = client.documents.list(
            dataset_id=test_document["dataset_id"],
            page=1,
            limit=10,
        )

        assert isinstance(result, PaginatedResponse)
        assert result.page == 1
        assert result.limit == 10


class TestDocumentsGet:
    """Tests for documents.get() method."""

    def test_get_existing_document(self, client: "DifyDatasetClient", test_document: dict):
        """Test getting an existing document by ID."""
        document = client.documents.get(
            dataset_id=test_document["dataset_id"],
            document_id=test_document["id"],
        )

        assert isinstance(document, Document)
        assert document.id == test_document["id"]

    def test_get_document_with_metadata_all(self, client: "DifyDatasetClient", test_document: dict):
        """Test getting document with all metadata."""
        document = client.documents.get(
            dataset_id=test_document["dataset_id"],
            document_id=test_document["id"],
            metadata="all",
        )

        assert isinstance(document, Document)
        assert document.id == test_document["id"]

    @pytest.mark.skip(reason="metadata='only' returns incomplete document structure")
    def test_get_document_with_metadata_only(self, client: "DifyDatasetClient", test_document: dict):
        """Test getting document with only metadata."""
        # Note: metadata="only" returns partial document data
        # This test just verifies the API call works
        result = client.documents.get(
            dataset_id=test_document["dataset_id"],
            document_id=test_document["id"],
            metadata="only",
        )
        # Result may be partial, just check it's not None
        assert result is not None

    def test_get_document_with_metadata_without(self, client: "DifyDatasetClient", test_document: dict):
        """Test getting document without metadata."""
        document = client.documents.get(
            dataset_id=test_document["dataset_id"],
            document_id=test_document["id"],
            metadata="without",
        )

        assert isinstance(document, Document)

    def test_get_document_returns_all_fields(self, client: "DifyDatasetClient", test_document: dict):
        """Test that get returns all expected fields."""
        document = client.documents.get(
            dataset_id=test_document["dataset_id"],
            document_id=test_document["id"],
        )

        assert document.id is not None
        assert document.name is not None
        assert document.data_source_type is not None
        assert document.indexing_status is not None
        assert document.created_by is not None
        assert document.created_at is not None


class TestDocumentsUpdateByText:
    """Tests for documents.update_by_text() method."""

    def test_update_by_text_name_only(self, client: "DifyDatasetClient", test_document: dict):
        """Test updating document name only."""
        # Wait for document to be fully indexed and available
        time.sleep(3)
        new_name = f"UpdatedDoc_{int(time.time())}"

        response = client.documents.update_by_text(
            dataset_id=test_document["dataset_id"],
            document_id=test_document["id"],
            name=new_name,
            process_rule=ProcessRule(mode="automatic"),
        )

        assert isinstance(response, DocumentResponse)
        assert response.document.name == new_name

    def test_update_by_text_content_only(self, client: "DifyDatasetClient", test_document: dict):
        """Test updating document text content."""
        time.sleep(3)
        new_name = f"ContentUpdate_{int(time.time())}"
        new_text = "Updated document content for testing."

        response = client.documents.update_by_text(
            dataset_id=test_document["dataset_id"],
            document_id=test_document["id"],
            name=new_name,
            text=new_text,
        )

        assert isinstance(response, DocumentResponse)
        assert response.document.id == test_document["id"]

    def test_update_by_text_name_and_content(self, client: "DifyDatasetClient", test_document: dict):
        """Test updating both document name and content."""
        time.sleep(3)
        new_name = f"FullUpdate_{int(time.time())}"
        new_text = "Fully updated document content."

        response = client.documents.update_by_text(
            dataset_id=test_document["dataset_id"],
            document_id=test_document["id"],
            name=new_name,
            text=new_text,
        )

        assert isinstance(response, DocumentResponse)
        assert response.document.name == new_name

    def test_update_by_text_with_process_rule(self, client: "DifyDatasetClient", test_document: dict):
        """Test updating document with processing rules."""
        time.sleep(3)
        new_name = f"ProcessRuleUpdate_{int(time.time())}"
        process_rule = ProcessRule(mode="automatic")

        response = client.documents.update_by_text(
            dataset_id=test_document["dataset_id"],
            document_id=test_document["id"],
            name=new_name,
            text="Updated with process rules.",
            process_rule=process_rule,
        )

        assert isinstance(response, DocumentResponse)


class TestDocumentsUpdateByFile:
    """Tests for documents.update_by_file() method."""

    def test_update_by_file(self, client: "DifyDatasetClient", test_document: dict, test_file: Path):
        """Test updating document with a file."""
        time.sleep(3)
        response = client.documents.update_by_file(
            dataset_id=test_document["dataset_id"],
            document_id=test_document["id"],
            file_path=test_file,
        )

        assert isinstance(response, DocumentResponse)
        assert response.document.id == test_document["id"]

    def test_update_by_file_with_name(self, client: "DifyDatasetClient", test_document: dict, test_file: Path):
        """Test updating document with file and new name."""
        time.sleep(3)
        new_name = f"FileUpdated_{int(time.time())}"

        response = client.documents.update_by_file(
            dataset_id=test_document["dataset_id"],
            document_id=test_document["id"],
            file_path=test_file,
            name=new_name,
        )

        assert isinstance(response, DocumentResponse)
        assert response.document.name == new_name

    def test_update_by_file_nonexistent(self, client: "DifyDatasetClient", test_document: dict):
        """Test updating document with non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            client.documents.update_by_file(
                dataset_id=test_document["dataset_id"],
                document_id=test_document["id"],
                file_path="/nonexistent/path/file.txt",
            )


class TestDocumentsDelete:
    """Tests for documents.delete() method."""

    def test_delete_document(self, client: "DifyDatasetClient", test_dataset: dict):
        """Test deleting a document."""
        # Create a document to delete
        response = client.documents.create_by_text(
            dataset_id=test_dataset["id"],
            name="ToDeleteDoc",
            text="Document to be deleted.",
        )
        doc_id = response.document.id

        # Delete it
        result = client.documents.delete(
            dataset_id=test_dataset["id"],
            document_id=doc_id,
        )

        assert result is not None


class TestDocumentsIndexingStatus:
    """Tests for documents.get_indexing_status() method."""

    def test_get_indexing_status(self, client: "DifyDatasetClient", test_document: dict):
        """Test getting document indexing status."""
        result = client.documents.get_indexing_status(
            dataset_id=test_document["dataset_id"],
            batch=test_document["batch"],
        )

        assert isinstance(result, IndexingStatusResponse)
        assert isinstance(result.data, list)


class TestDocumentsBatchUpdateStatus:
    """Tests for documents.batch_update_status() method."""

    @pytest.mark.skip(reason="Server may not support this action")
    def test_batch_disable_documents(self, client: "DifyDatasetClient", test_document: dict):
        """Test batch disabling documents."""
        result = client.documents.batch_update_status(
            dataset_id=test_document["dataset_id"],
            action="disable",
            document_ids=[test_document["id"]],
        )

        assert result is not None

    @pytest.mark.skip(reason="Server may not support this action")
    def test_batch_enable_documents(self, client: "DifyDatasetClient", test_document: dict):
        """Test batch enabling documents."""
        # First disable
        client.documents.batch_update_status(
            dataset_id=test_document["dataset_id"],
            action="disable",
            document_ids=[test_document["id"]],
        )

        # Then enable
        result = client.documents.batch_update_status(
            dataset_id=test_document["dataset_id"],
            action="enable",
            document_ids=[test_document["id"]],
        )

        assert result is not None

    @pytest.mark.skip(reason="Server may not support this action")
    def test_batch_archive_documents(self, client: "DifyDatasetClient", test_document: dict):
        """Test batch archiving documents."""
        result = client.documents.batch_update_status(
            dataset_id=test_document["dataset_id"],
            action="archive",
            document_ids=[test_document["id"]],
        )

        assert result is not None

    @pytest.mark.skip(reason="Server may not support this action")
    def test_batch_unarchive_documents(self, client: "DifyDatasetClient", test_document: dict):
        """Test batch unarchiving documents."""
        # First archive
        client.documents.batch_update_status(
            dataset_id=test_document["dataset_id"],
            action="archive",
            document_ids=[test_document["id"]],
        )

        # Then unarchive
        result = client.documents.batch_update_status(
            dataset_id=test_document["dataset_id"],
            action="un_archive",
            document_ids=[test_document["id"]],
        )

        assert result is not None


class TestDocumentsGetUploadFile:
    """Tests for documents.get_upload_file() method."""

    @pytest.mark.skip(reason="API may not be available for text-created documents")
    def test_get_upload_file(self, client: "DifyDatasetClient", test_document: dict):
        """Test getting uploaded file information."""
        result = client.documents.get_upload_file(
            dataset_id=test_document["dataset_id"],
            document_id=test_document["id"],
        )

        # Result may be empty dict or contain file info
        assert isinstance(result, dict)
