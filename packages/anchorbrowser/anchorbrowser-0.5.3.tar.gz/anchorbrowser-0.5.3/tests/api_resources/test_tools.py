# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import httpx
import pytest
from respx import MockRouter

from tests.utils import assert_matches_type
from anchorbrowser import Anchorbrowser, AsyncAnchorbrowser
from anchorbrowser.types import (
    ToolPerformWebTaskResponse,
)
from anchorbrowser._response import (
    BinaryAPIResponse,
    AsyncBinaryAPIResponse,
    StreamedBinaryAPIResponse,
    AsyncStreamedBinaryAPIResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestTools:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_fetch_webpage(self, client: Anchorbrowser) -> None:
        tool = client.tools.fetch_webpage()
        assert_matches_type(str, tool, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_fetch_webpage_with_all_params(self, client: Anchorbrowser) -> None:
        tool = client.tools.fetch_webpage(
            session_id="sessionId",
            format="html",
            new_page=True,
            page_index=0,
            return_partial_on_timeout=True,
            url="url",
            wait=0,
        )
        assert_matches_type(str, tool, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_fetch_webpage(self, client: Anchorbrowser) -> None:
        response = client.tools.with_raw_response.fetch_webpage()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        tool = response.parse()
        assert_matches_type(str, tool, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_fetch_webpage(self, client: Anchorbrowser) -> None:
        with client.tools.with_streaming_response.fetch_webpage() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            tool = response.parse()
            assert_matches_type(str, tool, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_perform_web_task(self, client: Anchorbrowser) -> None:
        tool = client.tools.perform_web_task(
            prompt="prompt",
        )
        assert_matches_type(ToolPerformWebTaskResponse, tool, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_perform_web_task_with_all_params(self, client: Anchorbrowser) -> None:
        tool = client.tools.perform_web_task(
            prompt="prompt",
            session_id="sessionId",
            agent="browser-use",
            detect_elements=True,
            highlight_elements=True,
            human_intervention=True,
            max_steps=0,
            model="model",
            output_schema={},
            provider="openai",
            secret_values={"foo": "string"},
            url="url",
        )
        assert_matches_type(ToolPerformWebTaskResponse, tool, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_perform_web_task(self, client: Anchorbrowser) -> None:
        response = client.tools.with_raw_response.perform_web_task(
            prompt="prompt",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        tool = response.parse()
        assert_matches_type(ToolPerformWebTaskResponse, tool, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_perform_web_task(self, client: Anchorbrowser) -> None:
        with client.tools.with_streaming_response.perform_web_task(
            prompt="prompt",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            tool = response.parse()
            assert_matches_type(ToolPerformWebTaskResponse, tool, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    def test_method_screenshot_webpage(self, client: Anchorbrowser, respx_mock: MockRouter) -> None:
        respx_mock.post("/v1/tools/screenshot").mock(return_value=httpx.Response(200, json={"foo": "bar"}))
        tool = client.tools.screenshot_webpage()
        assert tool.is_closed
        assert tool.json() == {"foo": "bar"}
        assert cast(Any, tool.is_closed) is True
        assert isinstance(tool, BinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    def test_method_screenshot_webpage_with_all_params(self, client: Anchorbrowser, respx_mock: MockRouter) -> None:
        respx_mock.post("/v1/tools/screenshot").mock(return_value=httpx.Response(200, json={"foo": "bar"}))
        tool = client.tools.screenshot_webpage(
            session_id="sessionId",
            capture_full_height=True,
            height=0,
            image_quality=0,
            s3_target_address="s3_target_address",
            scroll_all_content=True,
            url="url",
            wait=0,
            width=0,
        )
        assert tool.is_closed
        assert tool.json() == {"foo": "bar"}
        assert cast(Any, tool.is_closed) is True
        assert isinstance(tool, BinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    def test_raw_response_screenshot_webpage(self, client: Anchorbrowser, respx_mock: MockRouter) -> None:
        respx_mock.post("/v1/tools/screenshot").mock(return_value=httpx.Response(200, json={"foo": "bar"}))

        tool = client.tools.with_raw_response.screenshot_webpage()

        assert tool.is_closed is True
        assert tool.http_request.headers.get("X-Stainless-Lang") == "python"
        assert tool.json() == {"foo": "bar"}
        assert isinstance(tool, BinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    def test_streaming_response_screenshot_webpage(self, client: Anchorbrowser, respx_mock: MockRouter) -> None:
        respx_mock.post("/v1/tools/screenshot").mock(return_value=httpx.Response(200, json={"foo": "bar"}))
        with client.tools.with_streaming_response.screenshot_webpage() as tool:
            assert not tool.is_closed
            assert tool.http_request.headers.get("X-Stainless-Lang") == "python"

            assert tool.json() == {"foo": "bar"}
            assert cast(Any, tool.is_closed) is True
            assert isinstance(tool, StreamedBinaryAPIResponse)

        assert cast(Any, tool.is_closed) is True


class TestAsyncTools:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_fetch_webpage(self, async_client: AsyncAnchorbrowser) -> None:
        tool = await async_client.tools.fetch_webpage()
        assert_matches_type(str, tool, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_fetch_webpage_with_all_params(self, async_client: AsyncAnchorbrowser) -> None:
        tool = await async_client.tools.fetch_webpage(
            session_id="sessionId",
            format="html",
            new_page=True,
            page_index=0,
            return_partial_on_timeout=True,
            url="url",
            wait=0,
        )
        assert_matches_type(str, tool, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_fetch_webpage(self, async_client: AsyncAnchorbrowser) -> None:
        response = await async_client.tools.with_raw_response.fetch_webpage()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        tool = await response.parse()
        assert_matches_type(str, tool, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_fetch_webpage(self, async_client: AsyncAnchorbrowser) -> None:
        async with async_client.tools.with_streaming_response.fetch_webpage() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            tool = await response.parse()
            assert_matches_type(str, tool, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_perform_web_task(self, async_client: AsyncAnchorbrowser) -> None:
        tool = await async_client.tools.perform_web_task(
            prompt="prompt",
        )
        assert_matches_type(ToolPerformWebTaskResponse, tool, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_perform_web_task_with_all_params(self, async_client: AsyncAnchorbrowser) -> None:
        tool = await async_client.tools.perform_web_task(
            prompt="prompt",
            session_id="sessionId",
            agent="browser-use",
            detect_elements=True,
            highlight_elements=True,
            human_intervention=True,
            max_steps=0,
            model="model",
            output_schema={},
            provider="openai",
            secret_values={"foo": "string"},
            url="url",
        )
        assert_matches_type(ToolPerformWebTaskResponse, tool, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_perform_web_task(self, async_client: AsyncAnchorbrowser) -> None:
        response = await async_client.tools.with_raw_response.perform_web_task(
            prompt="prompt",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        tool = await response.parse()
        assert_matches_type(ToolPerformWebTaskResponse, tool, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_perform_web_task(self, async_client: AsyncAnchorbrowser) -> None:
        async with async_client.tools.with_streaming_response.perform_web_task(
            prompt="prompt",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            tool = await response.parse()
            assert_matches_type(ToolPerformWebTaskResponse, tool, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    async def test_method_screenshot_webpage(self, async_client: AsyncAnchorbrowser, respx_mock: MockRouter) -> None:
        respx_mock.post("/v1/tools/screenshot").mock(return_value=httpx.Response(200, json={"foo": "bar"}))
        tool = await async_client.tools.screenshot_webpage()
        assert tool.is_closed
        assert await tool.json() == {"foo": "bar"}
        assert cast(Any, tool.is_closed) is True
        assert isinstance(tool, AsyncBinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    async def test_method_screenshot_webpage_with_all_params(
        self, async_client: AsyncAnchorbrowser, respx_mock: MockRouter
    ) -> None:
        respx_mock.post("/v1/tools/screenshot").mock(return_value=httpx.Response(200, json={"foo": "bar"}))
        tool = await async_client.tools.screenshot_webpage(
            session_id="sessionId",
            capture_full_height=True,
            height=0,
            image_quality=0,
            s3_target_address="s3_target_address",
            scroll_all_content=True,
            url="url",
            wait=0,
            width=0,
        )
        assert tool.is_closed
        assert await tool.json() == {"foo": "bar"}
        assert cast(Any, tool.is_closed) is True
        assert isinstance(tool, AsyncBinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    async def test_raw_response_screenshot_webpage(
        self, async_client: AsyncAnchorbrowser, respx_mock: MockRouter
    ) -> None:
        respx_mock.post("/v1/tools/screenshot").mock(return_value=httpx.Response(200, json={"foo": "bar"}))

        tool = await async_client.tools.with_raw_response.screenshot_webpage()

        assert tool.is_closed is True
        assert tool.http_request.headers.get("X-Stainless-Lang") == "python"
        assert await tool.json() == {"foo": "bar"}
        assert isinstance(tool, AsyncBinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    async def test_streaming_response_screenshot_webpage(
        self, async_client: AsyncAnchorbrowser, respx_mock: MockRouter
    ) -> None:
        respx_mock.post("/v1/tools/screenshot").mock(return_value=httpx.Response(200, json={"foo": "bar"}))
        async with async_client.tools.with_streaming_response.screenshot_webpage() as tool:
            assert not tool.is_closed
            assert tool.http_request.headers.get("X-Stainless-Lang") == "python"

            assert await tool.json() == {"foo": "bar"}
            assert cast(Any, tool.is_closed) is True
            assert isinstance(tool, AsyncStreamedBinaryAPIResponse)

        assert cast(Any, tool.is_closed) is True
