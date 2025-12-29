# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ..types import report_list_params, report_retrieve_audio_params
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
from ..types.report_list_response import ReportListResponse
from ..types.report_retrieve_response import ReportRetrieveResponse
from ..types.report_retrieve_audio_response import ReportRetrieveAudioResponse

__all__ = ["ReportsResource", "AsyncReportsResource"]


class ReportsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> ReportsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/y2-intel/y2-py#accessing-raw-response-data-eg-headers
        """
        return ReportsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ReportsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/y2-intel/y2-py#with_streaming_response
        """
        return ReportsResourceWithStreamingResponse(self)

    def retrieve(
        self,
        report_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ReportRetrieveResponse:
        """
        Returns the full content of a specific intelligence report, including HTML
        content, sources, and audio metadata.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not report_id:
            raise ValueError(f"Expected a non-empty value for `report_id` but received {report_id!r}")
        return self._get(
            f"/reports/{report_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ReportRetrieveResponse,
        )

    def list(
        self,
        *,
        limit: int | Omit = omit,
        profile_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ReportListResponse:
        """Returns a list of reports for the user's subscribed profiles.

        Results are sorted
        by generation date (newest first).

        Args:
          limit: Maximum number of reports to return

          profile_id: Filter reports by profile ID

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/reports",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "limit": limit,
                        "profile_id": profile_id,
                    },
                    report_list_params.ReportListParams,
                ),
            ),
            cast_to=ReportListResponse,
        )

    def retrieve_audio(
        self,
        report_id: str,
        *,
        redirect: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ReportRetrieveAudioResponse:
        """Returns audio file metadata or redirects to the CDN URL.

        Requires the
        `reports:audio` scope.

        Args:
          redirect: If true, returns 302 redirect to audio CDN URL

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not report_id:
            raise ValueError(f"Expected a non-empty value for `report_id` but received {report_id!r}")
        return self._get(
            f"/reports/{report_id}/audio",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform({"redirect": redirect}, report_retrieve_audio_params.ReportRetrieveAudioParams),
            ),
            cast_to=ReportRetrieveAudioResponse,
        )


class AsyncReportsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncReportsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/y2-intel/y2-py#accessing-raw-response-data-eg-headers
        """
        return AsyncReportsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncReportsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/y2-intel/y2-py#with_streaming_response
        """
        return AsyncReportsResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        report_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ReportRetrieveResponse:
        """
        Returns the full content of a specific intelligence report, including HTML
        content, sources, and audio metadata.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not report_id:
            raise ValueError(f"Expected a non-empty value for `report_id` but received {report_id!r}")
        return await self._get(
            f"/reports/{report_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ReportRetrieveResponse,
        )

    async def list(
        self,
        *,
        limit: int | Omit = omit,
        profile_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ReportListResponse:
        """Returns a list of reports for the user's subscribed profiles.

        Results are sorted
        by generation date (newest first).

        Args:
          limit: Maximum number of reports to return

          profile_id: Filter reports by profile ID

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/reports",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "limit": limit,
                        "profile_id": profile_id,
                    },
                    report_list_params.ReportListParams,
                ),
            ),
            cast_to=ReportListResponse,
        )

    async def retrieve_audio(
        self,
        report_id: str,
        *,
        redirect: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ReportRetrieveAudioResponse:
        """Returns audio file metadata or redirects to the CDN URL.

        Requires the
        `reports:audio` scope.

        Args:
          redirect: If true, returns 302 redirect to audio CDN URL

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not report_id:
            raise ValueError(f"Expected a non-empty value for `report_id` but received {report_id!r}")
        return await self._get(
            f"/reports/{report_id}/audio",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {"redirect": redirect}, report_retrieve_audio_params.ReportRetrieveAudioParams
                ),
            ),
            cast_to=ReportRetrieveAudioResponse,
        )


class ReportsResourceWithRawResponse:
    def __init__(self, reports: ReportsResource) -> None:
        self._reports = reports

        self.retrieve = to_raw_response_wrapper(
            reports.retrieve,
        )
        self.list = to_raw_response_wrapper(
            reports.list,
        )
        self.retrieve_audio = to_raw_response_wrapper(
            reports.retrieve_audio,
        )


class AsyncReportsResourceWithRawResponse:
    def __init__(self, reports: AsyncReportsResource) -> None:
        self._reports = reports

        self.retrieve = async_to_raw_response_wrapper(
            reports.retrieve,
        )
        self.list = async_to_raw_response_wrapper(
            reports.list,
        )
        self.retrieve_audio = async_to_raw_response_wrapper(
            reports.retrieve_audio,
        )


class ReportsResourceWithStreamingResponse:
    def __init__(self, reports: ReportsResource) -> None:
        self._reports = reports

        self.retrieve = to_streamed_response_wrapper(
            reports.retrieve,
        )
        self.list = to_streamed_response_wrapper(
            reports.list,
        )
        self.retrieve_audio = to_streamed_response_wrapper(
            reports.retrieve_audio,
        )


class AsyncReportsResourceWithStreamingResponse:
    def __init__(self, reports: AsyncReportsResource) -> None:
        self._reports = reports

        self.retrieve = async_to_streamed_response_wrapper(
            reports.retrieve,
        )
        self.list = async_to_streamed_response_wrapper(
            reports.list,
        )
        self.retrieve_audio = async_to_streamed_response_wrapper(
            reports.retrieve_audio,
        )
