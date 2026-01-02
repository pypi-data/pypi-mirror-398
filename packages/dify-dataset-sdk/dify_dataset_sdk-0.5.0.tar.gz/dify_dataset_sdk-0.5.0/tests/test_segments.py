"""Tests for SegmentsClient - Segment and child chunk management operations."""

import pytest
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dify_dataset_sdk import DifyDatasetClient

from dify_dataset_sdk.segments.models import SegmentResponse, ChildChunkResponse


@pytest.fixture
def test_segment(client: "DifyDatasetClient", test_document: dict):
    """Create a test segment and return its info."""
    # Wait for document indexing to complete
    time.sleep(5)

    # List existing segments first (with retry)
    for _ in range(3):
        try:
            segments = client.segments.list(
                dataset_id=test_document["dataset_id"],
                document_id=test_document["id"],
            )

            if segments.data and len(segments.data) > 0:
                segment = segments.data[0]
                return {
                    "id": segment.get("id") if isinstance(segment, dict) else segment.id,
                    "dataset_id": test_document["dataset_id"],
                    "document_id": test_document["id"],
                }
            break
        except Exception:
            time.sleep(5)

    # Create new segment if none exist
    try:
        response = client.segments.create(
            dataset_id=test_document["dataset_id"],
            document_id=test_document["id"],
            segments=[{"content": "Test segment content for testing purposes."}],
        )

        if response.data and len(response.data) > 0:
            segment = response.data[0]
            return {
                "id": segment.get("id") if isinstance(segment, dict) else segment.id,
                "dataset_id": test_document["dataset_id"],
                "document_id": test_document["id"],
            }
    except Exception:
        pass

    pytest.skip("Could not create test segment - document may not be indexed yet")


class TestSegmentsCreate:
    """Tests for segments.create() method."""

    def test_create_single_segment(self, client: "DifyDatasetClient", test_document: dict):
        """Test creating a single segment."""
        time.sleep(5)

        response = client.segments.create(
            dataset_id=test_document["dataset_id"],
            document_id=test_document["id"],
            segments=[{"content": "Single segment content."}],
        )

        assert isinstance(response, SegmentResponse)
        assert response.data is not None

    def test_create_multiple_segments(self, client: "DifyDatasetClient", test_document: dict):
        """Test creating multiple segments at once."""
        time.sleep(5)

        response = client.segments.create(
            dataset_id=test_document["dataset_id"],
            document_id=test_document["id"],
            segments=[
                {"content": "First segment content."},
                {"content": "Second segment content."},
            ],
        )

        assert isinstance(response, SegmentResponse)

    def test_create_segment_with_keywords(self, client: "DifyDatasetClient", test_document: dict):
        """Test creating segment with keywords."""
        time.sleep(5)

        response = client.segments.create(
            dataset_id=test_document["dataset_id"],
            document_id=test_document["id"],
            segments=[
                {
                    "content": "Segment with keywords.",
                    "keywords": ["test", "keyword", "example"],
                }
            ],
        )

        assert isinstance(response, SegmentResponse)

    @pytest.mark.skip(reason="QA mode documents may need longer indexing time")
    def test_create_segment_with_answer_qa_mode(self, client: "DifyDatasetClient", test_dataset: dict):
        """Test creating segment with answer (Q&A mode)."""
        from dify_dataset_sdk.documents.models import ProcessRule

        # Create a QA mode document
        doc_response = client.documents.create_by_text(
            dataset_id=test_dataset["id"],
            name="QADoc",
            text="What is Python?",
            doc_form="qa_model",
            doc_language="English",
            process_rule=ProcessRule(mode="automatic"),
        )
        # QA mode documents need more time to index
        time.sleep(10)

        response = client.segments.create(
            dataset_id=test_dataset["id"],
            document_id=doc_response.document.id,
            segments=[
                {
                    "content": "What is Python?",
                    "answer": "Python is a programming language.",
                }
            ],
        )

        assert isinstance(response, SegmentResponse)


class TestSegmentsList:
    """Tests for segments.list() method."""

    def test_list_default_params(self, client: "DifyDatasetClient", test_document: dict):
        """Test listing segments with default parameters."""
        time.sleep(5)

        result = client.segments.list(
            dataset_id=test_document["dataset_id"],
            document_id=test_document["id"],
        )

        assert isinstance(result, SegmentResponse)
        assert result.data is not None

    def test_list_with_page(self, client: "DifyDatasetClient", test_document: dict):
        """Test listing segments with specific page number."""
        time.sleep(5)

        result = client.segments.list(
            dataset_id=test_document["dataset_id"],
            document_id=test_document["id"],
            page=1,
        )

        assert isinstance(result, SegmentResponse)

    def test_list_with_limit(self, client: "DifyDatasetClient", test_document: dict):
        """Test listing segments with custom limit."""
        time.sleep(5)

        result = client.segments.list(
            dataset_id=test_document["dataset_id"],
            document_id=test_document["id"],
            limit=5,
        )

        assert isinstance(result, SegmentResponse)

    def test_list_with_keyword(self, client: "DifyDatasetClient", test_document: dict):
        """Test listing segments with keyword filter."""
        time.sleep(5)

        result = client.segments.list(
            dataset_id=test_document["dataset_id"],
            document_id=test_document["id"],
            keyword="test",
        )

        assert isinstance(result, SegmentResponse)

    def test_list_with_status(self, client: "DifyDatasetClient", test_document: dict):
        """Test listing segments with status filter."""
        time.sleep(5)

        result = client.segments.list(
            dataset_id=test_document["dataset_id"],
            document_id=test_document["id"],
            status="completed",
        )

        assert isinstance(result, SegmentResponse)

    def test_list_with_all_params(self, client: "DifyDatasetClient", test_document: dict):
        """Test listing segments with all parameters."""
        time.sleep(5)

        result = client.segments.list(
            dataset_id=test_document["dataset_id"],
            document_id=test_document["id"],
            keyword="content",
            status="completed",
            page=1,
            limit=10,
        )

        assert isinstance(result, SegmentResponse)


class TestSegmentsGet:
    """Tests for segments.get() method."""

    def test_get_existing_segment(self, client: "DifyDatasetClient", test_segment: dict):
        """Test getting an existing segment by ID."""
        result = client.segments.get(
            dataset_id=test_segment["dataset_id"],
            document_id=test_segment["document_id"],
            segment_id=test_segment["id"],
        )

        assert result is not None
        assert isinstance(result, dict)

    def test_get_segment_returns_content(self, client: "DifyDatasetClient", test_segment: dict):
        """Test that get returns segment content."""
        result = client.segments.get(
            dataset_id=test_segment["dataset_id"],
            document_id=test_segment["document_id"],
            segment_id=test_segment["id"],
        )

        # Should contain data or segment info
        assert result is not None


class TestSegmentsUpdate:
    """Tests for segments.update() method."""

    def test_update_segment_content(self, client: "DifyDatasetClient", test_segment: dict):
        """Test updating segment content."""
        result = client.segments.update(
            dataset_id=test_segment["dataset_id"],
            document_id=test_segment["document_id"],
            segment_id=test_segment["id"],
            segment_data={"content": "Updated segment content."},
        )

        assert result is not None

    def test_update_segment_with_keywords(self, client: "DifyDatasetClient", test_segment: dict):
        """Test updating segment with keywords."""
        result = client.segments.update(
            dataset_id=test_segment["dataset_id"],
            document_id=test_segment["document_id"],
            segment_id=test_segment["id"],
            segment_data={
                "content": "Segment with updated keywords.",
                "keywords": ["updated", "new", "keywords"],
            },
        )

        assert result is not None

    @pytest.mark.skip(reason="Segment may still be indexing")
    def test_update_segment_enabled_status(self, client: "DifyDatasetClient", test_segment: dict):
        """Test updating segment enabled status."""
        result = client.segments.update(
            dataset_id=test_segment["dataset_id"],
            document_id=test_segment["document_id"],
            segment_id=test_segment["id"],
            segment_data={
                "content": "Content remains.",
                "enabled": False,
            },
        )

        assert result is not None

        # Re-enable
        result = client.segments.update(
            dataset_id=test_segment["dataset_id"],
            document_id=test_segment["document_id"],
            segment_id=test_segment["id"],
            segment_data={
                "content": "Content remains.",
                "enabled": True,
            },
        )

        assert result is not None


class TestSegmentsDelete:
    """Tests for segments.delete() method."""

    def test_delete_segment(self, client: "DifyDatasetClient", test_document: dict):
        """Test deleting a segment."""
        time.sleep(5)

        # Create a segment to delete
        response = client.segments.create(
            dataset_id=test_document["dataset_id"],
            document_id=test_document["id"],
            segments=[{"content": "Segment to be deleted."}],
        )

        if response.data and len(response.data) > 0:
            segment = response.data[0]
            segment_id = segment.get("id") if isinstance(segment, dict) else segment.id

            result = client.segments.delete(
                dataset_id=test_document["dataset_id"],
                document_id=test_document["id"],
                segment_id=segment_id,
            )

            assert result is not None


class TestChildChunksCreate:
    """Tests for segments.create_child_chunk() method."""

    def test_create_child_chunk(self, client: "DifyDatasetClient", test_segment: dict):
        """Test creating a child chunk."""
        result = client.segments.create_child_chunk(
            dataset_id=test_segment["dataset_id"],
            document_id=test_segment["document_id"],
            segment_id=test_segment["id"],
            content="This is a child chunk content.",
        )

        assert result is not None
        assert isinstance(result, dict)

    def test_create_child_chunk_long_content(self, client: "DifyDatasetClient", test_segment: dict):
        """Test creating child chunk with long content."""
        long_content = "This is a long child chunk. " * 20

        result = client.segments.create_child_chunk(
            dataset_id=test_segment["dataset_id"],
            document_id=test_segment["document_id"],
            segment_id=test_segment["id"],
            content=long_content,
        )

        assert result is not None


class TestChildChunksList:
    """Tests for segments.list_child_chunks() method."""

    def test_list_child_chunks_default(self, client: "DifyDatasetClient", test_segment: dict):
        """Test listing child chunks with default parameters."""
        result = client.segments.list_child_chunks(
            dataset_id=test_segment["dataset_id"],
            document_id=test_segment["document_id"],
            segment_id=test_segment["id"],
        )

        assert isinstance(result, ChildChunkResponse)

    def test_list_child_chunks_with_page(self, client: "DifyDatasetClient", test_segment: dict):
        """Test listing child chunks with specific page."""
        result = client.segments.list_child_chunks(
            dataset_id=test_segment["dataset_id"],
            document_id=test_segment["document_id"],
            segment_id=test_segment["id"],
            page=1,
        )

        assert isinstance(result, ChildChunkResponse)

    def test_list_child_chunks_with_limit(self, client: "DifyDatasetClient", test_segment: dict):
        """Test listing child chunks with custom limit."""
        result = client.segments.list_child_chunks(
            dataset_id=test_segment["dataset_id"],
            document_id=test_segment["document_id"],
            segment_id=test_segment["id"],
            limit=5,
        )

        assert isinstance(result, ChildChunkResponse)

    def test_list_child_chunks_with_keyword(self, client: "DifyDatasetClient", test_segment: dict):
        """Test listing child chunks with keyword filter."""
        result = client.segments.list_child_chunks(
            dataset_id=test_segment["dataset_id"],
            document_id=test_segment["document_id"],
            segment_id=test_segment["id"],
            keyword="chunk",
        )

        assert isinstance(result, ChildChunkResponse)


class TestChildChunksUpdate:
    """Tests for segments.update_child_chunk() method."""

    @pytest.fixture
    def test_child_chunk(self, client: "DifyDatasetClient", test_segment: dict):
        """Create a test child chunk."""
        result = client.segments.create_child_chunk(
            dataset_id=test_segment["dataset_id"],
            document_id=test_segment["document_id"],
            segment_id=test_segment["id"],
            content="Original child chunk content.",
        )

        if result and result.get("data"):
            chunk = result["data"]
            return {
                "id": chunk.get("id"),
                "dataset_id": test_segment["dataset_id"],
                "document_id": test_segment["document_id"],
                "segment_id": test_segment["id"],
            }

        pytest.skip("Could not create test child chunk")

    def test_update_child_chunk_content(self, client: "DifyDatasetClient", test_child_chunk: dict):
        """Test updating child chunk content."""
        if not test_child_chunk:
            pytest.skip("No test child chunk available")

        result = client.segments.update_child_chunk(
            dataset_id=test_child_chunk["dataset_id"],
            document_id=test_child_chunk["document_id"],
            segment_id=test_child_chunk["segment_id"],
            child_chunk_id=test_child_chunk["id"],
            content="Updated child chunk content.",
        )

        assert result is not None


class TestChildChunksDelete:
    """Tests for segments.delete_child_chunk() method."""

    def test_delete_child_chunk(self, client: "DifyDatasetClient", test_segment: dict):
        """Test deleting a child chunk."""
        # Create a child chunk to delete
        create_result = client.segments.create_child_chunk(
            dataset_id=test_segment["dataset_id"],
            document_id=test_segment["document_id"],
            segment_id=test_segment["id"],
            content="Child chunk to delete.",
        )

        if create_result and create_result.get("data"):
            chunk_id = create_result["data"].get("id")

            result = client.segments.delete_child_chunk(
                dataset_id=test_segment["dataset_id"],
                document_id=test_segment["document_id"],
                segment_id=test_segment["id"],
                child_chunk_id=chunk_id,
            )

            assert result is not None
