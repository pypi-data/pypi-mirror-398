# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["ReportListResponse", "Data", "Meta"]


class Data(BaseModel):
    id: str
    """Report ID (Convex document ID)"""

    generated_at: int = FieldInfo(alias="generatedAt")
    """Unix timestamp (milliseconds)"""

    generated_at_iso: datetime = FieldInfo(alias="generatedAtISO")
    """ISO 8601 timestamp"""

    profile_id: str = FieldInfo(alias="profileId")
    """Profile ID this report belongs to"""

    has_audio: Optional[bool] = FieldInfo(alias="hasAudio", default=None)
    """Whether audio narration is available"""

    model: Optional[str] = None
    """LLM model used for generation"""

    summary: Optional[str] = None
    """Brief SMS-friendly summary"""

    topic: Optional[str] = None
    """Report topic"""


class Meta(BaseModel):
    count: Optional[int] = None

    limit: Optional[int] = None


class ReportListResponse(BaseModel):
    data: List[Data]

    meta: Meta
