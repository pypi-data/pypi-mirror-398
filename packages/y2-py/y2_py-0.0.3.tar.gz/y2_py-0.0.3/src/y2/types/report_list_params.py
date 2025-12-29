# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["ReportListParams"]


class ReportListParams(TypedDict, total=False):
    limit: int
    """Maximum number of reports to return"""

    profile_id: Annotated[str, PropertyInfo(alias="profileId")]
    """Filter reports by profile ID"""
