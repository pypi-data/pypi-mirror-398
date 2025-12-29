# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import TypedDict

__all__ = ["NewsListParams"]


class NewsListParams(TypedDict, total=False):
    limit: int
    """Maximum number of items to return"""

    topics: str
    """
    Comma-separated list of topics to filter by. Valid topics: ai, ai_agents, aptos,
    base, bitcoin, crypto, dats, defi, ethereum, hyperliquid, machine_learning,
    macro, ondo, perps, ripple, rwa, solana, tech, virtuals. Default: crypto,
    ai_agents, macro, bitcoin, ethereum, tech
    """
