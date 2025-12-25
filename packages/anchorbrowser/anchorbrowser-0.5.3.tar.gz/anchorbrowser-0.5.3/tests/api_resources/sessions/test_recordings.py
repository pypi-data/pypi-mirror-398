# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from anchorbrowser import Anchorbrowser, AsyncAnchorbrowser
from anchorbrowser.types.sessions import RecordingListResponse, RecordingPauseResponse, RecordingResumeResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestRecordings:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Anchorbrowser) -> None:
        recording = client.sessions.recordings.list(
            "session_id",
        )
        assert_matches_type(RecordingListResponse, recording, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Anchorbrowser) -> None:
        response = client.sessions.recordings.with_raw_response.list(
            "session_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        recording = response.parse()
        assert_matches_type(RecordingListResponse, recording, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Anchorbrowser) -> None:
        with client.sessions.recordings.with_streaming_response.list(
            "session_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            recording = response.parse()
            assert_matches_type(RecordingListResponse, recording, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_list(self, client: Anchorbrowser) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            client.sessions.recordings.with_raw_response.list(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_pause(self, client: Anchorbrowser) -> None:
        recording = client.sessions.recordings.pause(
            "session_id",
        )
        assert_matches_type(RecordingPauseResponse, recording, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_pause(self, client: Anchorbrowser) -> None:
        response = client.sessions.recordings.with_raw_response.pause(
            "session_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        recording = response.parse()
        assert_matches_type(RecordingPauseResponse, recording, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_pause(self, client: Anchorbrowser) -> None:
        with client.sessions.recordings.with_streaming_response.pause(
            "session_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            recording = response.parse()
            assert_matches_type(RecordingPauseResponse, recording, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_pause(self, client: Anchorbrowser) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            client.sessions.recordings.with_raw_response.pause(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_resume(self, client: Anchorbrowser) -> None:
        recording = client.sessions.recordings.resume(
            "session_id",
        )
        assert_matches_type(RecordingResumeResponse, recording, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_resume(self, client: Anchorbrowser) -> None:
        response = client.sessions.recordings.with_raw_response.resume(
            "session_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        recording = response.parse()
        assert_matches_type(RecordingResumeResponse, recording, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_resume(self, client: Anchorbrowser) -> None:
        with client.sessions.recordings.with_streaming_response.resume(
            "session_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            recording = response.parse()
            assert_matches_type(RecordingResumeResponse, recording, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_resume(self, client: Anchorbrowser) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            client.sessions.recordings.with_raw_response.resume(
                "",
            )


class TestAsyncRecordings:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncAnchorbrowser) -> None:
        recording = await async_client.sessions.recordings.list(
            "session_id",
        )
        assert_matches_type(RecordingListResponse, recording, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncAnchorbrowser) -> None:
        response = await async_client.sessions.recordings.with_raw_response.list(
            "session_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        recording = await response.parse()
        assert_matches_type(RecordingListResponse, recording, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncAnchorbrowser) -> None:
        async with async_client.sessions.recordings.with_streaming_response.list(
            "session_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            recording = await response.parse()
            assert_matches_type(RecordingListResponse, recording, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_list(self, async_client: AsyncAnchorbrowser) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            await async_client.sessions.recordings.with_raw_response.list(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_pause(self, async_client: AsyncAnchorbrowser) -> None:
        recording = await async_client.sessions.recordings.pause(
            "session_id",
        )
        assert_matches_type(RecordingPauseResponse, recording, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_pause(self, async_client: AsyncAnchorbrowser) -> None:
        response = await async_client.sessions.recordings.with_raw_response.pause(
            "session_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        recording = await response.parse()
        assert_matches_type(RecordingPauseResponse, recording, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_pause(self, async_client: AsyncAnchorbrowser) -> None:
        async with async_client.sessions.recordings.with_streaming_response.pause(
            "session_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            recording = await response.parse()
            assert_matches_type(RecordingPauseResponse, recording, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_pause(self, async_client: AsyncAnchorbrowser) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            await async_client.sessions.recordings.with_raw_response.pause(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_resume(self, async_client: AsyncAnchorbrowser) -> None:
        recording = await async_client.sessions.recordings.resume(
            "session_id",
        )
        assert_matches_type(RecordingResumeResponse, recording, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_resume(self, async_client: AsyncAnchorbrowser) -> None:
        response = await async_client.sessions.recordings.with_raw_response.resume(
            "session_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        recording = await response.parse()
        assert_matches_type(RecordingResumeResponse, recording, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_resume(self, async_client: AsyncAnchorbrowser) -> None:
        async with async_client.sessions.recordings.with_streaming_response.resume(
            "session_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            recording = await response.parse()
            assert_matches_type(RecordingResumeResponse, recording, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_resume(self, async_client: AsyncAnchorbrowser) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            await async_client.sessions.recordings.with_raw_response.resume(
                "",
            )
