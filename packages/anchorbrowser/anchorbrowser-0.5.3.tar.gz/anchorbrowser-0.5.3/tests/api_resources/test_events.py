# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from anchorbrowser import Anchorbrowser, AsyncAnchorbrowser
from anchorbrowser.types import EventWaitForResponse
from anchorbrowser.types.shared import SuccessResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestEvents:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_signal(self, client: Anchorbrowser) -> None:
        event = client.events.signal(
            event_name="event_name",
            data={
                "message": "bar",
                "result": "bar",
                "timestamp": "bar",
            },
        )
        assert_matches_type(SuccessResponse, event, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_signal(self, client: Anchorbrowser) -> None:
        response = client.events.with_raw_response.signal(
            event_name="event_name",
            data={
                "message": "bar",
                "result": "bar",
                "timestamp": "bar",
            },
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        event = response.parse()
        assert_matches_type(SuccessResponse, event, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_signal(self, client: Anchorbrowser) -> None:
        with client.events.with_streaming_response.signal(
            event_name="event_name",
            data={
                "message": "bar",
                "result": "bar",
                "timestamp": "bar",
            },
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            event = response.parse()
            assert_matches_type(SuccessResponse, event, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_signal(self, client: Anchorbrowser) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `event_name` but received ''"):
            client.events.with_raw_response.signal(
                event_name="",
                data={
                    "message": "bar",
                    "result": "bar",
                    "timestamp": "bar",
                },
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_wait_for(self, client: Anchorbrowser) -> None:
        event = client.events.wait_for(
            event_name="event_name",
        )
        assert_matches_type(EventWaitForResponse, event, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_wait_for_with_all_params(self, client: Anchorbrowser) -> None:
        event = client.events.wait_for(
            event_name="event_name",
            timeout_ms=0,
        )
        assert_matches_type(EventWaitForResponse, event, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_wait_for(self, client: Anchorbrowser) -> None:
        response = client.events.with_raw_response.wait_for(
            event_name="event_name",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        event = response.parse()
        assert_matches_type(EventWaitForResponse, event, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_wait_for(self, client: Anchorbrowser) -> None:
        with client.events.with_streaming_response.wait_for(
            event_name="event_name",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            event = response.parse()
            assert_matches_type(EventWaitForResponse, event, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_wait_for(self, client: Anchorbrowser) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `event_name` but received ''"):
            client.events.with_raw_response.wait_for(
                event_name="",
            )


class TestAsyncEvents:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_signal(self, async_client: AsyncAnchorbrowser) -> None:
        event = await async_client.events.signal(
            event_name="event_name",
            data={
                "message": "bar",
                "result": "bar",
                "timestamp": "bar",
            },
        )
        assert_matches_type(SuccessResponse, event, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_signal(self, async_client: AsyncAnchorbrowser) -> None:
        response = await async_client.events.with_raw_response.signal(
            event_name="event_name",
            data={
                "message": "bar",
                "result": "bar",
                "timestamp": "bar",
            },
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        event = await response.parse()
        assert_matches_type(SuccessResponse, event, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_signal(self, async_client: AsyncAnchorbrowser) -> None:
        async with async_client.events.with_streaming_response.signal(
            event_name="event_name",
            data={
                "message": "bar",
                "result": "bar",
                "timestamp": "bar",
            },
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            event = await response.parse()
            assert_matches_type(SuccessResponse, event, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_signal(self, async_client: AsyncAnchorbrowser) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `event_name` but received ''"):
            await async_client.events.with_raw_response.signal(
                event_name="",
                data={
                    "message": "bar",
                    "result": "bar",
                    "timestamp": "bar",
                },
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_wait_for(self, async_client: AsyncAnchorbrowser) -> None:
        event = await async_client.events.wait_for(
            event_name="event_name",
        )
        assert_matches_type(EventWaitForResponse, event, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_wait_for_with_all_params(self, async_client: AsyncAnchorbrowser) -> None:
        event = await async_client.events.wait_for(
            event_name="event_name",
            timeout_ms=0,
        )
        assert_matches_type(EventWaitForResponse, event, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_wait_for(self, async_client: AsyncAnchorbrowser) -> None:
        response = await async_client.events.with_raw_response.wait_for(
            event_name="event_name",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        event = await response.parse()
        assert_matches_type(EventWaitForResponse, event, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_wait_for(self, async_client: AsyncAnchorbrowser) -> None:
        async with async_client.events.with_streaming_response.wait_for(
            event_name="event_name",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            event = await response.parse()
            assert_matches_type(EventWaitForResponse, event, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_wait_for(self, async_client: AsyncAnchorbrowser) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `event_name` but received ''"):
            await async_client.events.with_raw_response.wait_for(
                event_name="",
            )
