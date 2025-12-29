# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["ProfileListResponse", "Data", "DataProfile", "Meta"]


class DataProfile(BaseModel):
    audio_enabled: Optional[bool] = FieldInfo(alias="audioEnabled", default=None)

    frequency: Optional[str] = None

    name: Optional[str] = None

    status: Optional[str] = None

    topic: Optional[str] = None


class Data(BaseModel):
    delivery_method: Literal["email", "sms", "webhook", "both_email_sms"] = FieldInfo(alias="deliveryMethod")

    is_active: bool = FieldInfo(alias="isActive")

    profile_id: str = FieldInfo(alias="profileId")

    subscribed_at: int = FieldInfo(alias="subscribedAt")

    subscription_id: str = FieldInfo(alias="subscriptionId")

    profile: Optional[DataProfile] = None


class Meta(BaseModel):
    count: Optional[int] = None


class ProfileListResponse(BaseModel):
    data: List[Data]

    meta: Meta
