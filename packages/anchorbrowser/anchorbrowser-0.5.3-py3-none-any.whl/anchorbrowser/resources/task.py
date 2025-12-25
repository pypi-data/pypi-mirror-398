# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict
from typing_extensions import Literal

import httpx

from ..types import task_run_params, task_list_params, task_create_params
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
from ..types.task_run_response import RunExecuteResponse
from ..types.task_list_response import TaskListResponse
from ..types.task_create_response import TaskCreateResponse

__all__ = ["TaskResource", "AsyncTaskResource"]


class TaskResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> TaskResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/anchorbrowser/AnchorBrowser-SDK-Python#accessing-raw-response-data-eg-headers
        """
        return TaskResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> TaskResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/anchorbrowser/AnchorBrowser-SDK-Python#with_streaming_response
        """
        return TaskResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        language: Literal["typescript"],
        name: str,
        browser_configuration: task_create_params.BrowserConfiguration | Omit = omit,
        code: str | Omit = omit,
        description: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> TaskCreateResponse:
        """Creates a new task or updates an existing task with the same name.

        Tasks are
        reusable code snippets that can be executed in browser sessions. Tasks support
        versioning with draft and published versions.

        Args:
          language: Programming language for the task

          name: Task name (letters, numbers, hyphens, and underscores only)

          browser_configuration: Browser configuration for task execution

          code: Base64 encoded task code (optional)

          description: Optional description of the task

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/v1/task",
            body=maybe_transform(
                {
                    "language": language,
                    "name": name,
                    "browser_configuration": browser_configuration,
                    "code": code,
                    "description": description,
                },
                task_create_params.TaskCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TaskCreateResponse,
        )

    def list(
        self,
        *,
        limit: str | Omit = omit,
        page: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> TaskListResponse:
        """Retrieves a paginated list of all tasks for the authenticated team.

        Tasks are
        returned with their latest version information and metadata.

        Args:
          limit: Number of tasks per page

          page: Page number

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/v1/task",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "limit": limit,
                        "page": page,
                    },
                    task_list_params.TaskListParams,
                ),
            ),
            cast_to=TaskListResponse,
        )

    def run(
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


class AsyncTaskResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncTaskResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/anchorbrowser/AnchorBrowser-SDK-Python#accessing-raw-response-data-eg-headers
        """
        return AsyncTaskResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncTaskResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/anchorbrowser/AnchorBrowser-SDK-Python#with_streaming_response
        """
        return AsyncTaskResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        language: Literal["typescript"],
        name: str,
        browser_configuration: task_create_params.BrowserConfiguration | Omit = omit,
        code: str | Omit = omit,
        description: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> TaskCreateResponse:
        """Creates a new task or updates an existing task with the same name.

        Tasks are
        reusable code snippets that can be executed in browser sessions. Tasks support
        versioning with draft and published versions.

        Args:
          language: Programming language for the task

          name: Task name (letters, numbers, hyphens, and underscores only)

          browser_configuration: Browser configuration for task execution

          code: Base64 encoded task code (optional)

          description: Optional description of the task

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/v1/task",
            body=await async_maybe_transform(
                {
                    "language": language,
                    "name": name,
                    "browser_configuration": browser_configuration,
                    "code": code,
                    "description": description,
                },
                task_create_params.TaskCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TaskCreateResponse,
        )

    async def list(
        self,
        *,
        limit: str | Omit = omit,
        page: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> TaskListResponse:
        """Retrieves a paginated list of all tasks for the authenticated team.

        Tasks are
        returned with their latest version information and metadata.

        Args:
          limit: Number of tasks per page

          page: Page number

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/v1/task",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "limit": limit,
                        "page": page,
                    },
                    task_list_params.TaskListParams,
                ),
            ),
            cast_to=TaskListResponse,
        )

    async def run(
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
                    "async": async_,
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


class TaskResourceWithRawResponse:
    def __init__(self, task: TaskResource) -> None:
        self._task = task

        self.create = to_raw_response_wrapper(
            task.create,
        )
        self.list = to_raw_response_wrapper(
            task.list,
        )
        self.run = to_raw_response_wrapper(
            task.run,
        )


class AsyncTaskResourceWithRawResponse:
    def __init__(self, task: AsyncTaskResource) -> None:
        self._task = task

        self.create = async_to_raw_response_wrapper(
            task.create,
        )
        self.list = async_to_raw_response_wrapper(
            task.list,
        )
        self.run = async_to_raw_response_wrapper(
            task.run,
        )


class TaskResourceWithStreamingResponse:
    def __init__(self, task: TaskResource) -> None:
        self._task = task

        self.create = to_streamed_response_wrapper(
            task.create,
        )
        self.list = to_streamed_response_wrapper(
            task.list,
        )
        self.run = to_streamed_response_wrapper(
            task.run,
        )


class AsyncTaskResourceWithStreamingResponse:
    def __init__(self, task: AsyncTaskResource) -> None:
        self._task = task

        self.create = async_to_streamed_response_wrapper(
            task.create,
        )
        self.list = async_to_streamed_response_wrapper(
            task.list,
        )
        self.run = async_to_streamed_response_wrapper(
            task.run,
        )
