"""Segments module for Dify Dataset SDK."""

from .client import SegmentsClient
from .models import (
    ChildChunk,
    ChildChunkResponse,
    CreateChildChunkRequest,
    CreateSegmentRequest,
    Segment,
    SegmentResponse,
    UpdateChildChunkRequest,
    UpdateSegmentRequest,
)

__all__ = [
    "SegmentsClient",
    "Segment",
    "SegmentResponse",
    "ChildChunk",
    "ChildChunkResponse",
    "CreateSegmentRequest",
    "UpdateSegmentRequest",
    "CreateChildChunkRequest",
    "UpdateChildChunkRequest",
]
