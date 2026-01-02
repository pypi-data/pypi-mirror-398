"""Pytest configuration and fixtures for Dify Dataset SDK tests."""

import os
import pytest
import time
from pathlib import Path
from typing import Generator

from dify_dataset_sdk import DifyDatasetClient


# Test configuration
API_BASE_URL = os.getenv("DIFY_API_URL", "http://dify.jianxiaozhi.chat/v1")
API_KEY = os.getenv("DIFY_API_KEY", "dataset-vYbds107bwFBMLG3oDq7pRxK")


@pytest.fixture(scope="session")
def client() -> Generator[DifyDatasetClient, None, None]:
    """Create a Dify client for the test session."""
    # Remove /v1 suffix if present since client adds it
    base_url = API_BASE_URL.replace("/v1", "")
    client = DifyDatasetClient(
        api_key=API_KEY,
        base_url=base_url,
        timeout=60.0,
    )
    yield client
    client.close()


@pytest.fixture
def unique_name() -> str:
    """Generate a unique name for test resources."""
    return f"test_{int(time.time() * 1000)}"


@pytest.fixture
def test_dataset(client: DifyDatasetClient, unique_name: str) -> Generator[dict, None, None]:
    """Create a test dataset and clean up after test."""
    dataset = client.datasets.create(
        name=f"TestDataset_{unique_name}",
        description="Test dataset for unit tests",
    )
    yield {"id": dataset.id, "name": dataset.name}
    # Cleanup
    try:
        client.datasets.delete(dataset.id)
    except Exception:
        pass


@pytest.fixture
def test_document(client: DifyDatasetClient, test_dataset: dict) -> Generator[dict, None, None]:
    """Create a test document and clean up after test."""
    from dify_dataset_sdk.documents.models import ProcessRule

    doc_response = client.documents.create_by_text(
        dataset_id=test_dataset["id"],
        name="TestDocument",
        text="This is test content for the document. It contains some text for testing purposes. More content here to ensure proper segmentation.",
        indexing_technique="high_quality",
        process_rule=ProcessRule(mode="automatic"),
    )
    # Wait for indexing to complete (documents need sufficient time for full indexing)
    time.sleep(15)
    yield {
        "id": doc_response.document.id,
        "batch": doc_response.batch,
        "dataset_id": test_dataset["id"],
    }
    # Cleanup handled by test_dataset deletion


@pytest.fixture
def test_file(tmp_path: Path) -> Path:
    """Create a temporary test file."""
    file_path = tmp_path / "test_document.txt"
    file_path.write_text("This is a test file content for upload testing.\nIt has multiple lines.\nLine 3 here.")
    return file_path


