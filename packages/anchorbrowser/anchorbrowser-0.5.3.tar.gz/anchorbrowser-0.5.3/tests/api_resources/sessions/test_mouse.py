# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from anchorbrowser import Anchorbrowser, AsyncAnchorbrowser
from anchorbrowser.types.sessions import (
    MouseMoveResponse,
    MouseClickResponse,
    MouseDoubleClickResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestMouse:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_click(self, client: Anchorbrowser) -> None:
        mouse = client.sessions.mouse.click(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(MouseClickResponse, mouse, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_click_with_all_params(self, client: Anchorbrowser) -> None:
        mouse = client.sessions.mouse.click(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            button="left",
            index=0,
            selector="selector",
            selector_timeout_ms=0,
            x=0,
            y=0,
        )
        assert_matches_type(MouseClickResponse, mouse, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_click(self, client: Anchorbrowser) -> None:
        response = client.sessions.mouse.with_raw_response.click(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        mouse = response.parse()
        assert_matches_type(MouseClickResponse, mouse, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_click(self, client: Anchorbrowser) -> None:
        with client.sessions.mouse.with_streaming_response.click(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            mouse = response.parse()
            assert_matches_type(MouseClickResponse, mouse, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_click(self, client: Anchorbrowser) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            client.sessions.mouse.with_raw_response.click(
                session_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_double_click(self, client: Anchorbrowser) -> None:
        mouse = client.sessions.mouse.double_click(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            x=0,
            y=0,
        )
        assert_matches_type(MouseDoubleClickResponse, mouse, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_double_click_with_all_params(self, client: Anchorbrowser) -> None:
        mouse = client.sessions.mouse.double_click(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            x=0,
            y=0,
            button="left",
        )
        assert_matches_type(MouseDoubleClickResponse, mouse, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_double_click(self, client: Anchorbrowser) -> None:
        response = client.sessions.mouse.with_raw_response.double_click(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            x=0,
            y=0,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        mouse = response.parse()
        assert_matches_type(MouseDoubleClickResponse, mouse, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_double_click(self, client: Anchorbrowser) -> None:
        with client.sessions.mouse.with_streaming_response.double_click(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            x=0,
            y=0,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            mouse = response.parse()
            assert_matches_type(MouseDoubleClickResponse, mouse, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_double_click(self, client: Anchorbrowser) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            client.sessions.mouse.with_raw_response.double_click(
                session_id="",
                x=0,
                y=0,
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_move(self, client: Anchorbrowser) -> None:
        mouse = client.sessions.mouse.move(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            x=0,
            y=0,
        )
        assert_matches_type(MouseMoveResponse, mouse, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_move(self, client: Anchorbrowser) -> None:
        response = client.sessions.mouse.with_raw_response.move(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            x=0,
            y=0,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        mouse = response.parse()
        assert_matches_type(MouseMoveResponse, mouse, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_move(self, client: Anchorbrowser) -> None:
        with client.sessions.mouse.with_streaming_response.move(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            x=0,
            y=0,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            mouse = response.parse()
            assert_matches_type(MouseMoveResponse, mouse, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_move(self, client: Anchorbrowser) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            client.sessions.mouse.with_raw_response.move(
                session_id="",
                x=0,
                y=0,
            )


class TestAsyncMouse:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_click(self, async_client: AsyncAnchorbrowser) -> None:
        mouse = await async_client.sessions.mouse.click(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(MouseClickResponse, mouse, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_click_with_all_params(self, async_client: AsyncAnchorbrowser) -> None:
        mouse = await async_client.sessions.mouse.click(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            button="left",
            index=0,
            selector="selector",
            selector_timeout_ms=0,
            x=0,
            y=0,
        )
        assert_matches_type(MouseClickResponse, mouse, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_click(self, async_client: AsyncAnchorbrowser) -> None:
        response = await async_client.sessions.mouse.with_raw_response.click(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        mouse = await response.parse()
        assert_matches_type(MouseClickResponse, mouse, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_click(self, async_client: AsyncAnchorbrowser) -> None:
        async with async_client.sessions.mouse.with_streaming_response.click(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            mouse = await response.parse()
            assert_matches_type(MouseClickResponse, mouse, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_click(self, async_client: AsyncAnchorbrowser) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            await async_client.sessions.mouse.with_raw_response.click(
                session_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_double_click(self, async_client: AsyncAnchorbrowser) -> None:
        mouse = await async_client.sessions.mouse.double_click(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            x=0,
            y=0,
        )
        assert_matches_type(MouseDoubleClickResponse, mouse, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_double_click_with_all_params(self, async_client: AsyncAnchorbrowser) -> None:
        mouse = await async_client.sessions.mouse.double_click(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            x=0,
            y=0,
            button="left",
        )
        assert_matches_type(MouseDoubleClickResponse, mouse, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_double_click(self, async_client: AsyncAnchorbrowser) -> None:
        response = await async_client.sessions.mouse.with_raw_response.double_click(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            x=0,
            y=0,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        mouse = await response.parse()
        assert_matches_type(MouseDoubleClickResponse, mouse, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_double_click(self, async_client: AsyncAnchorbrowser) -> None:
        async with async_client.sessions.mouse.with_streaming_response.double_click(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            x=0,
            y=0,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            mouse = await response.parse()
            assert_matches_type(MouseDoubleClickResponse, mouse, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_double_click(self, async_client: AsyncAnchorbrowser) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            await async_client.sessions.mouse.with_raw_response.double_click(
                session_id="",
                x=0,
                y=0,
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_move(self, async_client: AsyncAnchorbrowser) -> None:
        mouse = await async_client.sessions.mouse.move(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            x=0,
            y=0,
        )
        assert_matches_type(MouseMoveResponse, mouse, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_move(self, async_client: AsyncAnchorbrowser) -> None:
        response = await async_client.sessions.mouse.with_raw_response.move(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            x=0,
            y=0,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        mouse = await response.parse()
        assert_matches_type(MouseMoveResponse, mouse, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_move(self, async_client: AsyncAnchorbrowser) -> None:
        async with async_client.sessions.mouse.with_streaming_response.move(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            x=0,
            y=0,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            mouse = await response.parse()
            assert_matches_type(MouseMoveResponse, mouse, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_move(self, async_client: AsyncAnchorbrowser) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            await async_client.sessions.mouse.with_raw_response.move(
                session_id="",
                x=0,
                y=0,
            )
