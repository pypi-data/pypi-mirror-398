# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel
from .topic_enum import TopicEnum

__all__ = ["NewsListResponse", "Data", "Meta"]


class Data(BaseModel):
    id: str

    signal: str
    """Primary signal/headline"""

    timestamp: int
    """Unix timestamp (seconds)"""

    timestamp_iso: datetime = FieldInfo(alias="timestampISO")

    author: Optional[str] = None

    categories: Optional[List[str]] = None

    content: Optional[str] = None
    """Full context"""

    narrative_id: Optional[str] = FieldInfo(alias="narrativeId", default=None)

    sentiment: Optional[Literal["bullish", "bearish", "neutral"]] = None
    """Sentiment classification for news items"""

    sentiment_value: Optional[float] = FieldInfo(alias="sentimentValue", default=None)

    sources: Optional[List[str]] = None

    summary: Optional[str] = None
    """Short context summary"""

    tokens: Optional[List[str]] = None
    """Related tokens/assets"""

    tweet_url: Optional[str] = FieldInfo(alias="tweetUrl", default=None)


class Meta(BaseModel):
    count: Optional[int] = None

    limit: Optional[int] = None

    topics: Optional[List[TopicEnum]] = None


class NewsListResponse(BaseModel):
    data: List[Data]

    meta: Meta
