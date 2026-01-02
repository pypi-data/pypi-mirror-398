"""Models for embedding models API module."""

from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field


class EmbeddingModelResponse(BaseModel):
    """Response model for embedding model list."""

    model_config = ConfigDict(extra="ignore")

    data: List[Dict[str, Any]] = Field(description="Embedding model list")
