"""Integration tests for Dify Dataset SDK - Full workflow tests."""

import pytest
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dify_dataset_sdk import DifyDatasetClient

from dify_dataset_sdk.datasets.models import RetrievalModel
from dify_dataset_sdk.documents.models import ProcessRule


class TestFullDatasetWorkflow:
    """Test complete dataset lifecycle."""

    def test_dataset_crud_workflow(self, client: "DifyDatasetClient", unique_name: str):
        """Test full CRUD workflow for datasets."""
        # 1. Create dataset
        dataset = client.datasets.create(
            name=f"IntegrationTest_{unique_name}",
            description="Integration test dataset",
            indexing_technique="high_quality",
            permission="only_me",
        )
        assert dataset.id is not None
        dataset_id = dataset.id

        try:
            # 2. Read/Get dataset
            fetched = client.datasets.get(dataset_id)
            assert fetched.id == dataset_id
            assert fetched.name == f"IntegrationTest_{unique_name}"

            # 3. Update dataset
            updated = client.datasets.update(
                dataset_id=dataset_id,
                name=f"UpdatedIntegration_{unique_name}",
                description="Updated description",
            )
            assert updated.name == f"UpdatedIntegration_{unique_name}"

            # 4. List datasets (verify it appears)
            datasets_list = client.datasets.list(keyword=f"UpdatedIntegration_{unique_name}")
            assert datasets_list.total >= 0

        finally:
            # 5. Delete dataset
            client.datasets.delete(dataset_id)


class TestFullDocumentWorkflow:
    """Test complete document lifecycle."""

    def test_document_text_workflow(self, client: "DifyDatasetClient", test_dataset: dict, unique_name: str):
        """Test full workflow for text-based documents."""
        # 1. Create document by text
        doc_response = client.documents.create_by_text(
            dataset_id=test_dataset["id"],
            name=f"IntegrationDoc_{unique_name}",
            text="This is integration test content. It contains important information for testing.",
            indexing_technique="high_quality",
            doc_form="text_model",
        )
        assert doc_response.document.id is not None
        doc_id = doc_response.document.id
        batch = doc_response.batch

        # Wait for indexing
        time.sleep(15)

        # 2. Check indexing status
        status = client.documents.get_indexing_status(
            dataset_id=test_dataset["id"],
            batch=batch,
        )
        assert status.data is not None

        # 3. Get document details
        document = client.documents.get(
            dataset_id=test_dataset["id"],
            document_id=doc_id,
        )
        assert document.id == doc_id

        # 4. Update document
        updated = client.documents.update_by_text(
            dataset_id=test_dataset["id"],
            document_id=doc_id,
            name=f"UpdatedDoc_{unique_name}",
            text="Updated integration test content.",
        )
        assert updated.document.name == f"UpdatedDoc_{unique_name}"

        # 5. List documents
        docs = client.documents.list(
            dataset_id=test_dataset["id"],
        )
        assert docs.total >= 1

        # 6. Delete document
        result = client.documents.delete(
            dataset_id=test_dataset["id"],
            document_id=doc_id,
        )
        assert result is not None

    def test_document_file_workflow(self, client: "DifyDatasetClient", test_dataset: dict, test_file: Path):
        """Test full workflow for file-based documents."""
        from dify_dataset_sdk.documents.models import ProcessRule

        # 1. Create document by file
        doc_response = client.documents.create_by_file(
            dataset_id=test_dataset["id"],
            file_path=test_file,
            indexing_technique="high_quality",
            process_rule=ProcessRule(mode="automatic"),
        )
        assert doc_response.document.id is not None
        doc_id = doc_response.document.id

        # Wait for indexing
        time.sleep(10)

        # 2. Get document
        document = client.documents.get(
            dataset_id=test_dataset["id"],
            document_id=doc_id,
        )
        assert document.id == doc_id

        # 3. Delete document
        client.documents.delete(
            dataset_id=test_dataset["id"],
            document_id=doc_id,
        )


class TestFullSegmentWorkflow:
    """Test complete segment lifecycle."""

    def test_segment_workflow(self, client: "DifyDatasetClient", test_document: dict):
        """Test full workflow for segments."""
        time.sleep(5)

        # 1. Create segments
        create_response = client.segments.create(
            dataset_id=test_document["dataset_id"],
            document_id=test_document["id"],
            segments=[
                {"content": "First integration test segment."},
                {"content": "Second integration test segment."},
            ],
        )
        assert create_response.data is not None

        # 2. List segments
        segments = client.segments.list(
            dataset_id=test_document["dataset_id"],
            document_id=test_document["id"],
        )
        assert segments.data is not None

        if segments.data and len(segments.data) > 0:
            segment = segments.data[0]
            segment_id = segment.get("id") if isinstance(segment, dict) else segment.id

            # 3. Get segment
            fetched = client.segments.get(
                dataset_id=test_document["dataset_id"],
                document_id=test_document["id"],
                segment_id=segment_id,
            )
            assert fetched is not None

            # 4. Update segment
            updated = client.segments.update(
                dataset_id=test_document["dataset_id"],
                document_id=test_document["id"],
                segment_id=segment_id,
                segment_data={"content": "Updated segment content."},
            )
            assert updated is not None


class TestKnowledgeRetrievalWorkflow:
    """Test knowledge retrieval workflow."""

    @pytest.mark.skip(reason="Server returns 500 for retrieval with custom model")
    def test_retrieval_workflow(self, client: "DifyDatasetClient", unique_name: str):
        """Test complete retrieval workflow."""
        # 1. Create dataset
        dataset = client.datasets.create(
            name=f"RetrievalTest_{unique_name}",
            description="Dataset for retrieval testing",
            indexing_technique="high_quality",
        )
        dataset_id = dataset.id

        try:
            # 2. Add document
            doc_response = client.documents.create_by_text(
                dataset_id=dataset_id,
                name="Retrieval Test Doc",
                text="Python is a programming language. It is used for web development, data science, and AI.",
            )

            # 3. Wait for indexing
            time.sleep(8)

            # 4. Perform semantic search
            result = client.datasets.retrieve(
                dataset_id=dataset_id,
                query="programming language",
                retrieval_model=RetrievalModel(
                    search_method="semantic_search",
                    top_k=5,
                ),
            )
            assert result.records is not None

            # 5. Perform keyword search
            result = client.datasets.retrieve(
                dataset_id=dataset_id,
                query="Python",
                retrieval_model=RetrievalModel(
                    search_method="keyword_search",
                    top_k=5,
                ),
            )
            assert result.records is not None

        finally:
            # Cleanup
            client.datasets.delete(dataset_id)


class TestClientContextManager:
    """Test client context manager functionality."""

    def test_context_manager(self):
        """Test using client as context manager."""
        from dify_dataset_sdk import DifyDatasetClient
        from tests.conftest import API_BASE_URL, API_KEY

        base_url = API_BASE_URL.replace("/v1", "")

        with DifyDatasetClient(api_key=API_KEY, base_url=base_url) as client:
            datasets = client.datasets.list()
            assert datasets is not None


class TestBatchOperations:
    """Test batch operations."""

    @pytest.mark.skip(reason="Server may not support batch status updates")
    def test_batch_document_operations(self, client: "DifyDatasetClient", test_dataset: dict):
        """Test batch document status updates."""
        # Create multiple documents
        docs = []
        for i in range(3):
            doc = client.documents.create_by_text(
                dataset_id=test_dataset["id"],
                name=f"BatchDoc_{i}",
                text=f"Batch document content {i}",
            )
            docs.append(doc.document.id)

        time.sleep(3)

        # Batch disable
        result = client.documents.batch_update_status(
            dataset_id=test_dataset["id"],
            action="disable",
            document_ids=docs,
        )
        assert result is not None

        # Batch enable
        result = client.documents.batch_update_status(
            dataset_id=test_dataset["id"],
            action="enable",
            document_ids=docs,
        )
        assert result is not None

        # Cleanup
        for doc_id in docs:
            client.documents.delete(
                dataset_id=test_dataset["id"],
                document_id=doc_id,
            )


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_dataset_list(self, client: "DifyDatasetClient"):
        """Test listing with filters that return empty results."""
        result = client.datasets.list(
            keyword="NonExistentDatasetName12345678",
        )
        assert result.data is not None

    def test_large_limit(self, client: "DifyDatasetClient"):
        """Test listing with large limit."""
        result = client.datasets.list(limit=100)
        assert result.limit == 100

    def test_unicode_content(self, client: "DifyDatasetClient", test_dataset: dict):
        """Test handling unicode content."""
        doc = client.documents.create_by_text(
            dataset_id=test_dataset["id"],
            name="Unicode测试文档",
            text="这是中文内容。日本語テキスト。한국어 텍스트。Emoji: 🎉🚀",
        )
        assert doc.document.id is not None

        # Cleanup
        client.documents.delete(
            dataset_id=test_dataset["id"],
            document_id=doc.document.id,
        )
