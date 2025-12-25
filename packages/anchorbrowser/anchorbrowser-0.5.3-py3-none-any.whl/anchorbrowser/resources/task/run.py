# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict

import httpx

from ...types import task_run_params
from ..._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from ..._utils import maybe_transform, async_maybe_transform
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..._base_client import make_request_options
from ...types.task_run_response import RunExecuteResponse

__all__ = ["RunResource", "AsyncRunResource"]


class RunResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> RunResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/anchorbrowser/AnchorBrowser-SDK-Python#accessing-raw-response-data-eg-headers
        """
        return RunResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> RunResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/anchorbrowser/AnchorBrowser-SDK-Python#with_streaming_response
        """
        return RunResourceWithStreamingResponse(self)

    def execute(
        self,
        *,
        task_id: str,
        async_: bool | Omit = omit,
        inputs: Dict[str, str] | Omit = omit,
        override_browser_configuration: task_run_params.OverrideBrowserConfiguration | Omit = omit,
        version: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RunExecuteResponse:
        """Executes a task in a browser session.

        The task can be run with a specific
        version or the latest version. Optionally, you can provide an existing session
        ID or let the system create a new one.

        Args:
          task_id: Task identifier

          async_: Whether to run the task asynchronously.

          inputs: Environment variables for task execution (keys must start with ANCHOR\\__)

          override_browser_configuration: Override browser configuration for this execution

          version: Version to run (draft, latest, or version number)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/v1/task/run",
            body=maybe_transform(
                {
                    "task_id": task_id,
                    "async_": async_,
                    "inputs": inputs,
                    "override_browser_configuration": override_browser_configuration,
                    "version": version,
                },
                task_run_params.RunExecuteParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RunExecuteResponse,
        )


class AsyncRunResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncRunResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/anchorbrowser/AnchorBrowser-SDK-Python#accessing-raw-response-data-eg-headers
        """
        return AsyncRunResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncRunResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/anchorbrowser/AnchorBrowser-SDK-Python#with_streaming_response
        """
        return AsyncRunResourceWithStreamingResponse(self)

    async def execute(
        self,
        *,
        task_id: str,
        async_: bool | Omit = omit,
        inputs: Dict[str, str] | Omit = omit,
        override_browser_configuration: task_run_params.OverrideBrowserConfiguration | Omit = omit,
        version: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RunExecuteResponse:
        """Executes a task in a browser session.

        The task can be run with a specific
        version or the latest version. Optionally, you can provide an existing session
        ID or let the system create a new one.

        Args:
          task_id: Task identifier

          async_: Whether to run the task asynchronously.

          inputs: Environment variables for task execution (keys must start with ANCHOR\\__)

          override_browser_configuration: Override browser configuration for this execution

          version: Version to run (draft, latest, or version number)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/v1/task/run",
            body=await async_maybe_transform(
                {
                    "task_id": task_id,
                    "async_": async_,
                    "inputs": inputs,
                    "override_browser_configuration": override_browser_configuration,
                    "version": version,
                },
                task_run_params.RunExecuteParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RunExecuteResponse,
        )


class RunResourceWithRawResponse:
    def __init__(self, run: RunResource) -> None:
        self._run = run

        self.execute = to_raw_response_wrapper(
            run.execute,
        )


class AsyncRunResourceWithRawResponse:
    def __init__(self, run: AsyncRunResource) -> None:
        self._run = run

        self.execute = async_to_raw_response_wrapper(
            run.execute,
        )


class RunResourceWithStreamingResponse:
    def __init__(self, run: RunResource) -> None:
        self._run = run

        self.execute = to_streamed_response_wrapper(
            run.execute,
        )


class AsyncRunResourceWithStreamingResponse:
    def __init__(self, run: AsyncRunResource) -> None:
        self._run = run

        self.execute = async_to_streamed_response_wrapper(
            run.execute,
        )
