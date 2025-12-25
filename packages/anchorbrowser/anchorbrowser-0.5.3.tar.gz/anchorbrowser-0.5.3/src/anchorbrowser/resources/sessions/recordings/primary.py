# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ...._types import Body, Query, Headers, NotGiven, not_given
from ...._compat import cached_property
from ...._resource import SyncAPIResource, AsyncAPIResource
from ...._response import (
    BinaryAPIResponse,
    AsyncBinaryAPIResponse,
    StreamedBinaryAPIResponse,
    AsyncStreamedBinaryAPIResponse,
    to_custom_raw_response_wrapper,
    to_custom_streamed_response_wrapper,
    async_to_custom_raw_response_wrapper,
    async_to_custom_streamed_response_wrapper,
)
from ...._base_client import make_request_options

__all__ = ["PrimaryResource", "AsyncPrimaryResource"]


class PrimaryResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> PrimaryResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/anchorbrowser/AnchorBrowser-SDK-Python#accessing-raw-response-data-eg-headers
        """
        return PrimaryResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> PrimaryResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/anchorbrowser/AnchorBrowser-SDK-Python#with_streaming_response
        """
        return PrimaryResourceWithStreamingResponse(self)

    def get(
        self,
        session_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BinaryAPIResponse:
        """Downloads the primary recording file for the specified browser session.

        Returns
        the recording as an MP4 file.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        extra_headers = {"Accept": "video/mp4", **(extra_headers or {})}
        return self._get(
            f"/v1/sessions/{session_id}/recordings/primary/fetch",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=BinaryAPIResponse,
        )


class AsyncPrimaryResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncPrimaryResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/anchorbrowser/AnchorBrowser-SDK-Python#accessing-raw-response-data-eg-headers
        """
        return AsyncPrimaryResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncPrimaryResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/anchorbrowser/AnchorBrowser-SDK-Python#with_streaming_response
        """
        return AsyncPrimaryResourceWithStreamingResponse(self)

    async def get(
        self,
        session_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncBinaryAPIResponse:
        """Downloads the primary recording file for the specified browser session.

        Returns
        the recording as an MP4 file.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        extra_headers = {"Accept": "video/mp4", **(extra_headers or {})}
        return await self._get(
            f"/v1/sessions/{session_id}/recordings/primary/fetch",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AsyncBinaryAPIResponse,
        )


class PrimaryResourceWithRawResponse:
    def __init__(self, primary: PrimaryResource) -> None:
        self._primary = primary

        self.get = to_custom_raw_response_wrapper(
            primary.get,
            BinaryAPIResponse,
        )


class AsyncPrimaryResourceWithRawResponse:
    def __init__(self, primary: AsyncPrimaryResource) -> None:
        self._primary = primary

        self.get = async_to_custom_raw_response_wrapper(
            primary.get,
            AsyncBinaryAPIResponse,
        )


class PrimaryResourceWithStreamingResponse:
    def __init__(self, primary: PrimaryResource) -> None:
        self._primary = primary

        self.get = to_custom_streamed_response_wrapper(
            primary.get,
            StreamedBinaryAPIResponse,
        )


class AsyncPrimaryResourceWithStreamingResponse:
    def __init__(self, primary: AsyncPrimaryResource) -> None:
        self._primary = primary

        self.get = async_to_custom_streamed_response_wrapper(
            primary.get,
            AsyncStreamedBinaryAPIResponse,
        )
