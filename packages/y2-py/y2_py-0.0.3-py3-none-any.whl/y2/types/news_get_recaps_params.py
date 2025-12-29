# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import TypedDict

from .timeframe_enum import TimeframeEnum

__all__ = ["NewsGetRecapsParams"]


class NewsGetRecapsParams(TypedDict, total=False):
    timeframe: TimeframeEnum
    """Time period for recaps"""

    topics: str
    """
    Comma-separated list of topics. Valid topics: ai, ai_agents, aptos, base,
    bitcoin, crypto, dats, defi, ethereum, hyperliquid, machine_learning, macro,
    ondo, perps, ripple, rwa, solana, tech, virtuals
    """
