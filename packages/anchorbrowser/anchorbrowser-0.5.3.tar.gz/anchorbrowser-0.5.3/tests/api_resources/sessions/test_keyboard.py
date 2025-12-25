# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from anchorbrowser import Anchorbrowser, AsyncAnchorbrowser
from anchorbrowser.types.sessions import (
    KeyboardTypeResponse,
    KeyboardShortcutResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestKeyboard:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_shortcut(self, client: Anchorbrowser) -> None:
        keyboard = client.sessions.keyboard.shortcut(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            keys=["string"],
        )
        assert_matches_type(KeyboardShortcutResponse, keyboard, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_shortcut_with_all_params(self, client: Anchorbrowser) -> None:
        keyboard = client.sessions.keyboard.shortcut(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            keys=["string"],
            hold_time=0,
        )
        assert_matches_type(KeyboardShortcutResponse, keyboard, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_shortcut(self, client: Anchorbrowser) -> None:
        response = client.sessions.keyboard.with_raw_response.shortcut(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            keys=["string"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        keyboard = response.parse()
        assert_matches_type(KeyboardShortcutResponse, keyboard, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_shortcut(self, client: Anchorbrowser) -> None:
        with client.sessions.keyboard.with_streaming_response.shortcut(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            keys=["string"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            keyboard = response.parse()
            assert_matches_type(KeyboardShortcutResponse, keyboard, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_shortcut(self, client: Anchorbrowser) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            client.sessions.keyboard.with_raw_response.shortcut(
                session_id="",
                keys=["string"],
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_type(self, client: Anchorbrowser) -> None:
        keyboard = client.sessions.keyboard.type(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            text="text",
        )
        assert_matches_type(KeyboardTypeResponse, keyboard, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_type_with_all_params(self, client: Anchorbrowser) -> None:
        keyboard = client.sessions.keyboard.type(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            text="text",
            delay=0,
        )
        assert_matches_type(KeyboardTypeResponse, keyboard, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_type(self, client: Anchorbrowser) -> None:
        response = client.sessions.keyboard.with_raw_response.type(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            text="text",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        keyboard = response.parse()
        assert_matches_type(KeyboardTypeResponse, keyboard, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_type(self, client: Anchorbrowser) -> None:
        with client.sessions.keyboard.with_streaming_response.type(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            text="text",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            keyboard = response.parse()
            assert_matches_type(KeyboardTypeResponse, keyboard, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_type(self, client: Anchorbrowser) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            client.sessions.keyboard.with_raw_response.type(
                session_id="",
                text="text",
            )


class TestAsyncKeyboard:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_shortcut(self, async_client: AsyncAnchorbrowser) -> None:
        keyboard = await async_client.sessions.keyboard.shortcut(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            keys=["string"],
        )
        assert_matches_type(KeyboardShortcutResponse, keyboard, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_shortcut_with_all_params(self, async_client: AsyncAnchorbrowser) -> None:
        keyboard = await async_client.sessions.keyboard.shortcut(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            keys=["string"],
            hold_time=0,
        )
        assert_matches_type(KeyboardShortcutResponse, keyboard, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_shortcut(self, async_client: AsyncAnchorbrowser) -> None:
        response = await async_client.sessions.keyboard.with_raw_response.shortcut(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            keys=["string"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        keyboard = await response.parse()
        assert_matches_type(KeyboardShortcutResponse, keyboard, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_shortcut(self, async_client: AsyncAnchorbrowser) -> None:
        async with async_client.sessions.keyboard.with_streaming_response.shortcut(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            keys=["string"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            keyboard = await response.parse()
            assert_matches_type(KeyboardShortcutResponse, keyboard, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_shortcut(self, async_client: AsyncAnchorbrowser) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            await async_client.sessions.keyboard.with_raw_response.shortcut(
                session_id="",
                keys=["string"],
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_type(self, async_client: AsyncAnchorbrowser) -> None:
        keyboard = await async_client.sessions.keyboard.type(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            text="text",
        )
        assert_matches_type(KeyboardTypeResponse, keyboard, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_type_with_all_params(self, async_client: AsyncAnchorbrowser) -> None:
        keyboard = await async_client.sessions.keyboard.type(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            text="text",
            delay=0,
        )
        assert_matches_type(KeyboardTypeResponse, keyboard, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_type(self, async_client: AsyncAnchorbrowser) -> None:
        response = await async_client.sessions.keyboard.with_raw_response.type(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            text="text",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        keyboard = await response.parse()
        assert_matches_type(KeyboardTypeResponse, keyboard, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_type(self, async_client: AsyncAnchorbrowser) -> None:
        async with async_client.sessions.keyboard.with_streaming_response.type(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            text="text",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            keyboard = await response.parse()
            assert_matches_type(KeyboardTypeResponse, keyboard, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_type(self, async_client: AsyncAnchorbrowser) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            await async_client.sessions.keyboard.with_raw_response.type(
                session_id="",
                text="text",
            )
