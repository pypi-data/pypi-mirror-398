# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from anchorbrowser import Anchorbrowser, AsyncAnchorbrowser
from anchorbrowser.types.shared import SuccessResponse
from anchorbrowser.types.sessions import AllStatusResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestAll:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: Anchorbrowser) -> None:
        all = client.sessions.all.delete()
        assert_matches_type(SuccessResponse, all, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: Anchorbrowser) -> None:
        response = client.sessions.all.with_raw_response.delete()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        all = response.parse()
        assert_matches_type(SuccessResponse, all, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: Anchorbrowser) -> None:
        with client.sessions.all.with_streaming_response.delete() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            all = response.parse()
            assert_matches_type(SuccessResponse, all, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_status(self, client: Anchorbrowser) -> None:
        all = client.sessions.all.status()
        assert_matches_type(AllStatusResponse, all, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_status(self, client: Anchorbrowser) -> None:
        response = client.sessions.all.with_raw_response.status()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        all = response.parse()
        assert_matches_type(AllStatusResponse, all, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_status(self, client: Anchorbrowser) -> None:
        with client.sessions.all.with_streaming_response.status() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            all = response.parse()
            assert_matches_type(AllStatusResponse, all, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncAll:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncAnchorbrowser) -> None:
        all = await async_client.sessions.all.delete()
        assert_matches_type(SuccessResponse, all, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncAnchorbrowser) -> None:
        response = await async_client.sessions.all.with_raw_response.delete()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        all = await response.parse()
        assert_matches_type(SuccessResponse, all, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncAnchorbrowser) -> None:
        async with async_client.sessions.all.with_streaming_response.delete() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            all = await response.parse()
            assert_matches_type(SuccessResponse, all, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_status(self, async_client: AsyncAnchorbrowser) -> None:
        all = await async_client.sessions.all.status()
        assert_matches_type(AllStatusResponse, all, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_status(self, async_client: AsyncAnchorbrowser) -> None:
        response = await async_client.sessions.all.with_raw_response.status()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        all = await response.parse()
        assert_matches_type(AllStatusResponse, all, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_status(self, async_client: AsyncAnchorbrowser) -> None:
        async with async_client.sessions.all.with_streaming_response.status() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            all = await response.parse()
            assert_matches_type(AllStatusResponse, all, path=["response"])

        assert cast(Any, response.is_closed) is True
