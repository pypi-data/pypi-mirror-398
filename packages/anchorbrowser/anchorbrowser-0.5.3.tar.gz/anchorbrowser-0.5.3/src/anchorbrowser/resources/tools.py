# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict
from typing_extensions import Literal

import httpx

from ..types import tool_fetch_webpage_params, tool_perform_web_task_params, tool_screenshot_webpage_params
from .._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from .._utils import maybe_transform, async_maybe_transform
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    BinaryAPIResponse,
    AsyncBinaryAPIResponse,
    StreamedBinaryAPIResponse,
    AsyncStreamedBinaryAPIResponse,
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    to_custom_raw_response_wrapper,
    async_to_streamed_response_wrapper,
    to_custom_streamed_response_wrapper,
    async_to_custom_raw_response_wrapper,
    async_to_custom_streamed_response_wrapper,
)
from .._base_client import make_request_options
from ..types.tool_perform_web_task_response import ToolPerformWebTaskResponse

__all__ = ["ToolsResource", "AsyncToolsResource"]


class ToolsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> ToolsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/anchorbrowser/AnchorBrowser-SDK-Python#accessing-raw-response-data-eg-headers
        """
        return ToolsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ToolsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/anchorbrowser/AnchorBrowser-SDK-Python#with_streaming_response
        """
        return ToolsResourceWithStreamingResponse(self)

    def fetch_webpage(
        self,
        *,
        session_id: str | Omit = omit,
        format: Literal["html", "markdown"] | Omit = omit,
        new_page: bool | Omit = omit,
        page_index: int | Omit = omit,
        return_partial_on_timeout: bool | Omit = omit,
        url: str | Omit = omit,
        wait: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> str:
        """
        Retrieve the rendered content of a webpage, optionally formatted as Markdown or
        HTML.

        Args:
          session_id: An optional browser session identifier to reference an existing running browser
              session. If provided, the tool will execute within that browser session.

          format: The output format of the content.

          new_page: Whether to create a new page for the content.

          page_index: The index of the page to fetch content from. **Overides new_page**.

          return_partial_on_timeout: Whether to return partial content if the content is not loaded within the 20
              seconds.

          url: The URL of the webpage to fetch content from. When left empty, the current
              webpage is used.

          wait: The time to wait for **dynamic** content to load in **milliseconds**.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "text/plain", **(extra_headers or {})}
        return self._post(
            "/v1/tools/fetch-webpage",
            body=maybe_transform(
                {
                    "format": format,
                    "new_page": new_page,
                    "page_index": page_index,
                    "return_partial_on_timeout": return_partial_on_timeout,
                    "url": url,
                    "wait": wait,
                },
                tool_fetch_webpage_params.ToolFetchWebpageParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform({"session_id": session_id}, tool_fetch_webpage_params.ToolFetchWebpageParams),
            ),
            cast_to=str,
        )

    def perform_web_task(
        self,
        *,
        prompt: str,
        session_id: str | Omit = omit,
        agent: Literal["browser-use", "openai-cua"] | Omit = omit,
        detect_elements: bool | Omit = omit,
        highlight_elements: bool | Omit = omit,
        human_intervention: bool | Omit = omit,
        max_steps: int | Omit = omit,
        model: str | Omit = omit,
        output_schema: object | Omit = omit,
        provider: Literal["openai", "gemini", "groq", "azure", "xai"] | Omit = omit,
        secret_values: Dict[str, str] | Omit = omit,
        url: str | Omit = omit,
        directly_open_url: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ToolPerformWebTaskResponse:
        """
        Start from a URL and perform the given task.

        Args:
          prompt: The task to be autonomously completed.

          session_id: An optional browser session identifier to reference an existing running browser
              sessions. When passed, the tool will be executed on the provided browser
              session.

          agent: The AI agent to use for task completion. Defaults to browser-use.

          detect_elements: Enable element detection for better interaction accuracy. Improves the agent's
              ability to identify and interact with UI elements.

          highlight_elements: Whether to highlight elements during task execution for better visibility.

          human_intervention: Allow human intervention during task execution. When enabled, the agent can
              request human input for ambiguous situations.

          max_steps: Maximum number of steps the agent can take to complete the task. Defaults
              to 200.

          model: The specific model to use for task completion. see our
              [models](/agentic-browser-control/ai-task-completion#available-models) page for
              more information.

          output_schema: JSON Schema defining the expected structure of the output data.

          provider: The AI provider to use for task completion.

          secret_values: Secret values to pass to the agent for secure credential handling. Keys and
              values are passed as environment variables to the agent.

          url: The URL of the webpage. If not provided, the tool will use the current page in
              the session.

          directly_open_url: If true, the tool will directly open the URL in the browser.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/v1/tools/perform-web-task",
            body=maybe_transform(
                {
                    "prompt": prompt,
                    "agent": agent,
                    "detect_elements": detect_elements,
                    "highlight_elements": highlight_elements,
                    "human_intervention": human_intervention,
                    "max_steps": max_steps,
                    "model": model,
                    "output_schema": output_schema,
                    "provider": provider,
                    "secret_values": secret_values,
                    "url": url,
                    "directly_open_url": directly_open_url,
                },
                tool_perform_web_task_params.ToolPerformWebTaskParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {"session_id": session_id}, tool_perform_web_task_params.ToolPerformWebTaskParams
                ),
            ),
            cast_to=ToolPerformWebTaskResponse,
        )

    def screenshot_webpage(
        self,
        *,
        session_id: str | Omit = omit,
        capture_full_height: bool | Omit = omit,
        height: int | Omit = omit,
        image_quality: int | Omit = omit,
        s3_target_address: str | Omit = omit,
        scroll_all_content: bool | Omit = omit,
        url: str | Omit = omit,
        wait: int | Omit = omit,
        width: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BinaryAPIResponse:
        """
        This endpoint captures a screenshot of the specified webpage using Chromium.
        Users can customize the viewport dimensions and capture options.

        Args:
          session_id: An optional browser session identifier to reference an existing running browser
              sessions. When passed, the tool will be executed on the provided browser
              session.

          capture_full_height: If true, captures the entire height of the page, ignoring the viewport height.

          height: The height of the browser viewport in pixels.

          image_quality: Quality of the output image, on the range 1-100. 100 will not perform any
              compression.

          s3_target_address: Presigned S3 url target to upload the image to.

          scroll_all_content: If true, scrolls the page and captures all visible content.

          url: The URL of the webpage to capture.

          wait: Duration in milliseconds to wait after page has loaded, mainly used for sites
              with JS animations.

          width: The width of the browser viewport in pixels.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "image/png", **(extra_headers or {})}
        return self._post(
            "/v1/tools/screenshot",
            body=maybe_transform(
                {
                    "capture_full_height": capture_full_height,
                    "height": height,
                    "image_quality": image_quality,
                    "s3_target_address": s3_target_address,
                    "scroll_all_content": scroll_all_content,
                    "url": url,
                    "wait": wait,
                    "width": width,
                },
                tool_screenshot_webpage_params.ToolScreenshotWebpageParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {"session_id": session_id}, tool_screenshot_webpage_params.ToolScreenshotWebpageParams
                ),
            ),
            cast_to=BinaryAPIResponse,
        )


class AsyncToolsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncToolsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/anchorbrowser/AnchorBrowser-SDK-Python#accessing-raw-response-data-eg-headers
        """
        return AsyncToolsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncToolsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/anchorbrowser/AnchorBrowser-SDK-Python#with_streaming_response
        """
        return AsyncToolsResourceWithStreamingResponse(self)

    async def fetch_webpage(
        self,
        *,
        session_id: str | Omit = omit,
        format: Literal["html", "markdown"] | Omit = omit,
        new_page: bool | Omit = omit,
        page_index: int | Omit = omit,
        return_partial_on_timeout: bool | Omit = omit,
        url: str | Omit = omit,
        wait: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> str:
        """
        Retrieve the rendered content of a webpage, optionally formatted as Markdown or
        HTML.

        Args:
          session_id: An optional browser session identifier to reference an existing running browser
              session. If provided, the tool will execute within that browser session.

          format: The output format of the content.

          new_page: Whether to create a new page for the content.

          page_index: The index of the page to fetch content from. **Overides new_page**.

          return_partial_on_timeout: Whether to return partial content if the content is not loaded within the 20
              seconds.

          url: The URL of the webpage to fetch content from. When left empty, the current
              webpage is used.

          wait: The time to wait for **dynamic** content to load in **milliseconds**.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "text/plain", **(extra_headers or {})}
        return await self._post(
            "/v1/tools/fetch-webpage",
            body=await async_maybe_transform(
                {
                    "format": format,
                    "new_page": new_page,
                    "page_index": page_index,
                    "return_partial_on_timeout": return_partial_on_timeout,
                    "url": url,
                    "wait": wait,
                },
                tool_fetch_webpage_params.ToolFetchWebpageParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {"session_id": session_id}, tool_fetch_webpage_params.ToolFetchWebpageParams
                ),
            ),
            cast_to=str,
        )

    async def perform_web_task(
        self,
        *,
        prompt: str,
        session_id: str | Omit = omit,
        agent: Literal["browser-use", "openai-cua"] | Omit = omit,
        detect_elements: bool | Omit = omit,
        highlight_elements: bool | Omit = omit,
        human_intervention: bool | Omit = omit,
        max_steps: int | Omit = omit,
        model: str | Omit = omit,
        output_schema: object | Omit = omit,
        provider: Literal["openai", "gemini", "groq", "azure", "xai"] | Omit = omit,
        secret_values: Dict[str, str] | Omit = omit,
        url: str | Omit = omit,
        directly_open_url: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ToolPerformWebTaskResponse:
        """
        Start from a URL and perform the given task.

        Args:
          prompt: The task to be autonomously completed.

          session_id: An optional browser session identifier to reference an existing running browser
              sessions. When passed, the tool will be executed on the provided browser
              session.

          agent: The AI agent to use for task completion. Defaults to browser-use.

          detect_elements: Enable element detection for better interaction accuracy. Improves the agent's
              ability to identify and interact with UI elements.

          highlight_elements: Whether to highlight elements during task execution for better visibility.

          human_intervention: Allow human intervention during task execution. When enabled, the agent can
              request human input for ambiguous situations.

          max_steps: Maximum number of steps the agent can take to complete the task. Defaults
              to 200.

          model: The specific model to use for task completion. see our
              [models](/agentic-browser-control/ai-task-completion#available-models) page for
              more information.

          output_schema: JSON Schema defining the expected structure of the output data.

          provider: The AI provider to use for task completion.

          secret_values: Secret values to pass to the agent for secure credential handling. Keys and
              values are passed as environment variables to the agent.

          url: The URL of the webpage. If not provided, the tool will use the current page in
              the session.

          directly_open_url: If true, the tool will directly open the URL in the browser.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/v1/tools/perform-web-task",
            body=await async_maybe_transform(
                {
                    "prompt": prompt,
                    "agent": agent,
                    "detect_elements": detect_elements,
                    "highlight_elements": highlight_elements,
                    "human_intervention": human_intervention,
                    "max_steps": max_steps,
                    "model": model,
                    "output_schema": output_schema,
                    "provider": provider,
                    "secret_values": secret_values,
                    "url": url,
                    "directly_open_url": directly_open_url,
                },
                tool_perform_web_task_params.ToolPerformWebTaskParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {"session_id": session_id}, tool_perform_web_task_params.ToolPerformWebTaskParams
                ),
            ),
            cast_to=ToolPerformWebTaskResponse,
        )

    async def screenshot_webpage(
        self,
        *,
        session_id: str | Omit = omit,
        capture_full_height: bool | Omit = omit,
        height: int | Omit = omit,
        image_quality: int | Omit = omit,
        s3_target_address: str | Omit = omit,
        scroll_all_content: bool | Omit = omit,
        url: str | Omit = omit,
        wait: int | Omit = omit,
        width: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncBinaryAPIResponse:
        """
        This endpoint captures a screenshot of the specified webpage using Chromium.
        Users can customize the viewport dimensions and capture options.

        Args:
          session_id: An optional browser session identifier to reference an existing running browser
              sessions. When passed, the tool will be executed on the provided browser
              session.

          capture_full_height: If true, captures the entire height of the page, ignoring the viewport height.

          height: The height of the browser viewport in pixels.

          image_quality: Quality of the output image, on the range 1-100. 100 will not perform any
              compression.

          s3_target_address: Presigned S3 url target to upload the image to.

          scroll_all_content: If true, scrolls the page and captures all visible content.

          url: The URL of the webpage to capture.

          wait: Duration in milliseconds to wait after page has loaded, mainly used for sites
              with JS animations.

          width: The width of the browser viewport in pixels.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "image/png", **(extra_headers or {})}
        return await self._post(
            "/v1/tools/screenshot",
            body=await async_maybe_transform(
                {
                    "capture_full_height": capture_full_height,
                    "height": height,
                    "image_quality": image_quality,
                    "s3_target_address": s3_target_address,
                    "scroll_all_content": scroll_all_content,
                    "url": url,
                    "wait": wait,
                    "width": width,
                },
                tool_screenshot_webpage_params.ToolScreenshotWebpageParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {"session_id": session_id}, tool_screenshot_webpage_params.ToolScreenshotWebpageParams
                ),
            ),
            cast_to=AsyncBinaryAPIResponse,
        )


class ToolsResourceWithRawResponse:
    def __init__(self, tools: ToolsResource) -> None:
        self._tools = tools

        self.fetch_webpage = to_raw_response_wrapper(
            tools.fetch_webpage,
        )
        self.perform_web_task = to_raw_response_wrapper(
            tools.perform_web_task,
        )
        self.screenshot_webpage = to_custom_raw_response_wrapper(
            tools.screenshot_webpage,
            BinaryAPIResponse,
        )


class AsyncToolsResourceWithRawResponse:
    def __init__(self, tools: AsyncToolsResource) -> None:
        self._tools = tools

        self.fetch_webpage = async_to_raw_response_wrapper(
            tools.fetch_webpage,
        )
        self.perform_web_task = async_to_raw_response_wrapper(
            tools.perform_web_task,
        )
        self.screenshot_webpage = async_to_custom_raw_response_wrapper(
            tools.screenshot_webpage,
            AsyncBinaryAPIResponse,
        )


class ToolsResourceWithStreamingResponse:
    def __init__(self, tools: ToolsResource) -> None:
        self._tools = tools

        self.fetch_webpage = to_streamed_response_wrapper(
            tools.fetch_webpage,
        )
        self.perform_web_task = to_streamed_response_wrapper(
            tools.perform_web_task,
        )
        self.screenshot_webpage = to_custom_streamed_response_wrapper(
            tools.screenshot_webpage,
            StreamedBinaryAPIResponse,
        )


class AsyncToolsResourceWithStreamingResponse:
    def __init__(self, tools: AsyncToolsResource) -> None:
        self._tools = tools

        self.fetch_webpage = async_to_streamed_response_wrapper(
            tools.fetch_webpage,
        )
        self.perform_web_task = async_to_streamed_response_wrapper(
            tools.perform_web_task,
        )
        self.screenshot_webpage = async_to_custom_streamed_response_wrapper(
            tools.screenshot_webpage,
            AsyncStreamedBinaryAPIResponse,
        )
