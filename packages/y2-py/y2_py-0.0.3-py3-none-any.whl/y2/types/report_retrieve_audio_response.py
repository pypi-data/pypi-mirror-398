# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from .._models import BaseModel
from .audio_metadata import AudioMetadata

__all__ = ["ReportRetrieveAudioResponse"]


class ReportRetrieveAudioResponse(BaseModel):
    data: Optional[AudioMetadata] = None
