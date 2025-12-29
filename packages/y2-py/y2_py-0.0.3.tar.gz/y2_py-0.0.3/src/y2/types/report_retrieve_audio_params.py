# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import TypedDict

__all__ = ["ReportRetrieveAudioParams"]


class ReportRetrieveAudioParams(TypedDict, total=False):
    redirect: bool
    """If true, returns 302 redirect to audio CDN URL"""
