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
    SessionCopyResponse,
    SessionGotoResponse,
    SessionPasteResponse,
    SessionCreateResponse,
    SessionScrollResponse,
    SessionRetrieveResponse,
    SessionListPagesResponse,
    SessionUploadFileResponse,
    SessionDragAndDropResponse,
    SessionRetrieveDownloadsResponse,
)
from anchorbrowser._response import (
    BinaryAPIResponse,
    AsyncBinaryAPIResponse,
    StreamedBinaryAPIResponse,
    AsyncStreamedBinaryAPIResponse,
)
from anchorbrowser.types.shared import SuccessResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestSessions:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: Anchorbrowser) -> None:
        session = client.sessions.create()
        assert_matches_type(SessionCreateResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_with_all_params(self, client: Anchorbrowser) -> None:
        session = client.sessions.create(
            browser={
                "adblock": {"active": True},
                "captcha_solver": {"active": True},
                "disable_web_security": {"active": True},
                "extensions": ["182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e"],
                "extra_stealth": {"active": True},
                "fullscreen": {"active": True},
                "headless": {"active": True},
                "p2p_download": {"active": True},
                "popup_blocker": {"active": True},
                "profile": {
                    "name": "name",
                    "persist": True,
                },
                "viewport": {
                    "height": 0,
                    "width": 0,
                },
            },
            integrations=[
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "configuration": {"load_mode": "all"},
                    "type": "1PASSWORD",
                }
            ],
            session={
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
        )
        assert_matches_type(SessionCreateResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: Anchorbrowser) -> None:
        response = client.sessions.with_raw_response.create()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        session = response.parse()
        assert_matches_type(SessionCreateResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: Anchorbrowser) -> None:
        with client.sessions.with_streaming_response.create() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            session = response.parse()
            assert_matches_type(SessionCreateResponse, session, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: Anchorbrowser) -> None:
        session = client.sessions.retrieve(
            "session_id",
        )
        assert_matches_type(SessionRetrieveResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: Anchorbrowser) -> None:
        response = client.sessions.with_raw_response.retrieve(
            "session_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        session = response.parse()
        assert_matches_type(SessionRetrieveResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: Anchorbrowser) -> None:
        with client.sessions.with_streaming_response.retrieve(
            "session_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            session = response.parse()
            assert_matches_type(SessionRetrieveResponse, session, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: Anchorbrowser) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            client.sessions.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: Anchorbrowser) -> None:
        session = client.sessions.delete(
            "session_id",
        )
        assert_matches_type(SuccessResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: Anchorbrowser) -> None:
        response = client.sessions.with_raw_response.delete(
            "session_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        session = response.parse()
        assert_matches_type(SuccessResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: Anchorbrowser) -> None:
        with client.sessions.with_streaming_response.delete(
            "session_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            session = response.parse()
            assert_matches_type(SuccessResponse, session, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_delete(self, client: Anchorbrowser) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            client.sessions.with_raw_response.delete(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_copy(self, client: Anchorbrowser) -> None:
        session = client.sessions.copy(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(SessionCopyResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_copy(self, client: Anchorbrowser) -> None:
        response = client.sessions.with_raw_response.copy(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        session = response.parse()
        assert_matches_type(SessionCopyResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_copy(self, client: Anchorbrowser) -> None:
        with client.sessions.with_streaming_response.copy(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            session = response.parse()
            assert_matches_type(SessionCopyResponse, session, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_copy(self, client: Anchorbrowser) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            client.sessions.with_raw_response.copy(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_drag_and_drop(self, client: Anchorbrowser) -> None:
        session = client.sessions.drag_and_drop(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            end_x=0,
            end_y=0,
            start_x=0,
            start_y=0,
        )
        assert_matches_type(SessionDragAndDropResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_drag_and_drop_with_all_params(self, client: Anchorbrowser) -> None:
        session = client.sessions.drag_and_drop(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            end_x=0,
            end_y=0,
            start_x=0,
            start_y=0,
            button="left",
        )
        assert_matches_type(SessionDragAndDropResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_drag_and_drop(self, client: Anchorbrowser) -> None:
        response = client.sessions.with_raw_response.drag_and_drop(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            end_x=0,
            end_y=0,
            start_x=0,
            start_y=0,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        session = response.parse()
        assert_matches_type(SessionDragAndDropResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_drag_and_drop(self, client: Anchorbrowser) -> None:
        with client.sessions.with_streaming_response.drag_and_drop(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            end_x=0,
            end_y=0,
            start_x=0,
            start_y=0,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            session = response.parse()
            assert_matches_type(SessionDragAndDropResponse, session, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_drag_and_drop(self, client: Anchorbrowser) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            client.sessions.with_raw_response.drag_and_drop(
                session_id="",
                end_x=0,
                end_y=0,
                start_x=0,
                start_y=0,
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_goto(self, client: Anchorbrowser) -> None:
        session = client.sessions.goto(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            url="url",
        )
        assert_matches_type(SessionGotoResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_goto(self, client: Anchorbrowser) -> None:
        response = client.sessions.with_raw_response.goto(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            url="url",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        session = response.parse()
        assert_matches_type(SessionGotoResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_goto(self, client: Anchorbrowser) -> None:
        with client.sessions.with_streaming_response.goto(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            url="url",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            session = response.parse()
            assert_matches_type(SessionGotoResponse, session, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_goto(self, client: Anchorbrowser) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            client.sessions.with_raw_response.goto(
                session_id="",
                url="url",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_pages(self, client: Anchorbrowser) -> None:
        session = client.sessions.list_pages(
            "session_id",
        )
        assert_matches_type(SessionListPagesResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list_pages(self, client: Anchorbrowser) -> None:
        response = client.sessions.with_raw_response.list_pages(
            "session_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        session = response.parse()
        assert_matches_type(SessionListPagesResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list_pages(self, client: Anchorbrowser) -> None:
        with client.sessions.with_streaming_response.list_pages(
            "session_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            session = response.parse()
            assert_matches_type(SessionListPagesResponse, session, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_list_pages(self, client: Anchorbrowser) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            client.sessions.with_raw_response.list_pages(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_paste(self, client: Anchorbrowser) -> None:
        session = client.sessions.paste(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            text="text",
        )
        assert_matches_type(SessionPasteResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_paste(self, client: Anchorbrowser) -> None:
        response = client.sessions.with_raw_response.paste(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            text="text",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        session = response.parse()
        assert_matches_type(SessionPasteResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_paste(self, client: Anchorbrowser) -> None:
        with client.sessions.with_streaming_response.paste(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            text="text",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            session = response.parse()
            assert_matches_type(SessionPasteResponse, session, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_paste(self, client: Anchorbrowser) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            client.sessions.with_raw_response.paste(
                session_id="",
                text="text",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_downloads(self, client: Anchorbrowser) -> None:
        session = client.sessions.retrieve_downloads(
            "session_id",
        )
        assert_matches_type(SessionRetrieveDownloadsResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve_downloads(self, client: Anchorbrowser) -> None:
        response = client.sessions.with_raw_response.retrieve_downloads(
            "session_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        session = response.parse()
        assert_matches_type(SessionRetrieveDownloadsResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve_downloads(self, client: Anchorbrowser) -> None:
        with client.sessions.with_streaming_response.retrieve_downloads(
            "session_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            session = response.parse()
            assert_matches_type(SessionRetrieveDownloadsResponse, session, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve_downloads(self, client: Anchorbrowser) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            client.sessions.with_raw_response.retrieve_downloads(
                "",
            )

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    def test_method_retrieve_screenshot(self, client: Anchorbrowser, respx_mock: MockRouter) -> None:
        respx_mock.get("/v1/sessions/182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e/screenshot").mock(
            return_value=httpx.Response(200, json={"foo": "bar"})
        )
        session = client.sessions.retrieve_screenshot(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert session.is_closed
        assert session.json() == {"foo": "bar"}
        assert cast(Any, session.is_closed) is True
        assert isinstance(session, BinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    def test_raw_response_retrieve_screenshot(self, client: Anchorbrowser, respx_mock: MockRouter) -> None:
        respx_mock.get("/v1/sessions/182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e/screenshot").mock(
            return_value=httpx.Response(200, json={"foo": "bar"})
        )

        session = client.sessions.with_raw_response.retrieve_screenshot(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert session.is_closed is True
        assert session.http_request.headers.get("X-Stainless-Lang") == "python"
        assert session.json() == {"foo": "bar"}
        assert isinstance(session, BinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    def test_streaming_response_retrieve_screenshot(self, client: Anchorbrowser, respx_mock: MockRouter) -> None:
        respx_mock.get("/v1/sessions/182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e/screenshot").mock(
            return_value=httpx.Response(200, json={"foo": "bar"})
        )
        with client.sessions.with_streaming_response.retrieve_screenshot(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as session:
            assert not session.is_closed
            assert session.http_request.headers.get("X-Stainless-Lang") == "python"

            assert session.json() == {"foo": "bar"}
            assert cast(Any, session.is_closed) is True
            assert isinstance(session, StreamedBinaryAPIResponse)

        assert cast(Any, session.is_closed) is True

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    def test_path_params_retrieve_screenshot(self, client: Anchorbrowser) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            client.sessions.with_raw_response.retrieve_screenshot(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_scroll(self, client: Anchorbrowser) -> None:
        session = client.sessions.scroll(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            delta_y=0,
            x=0,
            y=0,
        )
        assert_matches_type(SessionScrollResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_scroll_with_all_params(self, client: Anchorbrowser) -> None:
        session = client.sessions.scroll(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            delta_y=0,
            x=0,
            y=0,
            delta_x=0,
            steps=0,
            use_os=True,
        )
        assert_matches_type(SessionScrollResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_scroll(self, client: Anchorbrowser) -> None:
        response = client.sessions.with_raw_response.scroll(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            delta_y=0,
            x=0,
            y=0,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        session = response.parse()
        assert_matches_type(SessionScrollResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_scroll(self, client: Anchorbrowser) -> None:
        with client.sessions.with_streaming_response.scroll(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            delta_y=0,
            x=0,
            y=0,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            session = response.parse()
            assert_matches_type(SessionScrollResponse, session, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_scroll(self, client: Anchorbrowser) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            client.sessions.with_raw_response.scroll(
                session_id="",
                delta_y=0,
                x=0,
                y=0,
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_upload_file(self, client: Anchorbrowser) -> None:
        session = client.sessions.upload_file(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            file=b"raw file contents",
        )
        assert_matches_type(SessionUploadFileResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_upload_file(self, client: Anchorbrowser) -> None:
        response = client.sessions.with_raw_response.upload_file(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            file=b"raw file contents",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        session = response.parse()
        assert_matches_type(SessionUploadFileResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_upload_file(self, client: Anchorbrowser) -> None:
        with client.sessions.with_streaming_response.upload_file(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            file=b"raw file contents",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            session = response.parse()
            assert_matches_type(SessionUploadFileResponse, session, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_upload_file(self, client: Anchorbrowser) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            client.sessions.with_raw_response.upload_file(
                session_id="",
                file=b"raw file contents",
            )


class TestAsyncSessions:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncAnchorbrowser) -> None:
        session = await async_client.sessions.create()
        assert_matches_type(SessionCreateResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncAnchorbrowser) -> None:
        session = await async_client.sessions.create(
            browser={
                "adblock": {"active": True},
                "captcha_solver": {"active": True},
                "disable_web_security": {"active": True},
                "extensions": ["182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e"],
                "extra_stealth": {"active": True},
                "fullscreen": {"active": True},
                "headless": {"active": True},
                "p2p_download": {"active": True},
                "popup_blocker": {"active": True},
                "profile": {
                    "name": "name",
                    "persist": True,
                },
                "viewport": {
                    "height": 0,
                    "width": 0,
                },
            },
            integrations=[
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "configuration": {"load_mode": "all"},
                    "type": "1PASSWORD",
                }
            ],
            session={
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
        )
        assert_matches_type(SessionCreateResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncAnchorbrowser) -> None:
        response = await async_client.sessions.with_raw_response.create()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        session = await response.parse()
        assert_matches_type(SessionCreateResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncAnchorbrowser) -> None:
        async with async_client.sessions.with_streaming_response.create() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            session = await response.parse()
            assert_matches_type(SessionCreateResponse, session, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncAnchorbrowser) -> None:
        session = await async_client.sessions.retrieve(
            "session_id",
        )
        assert_matches_type(SessionRetrieveResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncAnchorbrowser) -> None:
        response = await async_client.sessions.with_raw_response.retrieve(
            "session_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        session = await response.parse()
        assert_matches_type(SessionRetrieveResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncAnchorbrowser) -> None:
        async with async_client.sessions.with_streaming_response.retrieve(
            "session_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            session = await response.parse()
            assert_matches_type(SessionRetrieveResponse, session, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncAnchorbrowser) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            await async_client.sessions.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncAnchorbrowser) -> None:
        session = await async_client.sessions.delete(
            "session_id",
        )
        assert_matches_type(SuccessResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncAnchorbrowser) -> None:
        response = await async_client.sessions.with_raw_response.delete(
            "session_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        session = await response.parse()
        assert_matches_type(SuccessResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncAnchorbrowser) -> None:
        async with async_client.sessions.with_streaming_response.delete(
            "session_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            session = await response.parse()
            assert_matches_type(SuccessResponse, session, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_delete(self, async_client: AsyncAnchorbrowser) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            await async_client.sessions.with_raw_response.delete(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_copy(self, async_client: AsyncAnchorbrowser) -> None:
        session = await async_client.sessions.copy(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(SessionCopyResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_copy(self, async_client: AsyncAnchorbrowser) -> None:
        response = await async_client.sessions.with_raw_response.copy(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        session = await response.parse()
        assert_matches_type(SessionCopyResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_copy(self, async_client: AsyncAnchorbrowser) -> None:
        async with async_client.sessions.with_streaming_response.copy(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            session = await response.parse()
            assert_matches_type(SessionCopyResponse, session, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_copy(self, async_client: AsyncAnchorbrowser) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            await async_client.sessions.with_raw_response.copy(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_drag_and_drop(self, async_client: AsyncAnchorbrowser) -> None:
        session = await async_client.sessions.drag_and_drop(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            end_x=0,
            end_y=0,
            start_x=0,
            start_y=0,
        )
        assert_matches_type(SessionDragAndDropResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_drag_and_drop_with_all_params(self, async_client: AsyncAnchorbrowser) -> None:
        session = await async_client.sessions.drag_and_drop(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            end_x=0,
            end_y=0,
            start_x=0,
            start_y=0,
            button="left",
        )
        assert_matches_type(SessionDragAndDropResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_drag_and_drop(self, async_client: AsyncAnchorbrowser) -> None:
        response = await async_client.sessions.with_raw_response.drag_and_drop(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            end_x=0,
            end_y=0,
            start_x=0,
            start_y=0,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        session = await response.parse()
        assert_matches_type(SessionDragAndDropResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_drag_and_drop(self, async_client: AsyncAnchorbrowser) -> None:
        async with async_client.sessions.with_streaming_response.drag_and_drop(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            end_x=0,
            end_y=0,
            start_x=0,
            start_y=0,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            session = await response.parse()
            assert_matches_type(SessionDragAndDropResponse, session, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_drag_and_drop(self, async_client: AsyncAnchorbrowser) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            await async_client.sessions.with_raw_response.drag_and_drop(
                session_id="",
                end_x=0,
                end_y=0,
                start_x=0,
                start_y=0,
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_goto(self, async_client: AsyncAnchorbrowser) -> None:
        session = await async_client.sessions.goto(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            url="url",
        )
        assert_matches_type(SessionGotoResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_goto(self, async_client: AsyncAnchorbrowser) -> None:
        response = await async_client.sessions.with_raw_response.goto(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            url="url",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        session = await response.parse()
        assert_matches_type(SessionGotoResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_goto(self, async_client: AsyncAnchorbrowser) -> None:
        async with async_client.sessions.with_streaming_response.goto(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            url="url",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            session = await response.parse()
            assert_matches_type(SessionGotoResponse, session, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_goto(self, async_client: AsyncAnchorbrowser) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            await async_client.sessions.with_raw_response.goto(
                session_id="",
                url="url",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_pages(self, async_client: AsyncAnchorbrowser) -> None:
        session = await async_client.sessions.list_pages(
            "session_id",
        )
        assert_matches_type(SessionListPagesResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list_pages(self, async_client: AsyncAnchorbrowser) -> None:
        response = await async_client.sessions.with_raw_response.list_pages(
            "session_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        session = await response.parse()
        assert_matches_type(SessionListPagesResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list_pages(self, async_client: AsyncAnchorbrowser) -> None:
        async with async_client.sessions.with_streaming_response.list_pages(
            "session_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            session = await response.parse()
            assert_matches_type(SessionListPagesResponse, session, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_list_pages(self, async_client: AsyncAnchorbrowser) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            await async_client.sessions.with_raw_response.list_pages(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_paste(self, async_client: AsyncAnchorbrowser) -> None:
        session = await async_client.sessions.paste(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            text="text",
        )
        assert_matches_type(SessionPasteResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_paste(self, async_client: AsyncAnchorbrowser) -> None:
        response = await async_client.sessions.with_raw_response.paste(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            text="text",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        session = await response.parse()
        assert_matches_type(SessionPasteResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_paste(self, async_client: AsyncAnchorbrowser) -> None:
        async with async_client.sessions.with_streaming_response.paste(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            text="text",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            session = await response.parse()
            assert_matches_type(SessionPasteResponse, session, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_paste(self, async_client: AsyncAnchorbrowser) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            await async_client.sessions.with_raw_response.paste(
                session_id="",
                text="text",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_downloads(self, async_client: AsyncAnchorbrowser) -> None:
        session = await async_client.sessions.retrieve_downloads(
            "session_id",
        )
        assert_matches_type(SessionRetrieveDownloadsResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve_downloads(self, async_client: AsyncAnchorbrowser) -> None:
        response = await async_client.sessions.with_raw_response.retrieve_downloads(
            "session_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        session = await response.parse()
        assert_matches_type(SessionRetrieveDownloadsResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve_downloads(self, async_client: AsyncAnchorbrowser) -> None:
        async with async_client.sessions.with_streaming_response.retrieve_downloads(
            "session_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            session = await response.parse()
            assert_matches_type(SessionRetrieveDownloadsResponse, session, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve_downloads(self, async_client: AsyncAnchorbrowser) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            await async_client.sessions.with_raw_response.retrieve_downloads(
                "",
            )

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    async def test_method_retrieve_screenshot(self, async_client: AsyncAnchorbrowser, respx_mock: MockRouter) -> None:
        respx_mock.get("/v1/sessions/182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e/screenshot").mock(
            return_value=httpx.Response(200, json={"foo": "bar"})
        )
        session = await async_client.sessions.retrieve_screenshot(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert session.is_closed
        assert await session.json() == {"foo": "bar"}
        assert cast(Any, session.is_closed) is True
        assert isinstance(session, AsyncBinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    async def test_raw_response_retrieve_screenshot(
        self, async_client: AsyncAnchorbrowser, respx_mock: MockRouter
    ) -> None:
        respx_mock.get("/v1/sessions/182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e/screenshot").mock(
            return_value=httpx.Response(200, json={"foo": "bar"})
        )

        session = await async_client.sessions.with_raw_response.retrieve_screenshot(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert session.is_closed is True
        assert session.http_request.headers.get("X-Stainless-Lang") == "python"
        assert await session.json() == {"foo": "bar"}
        assert isinstance(session, AsyncBinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    async def test_streaming_response_retrieve_screenshot(
        self, async_client: AsyncAnchorbrowser, respx_mock: MockRouter
    ) -> None:
        respx_mock.get("/v1/sessions/182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e/screenshot").mock(
            return_value=httpx.Response(200, json={"foo": "bar"})
        )
        async with async_client.sessions.with_streaming_response.retrieve_screenshot(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as session:
            assert not session.is_closed
            assert session.http_request.headers.get("X-Stainless-Lang") == "python"

            assert await session.json() == {"foo": "bar"}
            assert cast(Any, session.is_closed) is True
            assert isinstance(session, AsyncStreamedBinaryAPIResponse)

        assert cast(Any, session.is_closed) is True

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    async def test_path_params_retrieve_screenshot(self, async_client: AsyncAnchorbrowser) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            await async_client.sessions.with_raw_response.retrieve_screenshot(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_scroll(self, async_client: AsyncAnchorbrowser) -> None:
        session = await async_client.sessions.scroll(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            delta_y=0,
            x=0,
            y=0,
        )
        assert_matches_type(SessionScrollResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_scroll_with_all_params(self, async_client: AsyncAnchorbrowser) -> None:
        session = await async_client.sessions.scroll(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            delta_y=0,
            x=0,
            y=0,
            delta_x=0,
            steps=0,
            use_os=True,
        )
        assert_matches_type(SessionScrollResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_scroll(self, async_client: AsyncAnchorbrowser) -> None:
        response = await async_client.sessions.with_raw_response.scroll(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            delta_y=0,
            x=0,
            y=0,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        session = await response.parse()
        assert_matches_type(SessionScrollResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_scroll(self, async_client: AsyncAnchorbrowser) -> None:
        async with async_client.sessions.with_streaming_response.scroll(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            delta_y=0,
            x=0,
            y=0,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            session = await response.parse()
            assert_matches_type(SessionScrollResponse, session, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_scroll(self, async_client: AsyncAnchorbrowser) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            await async_client.sessions.with_raw_response.scroll(
                session_id="",
                delta_y=0,
                x=0,
                y=0,
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_upload_file(self, async_client: AsyncAnchorbrowser) -> None:
        session = await async_client.sessions.upload_file(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            file=b"raw file contents",
        )
        assert_matches_type(SessionUploadFileResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_upload_file(self, async_client: AsyncAnchorbrowser) -> None:
        response = await async_client.sessions.with_raw_response.upload_file(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            file=b"raw file contents",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        session = await response.parse()
        assert_matches_type(SessionUploadFileResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_upload_file(self, async_client: AsyncAnchorbrowser) -> None:
        async with async_client.sessions.with_streaming_response.upload_file(
            session_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            file=b"raw file contents",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            session = await response.parse()
            assert_matches_type(SessionUploadFileResponse, session, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_upload_file(self, async_client: AsyncAnchorbrowser) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            await async_client.sessions.with_raw_response.upload_file(
                session_id="",
                file=b"raw file contents",
            )
