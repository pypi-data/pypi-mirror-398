# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Optional

from .._models import BaseModel
from .topic_enum import TopicEnum
from .timeframe_enum import TimeframeEnum

__all__ = ["NewsGetRecapsResponse", "Meta"]


class Meta(BaseModel):
    timeframe: Optional[TimeframeEnum] = None
    """Time period for recap data"""

    topics: Optional[List[TopicEnum]] = None


class NewsGetRecapsResponse(BaseModel):
    data: Dict[str, object]

    meta: Meta
