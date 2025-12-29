# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from .._models import BaseModel
from .topic_enum import TopicEnum

__all__ = ["NewsListFeedsResponse", "Data", "Meta"]


class Data(BaseModel):
    id: TopicEnum
    """Available news feed topics from GloriaAI"""

    name: str
    """Human-readable name"""

    description: Optional[str] = None
    """Feed description"""


class Meta(BaseModel):
    count: Optional[int] = None


class NewsListFeedsResponse(BaseModel):
    data: List[Data]

    meta: Meta
