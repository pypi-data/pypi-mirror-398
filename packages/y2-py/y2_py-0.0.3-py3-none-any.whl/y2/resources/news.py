# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ..types import TimeframeEnum, news_list_params, news_get_recaps_params
from .._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from .._utils import maybe_transform, async_maybe_transform
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .._base_client import make_request_options
from ..types.timeframe_enum import TimeframeEnum
from ..types.news_list_response import NewsListResponse
from ..types.news_get_recaps_response import NewsGetRecapsResponse
from ..types.news_list_feeds_response import NewsListFeedsResponse

__all__ = ["NewsResource", "AsyncNewsResource"]


class NewsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> NewsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/y2-intel/y2-py#accessing-raw-response-data-eg-headers
        """
        return NewsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> NewsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/y2-intel/y2-py#with_streaming_response
        """
        return NewsResourceWithStreamingResponse(self)

    def list(
        self,
        *,
        limit: int | Omit = omit,
        topics: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> NewsListResponse:
        """Returns news items from the GloriaAI terminal cache.

        Supports filtering by
        topics and pagination.

        Args:
          limit: Maximum number of items to return

          topics: Comma-separated list of topics to filter by. Valid topics: ai, ai_agents, aptos,
              base, bitcoin, crypto, dats, defi, ethereum, hyperliquid, machine_learning,
              macro, ondo, perps, ripple, rwa, solana, tech, virtuals. Default: crypto,
              ai_agents, macro, bitcoin, ethereum, tech

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/news",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "limit": limit,
                        "topics": topics,
                    },
                    news_list_params.NewsListParams,
                ),
            ),
            cast_to=NewsListResponse,
        )

    def get_recaps(
        self,
        *,
        timeframe: TimeframeEnum | Omit = omit,
        topics: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> NewsGetRecapsResponse:
        """
        Returns AI-generated recap summaries for specified topics within a given
        timeframe.

        Args:
          timeframe: Time period for recaps

          topics: Comma-separated list of topics. Valid topics: ai, ai_agents, aptos, base,
              bitcoin, crypto, dats, defi, ethereum, hyperliquid, machine_learning, macro,
              ondo, perps, ripple, rwa, solana, tech, virtuals

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/news/recaps",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "timeframe": timeframe,
                        "topics": topics,
                    },
                    news_get_recaps_params.NewsGetRecapsParams,
                ),
            ),
            cast_to=NewsGetRecapsResponse,
        )

    def list_feeds(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> NewsListFeedsResponse:
        """Returns all available news feed topics with descriptions."""
        return self._get(
            "/news/feeds",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NewsListFeedsResponse,
        )


class AsyncNewsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncNewsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/y2-intel/y2-py#accessing-raw-response-data-eg-headers
        """
        return AsyncNewsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncNewsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/y2-intel/y2-py#with_streaming_response
        """
        return AsyncNewsResourceWithStreamingResponse(self)

    async def list(
        self,
        *,
        limit: int | Omit = omit,
        topics: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> NewsListResponse:
        """Returns news items from the GloriaAI terminal cache.

        Supports filtering by
        topics and pagination.

        Args:
          limit: Maximum number of items to return

          topics: Comma-separated list of topics to filter by. Valid topics: ai, ai_agents, aptos,
              base, bitcoin, crypto, dats, defi, ethereum, hyperliquid, machine_learning,
              macro, ondo, perps, ripple, rwa, solana, tech, virtuals. Default: crypto,
              ai_agents, macro, bitcoin, ethereum, tech

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/news",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "limit": limit,
                        "topics": topics,
                    },
                    news_list_params.NewsListParams,
                ),
            ),
            cast_to=NewsListResponse,
        )

    async def get_recaps(
        self,
        *,
        timeframe: TimeframeEnum | Omit = omit,
        topics: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> NewsGetRecapsResponse:
        """
        Returns AI-generated recap summaries for specified topics within a given
        timeframe.

        Args:
          timeframe: Time period for recaps

          topics: Comma-separated list of topics. Valid topics: ai, ai_agents, aptos, base,
              bitcoin, crypto, dats, defi, ethereum, hyperliquid, machine_learning, macro,
              ondo, perps, ripple, rwa, solana, tech, virtuals

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/news/recaps",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "timeframe": timeframe,
                        "topics": topics,
                    },
                    news_get_recaps_params.NewsGetRecapsParams,
                ),
            ),
            cast_to=NewsGetRecapsResponse,
        )

    async def list_feeds(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> NewsListFeedsResponse:
        """Returns all available news feed topics with descriptions."""
        return await self._get(
            "/news/feeds",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NewsListFeedsResponse,
        )


class NewsResourceWithRawResponse:
    def __init__(self, news: NewsResource) -> None:
        self._news = news

        self.list = to_raw_response_wrapper(
            news.list,
        )
        self.get_recaps = to_raw_response_wrapper(
            news.get_recaps,
        )
        self.list_feeds = to_raw_response_wrapper(
            news.list_feeds,
        )


class AsyncNewsResourceWithRawResponse:
    def __init__(self, news: AsyncNewsResource) -> None:
        self._news = news

        self.list = async_to_raw_response_wrapper(
            news.list,
        )
        self.get_recaps = async_to_raw_response_wrapper(
            news.get_recaps,
        )
        self.list_feeds = async_to_raw_response_wrapper(
            news.list_feeds,
        )


class NewsResourceWithStreamingResponse:
    def __init__(self, news: NewsResource) -> None:
        self._news = news

        self.list = to_streamed_response_wrapper(
            news.list,
        )
        self.get_recaps = to_streamed_response_wrapper(
            news.get_recaps,
        )
        self.list_feeds = to_streamed_response_wrapper(
            news.list_feeds,
        )


class AsyncNewsResourceWithStreamingResponse:
    def __init__(self, news: AsyncNewsResource) -> None:
        self._news = news

        self.list = async_to_streamed_response_wrapper(
            news.list,
        )
        self.get_recaps = async_to_streamed_response_wrapper(
            news.get_recaps,
        )
        self.list_feeds = async_to_streamed_response_wrapper(
            news.list_feeds,
        )
