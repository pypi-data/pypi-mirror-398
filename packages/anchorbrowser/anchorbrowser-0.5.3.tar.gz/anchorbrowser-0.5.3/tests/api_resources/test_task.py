# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from anchorbrowser import Anchorbrowser, AsyncAnchorbrowser
from anchorbrowser.types import TaskListResponse, TaskCreateResponse
from anchorbrowser.types.task_run_response import RunExecuteResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestTask:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: Anchorbrowser) -> None:
        task = client.task.create(
            language="typescript",
            name="web-scraper",
        )
        assert_matches_type(TaskCreateResponse, task, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_with_all_params(self, client: Anchorbrowser) -> None:
        task = client.task.create(
            language="typescript",
            name="web-scraper",
            browser_configuration={
                "initial_url": "https://example.com",
                "live_view": {"read_only": True},
                "proxy": {
                    "active": True,
                    "city": "city",
                    "country_code": "af",
                    "region": "region",
                    "type": "anchor_proxy",
                },
                "recording": {"active": True},
                "timeout": {
                    "idle_timeout": 0,
                    "max_duration": 0,
                },
            },
            code="Y29uc3QgYW5jaG9yID0gcmVxdWlyZSgnYW5jaG9yYnJvd3NlcicpOwoKYXN5bmMgZnVuY3Rpb24gcnVuKCkgewogIGNvbnN0IHNlc3Npb24gPSBhd2FpdCBhbmNob3IuY3JlYXRlU2Vzc2lvbigpOwogIGF3YWl0IHNlc3Npb24uZ29UbygnaHR0cHM6Ly9leGFtcGxlLmNvbScpOwogIGNvbnN0IHRpdGxlID0gYXdhaXQgc2Vzc2lvbi5nZXRUaXRsZSgpOwogIGNvbnNvbGUubG9nKHRpdGxlKTsKICBhd2FpdCBzZXNzaW9uLmNsb3NlKCk7Cn0KcnVuKCk7",
            description="A task to scrape product information from e-commerce sites",
        )
        assert_matches_type(TaskCreateResponse, task, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: Anchorbrowser) -> None:
        response = client.task.with_raw_response.create(
            language="typescript",
            name="web-scraper",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        task = response.parse()
        assert_matches_type(TaskCreateResponse, task, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: Anchorbrowser) -> None:
        with client.task.with_streaming_response.create(
            language="typescript",
            name="web-scraper",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            task = response.parse()
            assert_matches_type(TaskCreateResponse, task, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Anchorbrowser) -> None:
        task = client.task.list()
        assert_matches_type(TaskListResponse, task, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: Anchorbrowser) -> None:
        task = client.task.list(
            limit="469",
            page="469",
        )
        assert_matches_type(TaskListResponse, task, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Anchorbrowser) -> None:
        response = client.task.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        task = response.parse()
        assert_matches_type(TaskListResponse, task, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Anchorbrowser) -> None:
        with client.task.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            task = response.parse()
            assert_matches_type(TaskListResponse, task, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_run(self, client: Anchorbrowser) -> None:
        run = client.task.run(
            task_id="550e8400-e29b-41d4-a716-446655440000",
        )
        assert_matches_type(RunExecuteResponse, run, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_run_with_all_params(self, client: Anchorbrowser) -> None:
        run = client.task.run(
            task_id="550e8400-e29b-41d4-a716-446655440000",
            inputs={
                "ANCHOR_TARGET_URL": "https://example.com",
                "ANCHOR_MAX_PAGES": "10",
            },
            override_browser_configuration={
                "initial_url": "https://example.com",
                "live_view": {"read_only": True},
                "proxy": {
                    "active": True,
                    "city": "city",
                    "country_code": "af",
                    "region": "region",
                    "type": "anchor_proxy",
                },
                "recording": {"active": True},
                "timeout": {
                    "idle_timeout": 0,
                    "max_duration": 0,
                },
            },
            version="1",
        )
        assert_matches_type(RunExecuteResponse, run, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_run(self, client: Anchorbrowser) -> None:
        response = client.task.with_raw_response.run(
            task_id="550e8400-e29b-41d4-a716-446655440000",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        run = response.parse()
        assert_matches_type(RunExecuteResponse, run, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_run_async_with_all_params(self, client: Anchorbrowser) -> None:
        run = client.task.run(
            task_id="550e8400-e29b-41d4-a716-446655440000",
            async_=True,
            inputs={
                "ANCHOR_TARGET_URL": "https://example.com",
                "ANCHOR_MAX_PAGES": "10",
            },
            override_browser_configuration={
                "initial_url": "https://example.com",
                "live_view": {"read_only": True},
                "proxy": {
                    "active": True,
                    "city": "city",
                    "country_code": "af",
                    "region": "region",
                    "type": "anchor_proxy",
                },
                "recording": {"active": True},
                "timeout": {
                    "idle_timeout": 0,
                    "max_duration": 0,
                },
            },
            version="1",
        )
        assert_matches_type(RunExecuteResponse, run, path=["response"])
   
   
    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_run_async(self, client: Anchorbrowser) -> None:
        response = client.task.with_raw_response.run(
            task_id="550e8400-e29b-41d4-a716-446655440000",
            async_=True,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        run = response.parse()
        assert_matches_type(RunExecuteResponse, run, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_run(self, client: Anchorbrowser) -> None:
        with client.task.with_streaming_response.run(
            task_id="550e8400-e29b-41d4-a716-446655440000",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            run = response.parse()
            assert_matches_type(RunExecuteResponse, run, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncTask:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncAnchorbrowser) -> None:
        task = await async_client.task.create(
            language="typescript",
            name="web-scraper",
        )
        assert_matches_type(TaskCreateResponse, task, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncAnchorbrowser) -> None:
        task = await async_client.task.create(
            language="typescript",
            name="web-scraper",
            browser_configuration={
                "initial_url": "https://example.com",
                "live_view": {"read_only": True},
                "proxy": {
                    "active": True,
                    "city": "city",
                    "country_code": "af",
                    "region": "region",
                    "type": "anchor_proxy",
                },
                "recording": {"active": True},
                "timeout": {
                    "idle_timeout": 0,
                    "max_duration": 0,
                },
            },
            code="Y29uc3QgYW5jaG9yID0gcmVxdWlyZSgnYW5jaG9yYnJvd3NlcicpOwoKYXN5bmMgZnVuY3Rpb24gcnVuKCkgewogIGNvbnN0IHNlc3Npb24gPSBhd2FpdCBhbmNob3IuY3JlYXRlU2Vzc2lvbigpOwogIGF3YWl0IHNlc3Npb24uZ29UbygnaHR0cHM6Ly9leGFtcGxlLmNvbScpOwogIGNvbnN0IHRpdGxlID0gYXdhaXQgc2Vzc2lvbi5nZXRUaXRsZSgpOwogIGNvbnNvbGUubG9nKHRpdGxlKTsKICBhd2FpdCBzZXNzaW9uLmNsb3NlKCk7Cn0KcnVuKCk7",
            description="A task to scrape product information from e-commerce sites",
        )
        assert_matches_type(TaskCreateResponse, task, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncAnchorbrowser) -> None:
        response = await async_client.task.with_raw_response.create(
            language="typescript",
            name="web-scraper",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        task = await response.parse()
        assert_matches_type(TaskCreateResponse, task, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncAnchorbrowser) -> None:
        async with async_client.task.with_streaming_response.create(
            language="typescript",
            name="web-scraper",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            task = await response.parse()
            assert_matches_type(TaskCreateResponse, task, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncAnchorbrowser) -> None:
        task = await async_client.task.list()
        assert_matches_type(TaskListResponse, task, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncAnchorbrowser) -> None:
        task = await async_client.task.list(
            limit="469",
            page="469",
        )
        assert_matches_type(TaskListResponse, task, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncAnchorbrowser) -> None:
        response = await async_client.task.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        task = await response.parse()
        assert_matches_type(TaskListResponse, task, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncAnchorbrowser) -> None:
        async with async_client.task.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            task = await response.parse()
            assert_matches_type(TaskListResponse, task, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_run(self, async_client: AsyncAnchorbrowser) -> None:
        run = await async_client.task.run(
            task_id="550e8400-e29b-41d4-a716-446655440000",
        )
        assert_matches_type(RunExecuteResponse, run, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_run_with_all_params(self, async_client: AsyncAnchorbrowser) -> None:
        run = await async_client.task.run(
            task_id="550e8400-e29b-41d4-a716-446655440000",
            inputs={
                "ANCHOR_TARGET_URL": "https://example.com",
                "ANCHOR_MAX_PAGES": "10",
            },
            override_browser_configuration={
                "initial_url": "https://example.com",
                "live_view": {"read_only": True},
                "proxy": {
                    "active": True,
                    "city": "city",
                    "country_code": "af",
                    "region": "region",
                    "type": "anchor_proxy",
                },
                "recording": {"active": True},
                "timeout": {
                    "idle_timeout": 0,
                    "max_duration": 0,
                },
            },
            version="1",
        )
        assert_matches_type(RunExecuteResponse, run, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_run(self, async_client: AsyncAnchorbrowser) -> None:
        response = await async_client.task.with_raw_response.run(
            task_id="550e8400-e29b-41d4-a716-446655440000",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        run = await response.parse()
        assert_matches_type(RunExecuteResponse, run, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_run(self, async_client: AsyncAnchorbrowser) -> None:
        async with async_client.task.with_streaming_response.run(
            task_id="550e8400-e29b-41d4-a716-446655440000",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            run = await response.parse()
            assert_matches_type(RunExecuteResponse, run, path=["response"])

        assert cast(Any, response.is_closed) is True
