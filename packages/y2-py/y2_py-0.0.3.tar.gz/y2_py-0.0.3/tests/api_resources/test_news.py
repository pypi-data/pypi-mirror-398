# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from y2 import Y2, AsyncY2
from y2.types import (
    NewsListResponse,
    NewsGetRecapsResponse,
    NewsListFeedsResponse,
)
from tests.utils import assert_matches_type

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestNews:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Y2) -> None:
        news = client.news.list()
        assert_matches_type(NewsListResponse, news, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: Y2) -> None:
        news = client.news.list(
            limit=1,
            topics="crypto,ai_agents,bitcoin",
        )
        assert_matches_type(NewsListResponse, news, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Y2) -> None:
        response = client.news.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        news = response.parse()
        assert_matches_type(NewsListResponse, news, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Y2) -> None:
        with client.news.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            news = response.parse()
            assert_matches_type(NewsListResponse, news, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_recaps(self, client: Y2) -> None:
        news = client.news.get_recaps()
        assert_matches_type(NewsGetRecapsResponse, news, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_recaps_with_all_params(self, client: Y2) -> None:
        news = client.news.get_recaps(
            timeframe="12h",
            topics="topics",
        )
        assert_matches_type(NewsGetRecapsResponse, news, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_get_recaps(self, client: Y2) -> None:
        response = client.news.with_raw_response.get_recaps()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        news = response.parse()
        assert_matches_type(NewsGetRecapsResponse, news, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_get_recaps(self, client: Y2) -> None:
        with client.news.with_streaming_response.get_recaps() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            news = response.parse()
            assert_matches_type(NewsGetRecapsResponse, news, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_feeds(self, client: Y2) -> None:
        news = client.news.list_feeds()
        assert_matches_type(NewsListFeedsResponse, news, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list_feeds(self, client: Y2) -> None:
        response = client.news.with_raw_response.list_feeds()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        news = response.parse()
        assert_matches_type(NewsListFeedsResponse, news, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list_feeds(self, client: Y2) -> None:
        with client.news.with_streaming_response.list_feeds() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            news = response.parse()
            assert_matches_type(NewsListFeedsResponse, news, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncNews:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncY2) -> None:
        news = await async_client.news.list()
        assert_matches_type(NewsListResponse, news, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncY2) -> None:
        news = await async_client.news.list(
            limit=1,
            topics="crypto,ai_agents,bitcoin",
        )
        assert_matches_type(NewsListResponse, news, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncY2) -> None:
        response = await async_client.news.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        news = await response.parse()
        assert_matches_type(NewsListResponse, news, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncY2) -> None:
        async with async_client.news.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            news = await response.parse()
            assert_matches_type(NewsListResponse, news, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_recaps(self, async_client: AsyncY2) -> None:
        news = await async_client.news.get_recaps()
        assert_matches_type(NewsGetRecapsResponse, news, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_recaps_with_all_params(self, async_client: AsyncY2) -> None:
        news = await async_client.news.get_recaps(
            timeframe="12h",
            topics="topics",
        )
        assert_matches_type(NewsGetRecapsResponse, news, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_get_recaps(self, async_client: AsyncY2) -> None:
        response = await async_client.news.with_raw_response.get_recaps()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        news = await response.parse()
        assert_matches_type(NewsGetRecapsResponse, news, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_get_recaps(self, async_client: AsyncY2) -> None:
        async with async_client.news.with_streaming_response.get_recaps() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            news = await response.parse()
            assert_matches_type(NewsGetRecapsResponse, news, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_feeds(self, async_client: AsyncY2) -> None:
        news = await async_client.news.list_feeds()
        assert_matches_type(NewsListFeedsResponse, news, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list_feeds(self, async_client: AsyncY2) -> None:
        response = await async_client.news.with_raw_response.list_feeds()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        news = await response.parse()
        assert_matches_type(NewsListFeedsResponse, news, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list_feeds(self, async_client: AsyncY2) -> None:
        async with async_client.news.with_streaming_response.list_feeds() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            news = await response.parse()
            assert_matches_type(NewsListFeedsResponse, news, path=["response"])

        assert cast(Any, response.is_closed) is True
