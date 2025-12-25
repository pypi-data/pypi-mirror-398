# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import httpx
import pytest
from respx import MockRouter

from anchorbrowser import Anchorbrowser, AsyncAnchorbrowser
from anchorbrowser._response import (
    BinaryAPIResponse,
    AsyncBinaryAPIResponse,
    StreamedBinaryAPIResponse,
    AsyncStreamedBinaryAPIResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestPrimary:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    def test_method_get(self, client: Anchorbrowser, respx_mock: MockRouter) -> None:
        respx_mock.get("/v1/sessions/session_id/recordings/primary/fetch").mock(
            return_value=httpx.Response(200, json={"foo": "bar"})
        )
        primary = client.sessions.recordings.primary.get(
            "session_id",
        )
        assert primary.is_closed
        assert primary.json() == {"foo": "bar"}
        assert cast(Any, primary.is_closed) is True
        assert isinstance(primary, BinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    def test_raw_response_get(self, client: Anchorbrowser, respx_mock: MockRouter) -> None:
        respx_mock.get("/v1/sessions/session_id/recordings/primary/fetch").mock(
            return_value=httpx.Response(200, json={"foo": "bar"})
        )

        primary = client.sessions.recordings.primary.with_raw_response.get(
            "session_id",
        )

        assert primary.is_closed is True
        assert primary.http_request.headers.get("X-Stainless-Lang") == "python"
        assert primary.json() == {"foo": "bar"}
        assert isinstance(primary, BinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    def test_streaming_response_get(self, client: Anchorbrowser, respx_mock: MockRouter) -> None:
        respx_mock.get("/v1/sessions/session_id/recordings/primary/fetch").mock(
            return_value=httpx.Response(200, json={"foo": "bar"})
        )
        with client.sessions.recordings.primary.with_streaming_response.get(
            "session_id",
        ) as primary:
            assert not primary.is_closed
            assert primary.http_request.headers.get("X-Stainless-Lang") == "python"

            assert primary.json() == {"foo": "bar"}
            assert cast(Any, primary.is_closed) is True
            assert isinstance(primary, StreamedBinaryAPIResponse)

        assert cast(Any, primary.is_closed) is True

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    def test_path_params_get(self, client: Anchorbrowser) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            client.sessions.recordings.primary.with_raw_response.get(
                "",
            )


class TestAsyncPrimary:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    async def test_method_get(self, async_client: AsyncAnchorbrowser, respx_mock: MockRouter) -> None:
        respx_mock.get("/v1/sessions/session_id/recordings/primary/fetch").mock(
            return_value=httpx.Response(200, json={"foo": "bar"})
        )
        primary = await async_client.sessions.recordings.primary.get(
            "session_id",
        )
        assert primary.is_closed
        assert await primary.json() == {"foo": "bar"}
        assert cast(Any, primary.is_closed) is True
        assert isinstance(primary, AsyncBinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    async def test_raw_response_get(self, async_client: AsyncAnchorbrowser, respx_mock: MockRouter) -> None:
        respx_mock.get("/v1/sessions/session_id/recordings/primary/fetch").mock(
            return_value=httpx.Response(200, json={"foo": "bar"})
        )

        primary = await async_client.sessions.recordings.primary.with_raw_response.get(
            "session_id",
        )

        assert primary.is_closed is True
        assert primary.http_request.headers.get("X-Stainless-Lang") == "python"
        assert await primary.json() == {"foo": "bar"}
        assert isinstance(primary, AsyncBinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    async def test_streaming_response_get(self, async_client: AsyncAnchorbrowser, respx_mock: MockRouter) -> None:
        respx_mock.get("/v1/sessions/session_id/recordings/primary/fetch").mock(
            return_value=httpx.Response(200, json={"foo": "bar"})
        )
        async with async_client.sessions.recordings.primary.with_streaming_response.get(
            "session_id",
        ) as primary:
            assert not primary.is_closed
            assert primary.http_request.headers.get("X-Stainless-Lang") == "python"

            assert await primary.json() == {"foo": "bar"}
            assert cast(Any, primary.is_closed) is True
            assert isinstance(primary, AsyncStreamedBinaryAPIResponse)

        assert cast(Any, primary.is_closed) is True

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    async def test_path_params_get(self, async_client: AsyncAnchorbrowser) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            await async_client.sessions.recordings.primary.with_raw_response.get(
                "",
            )
