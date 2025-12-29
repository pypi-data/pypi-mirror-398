# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel
from .audio_metadata import AudioMetadata

__all__ = [
    "ReportRetrieveResponse",
    "Data",
    "DataContent",
    "DataMetadata",
    "DataMetadataFreshnessMetadata",
    "DataMetadataRecursionMetadata",
]


class DataContent(BaseModel):
    html: Optional[str] = None
    """Full HTML content"""

    summary: Optional[str] = None
    """SMS-friendly summary"""


class DataMetadataFreshnessMetadata(BaseModel):
    """Source freshness validation results"""

    accessible_links: Optional[int] = FieldInfo(alias="accessibleLinks", default=None)

    average_age_ms: Optional[int] = FieldInfo(alias="averageAgeMs", default=None)
    """Average source age in milliseconds"""

    freshness_score: Optional[float] = FieldInfo(alias="freshnessScore", default=None)
    """Overall freshness score (higher = fresher)"""

    stale_sources_count: Optional[int] = FieldInfo(alias="staleSourcesCount", default=None)

    total_links: Optional[int] = FieldInfo(alias="totalLinks", default=None)

    validated_at: Optional[int] = FieldInfo(alias="validatedAt", default=None)


class DataMetadataRecursionMetadata(BaseModel):
    """Metadata about recursive research execution"""

    depth: Optional[int] = None
    """Recursion depth achieved (0 = standard report)"""

    fallback_reason: Optional[str] = FieldInfo(alias="fallbackReason", default=None)
    """Reason if fallback to standard generation occurred"""

    layers_processed: Optional[int] = FieldInfo(alias="layersProcessed", default=None)

    strategy: Optional[Literal["breadth-first", "depth-first", "hybrid"]] = None

    subtopics_generated: Optional[List[str]] = FieldInfo(alias="subtopicsGenerated", default=None)

    total_sources_collected: Optional[int] = FieldInfo(alias="totalSourcesCollected", default=None)

    total_time_ms: Optional[int] = FieldInfo(alias="totalTimeMs", default=None)

    unique_sources_aggregated: Optional[int] = FieldInfo(alias="uniqueSourcesAggregated", default=None)


class DataMetadata(BaseModel):
    freshness_metadata: Optional[DataMetadataFreshnessMetadata] = FieldInfo(alias="freshnessMetadata", default=None)
    """Source freshness validation results"""

    model: Optional[str] = None

    recursion_metadata: Optional[DataMetadataRecursionMetadata] = FieldInfo(alias="recursionMetadata", default=None)
    """Metadata about recursive research execution"""

    total_cost: Optional[float] = FieldInfo(alias="totalCost", default=None)


class Data(BaseModel):
    id: str

    content: DataContent

    generated_at: int = FieldInfo(alias="generatedAt")

    generated_at_iso: datetime = FieldInfo(alias="generatedAtISO")

    profile_id: str = FieldInfo(alias="profileId")

    audio: Optional[AudioMetadata] = None

    metadata: Optional[DataMetadata] = None

    profile_name: Optional[str] = FieldInfo(alias="profileName", default=None)

    profile_topic: Optional[str] = FieldInfo(alias="profileTopic", default=None)

    sources: Optional[List[str]] = None

    topic: Optional[str] = None


class ReportRetrieveResponse(BaseModel):
    data: Data
