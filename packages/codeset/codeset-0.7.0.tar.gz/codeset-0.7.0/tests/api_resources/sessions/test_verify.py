# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from codeset import Codeset, AsyncCodeset
from tests.utils import assert_matches_type
from codeset.types.sessions import VerifyStartResponse, VerifyStatusResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestVerify:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_start(self, client: Codeset) -> None:
        verify = client.sessions.verify.start(
            "session_id",
        )
        assert_matches_type(VerifyStartResponse, verify, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_start(self, client: Codeset) -> None:
        response = client.sessions.verify.with_raw_response.start(
            "session_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        verify = response.parse()
        assert_matches_type(VerifyStartResponse, verify, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_start(self, client: Codeset) -> None:
        with client.sessions.verify.with_streaming_response.start(
            "session_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            verify = response.parse()
            assert_matches_type(VerifyStartResponse, verify, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_start(self, client: Codeset) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            client.sessions.verify.with_raw_response.start(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_status(self, client: Codeset) -> None:
        verify = client.sessions.verify.status(
            job_id="job_id",
            session_id="session_id",
        )
        assert_matches_type(VerifyStatusResponse, verify, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_status(self, client: Codeset) -> None:
        response = client.sessions.verify.with_raw_response.status(
            job_id="job_id",
            session_id="session_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        verify = response.parse()
        assert_matches_type(VerifyStatusResponse, verify, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_status(self, client: Codeset) -> None:
        with client.sessions.verify.with_streaming_response.status(
            job_id="job_id",
            session_id="session_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            verify = response.parse()
            assert_matches_type(VerifyStatusResponse, verify, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_status(self, client: Codeset) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            client.sessions.verify.with_raw_response.status(
                job_id="job_id",
                session_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `job_id` but received ''"):
            client.sessions.verify.with_raw_response.status(
                job_id="",
                session_id="session_id",
            )


class TestAsyncVerify:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_start(self, async_client: AsyncCodeset) -> None:
        verify = await async_client.sessions.verify.start(
            "session_id",
        )
        assert_matches_type(VerifyStartResponse, verify, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_start(self, async_client: AsyncCodeset) -> None:
        response = await async_client.sessions.verify.with_raw_response.start(
            "session_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        verify = await response.parse()
        assert_matches_type(VerifyStartResponse, verify, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_start(self, async_client: AsyncCodeset) -> None:
        async with async_client.sessions.verify.with_streaming_response.start(
            "session_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            verify = await response.parse()
            assert_matches_type(VerifyStartResponse, verify, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_start(self, async_client: AsyncCodeset) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            await async_client.sessions.verify.with_raw_response.start(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_status(self, async_client: AsyncCodeset) -> None:
        verify = await async_client.sessions.verify.status(
            job_id="job_id",
            session_id="session_id",
        )
        assert_matches_type(VerifyStatusResponse, verify, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_status(self, async_client: AsyncCodeset) -> None:
        response = await async_client.sessions.verify.with_raw_response.status(
            job_id="job_id",
            session_id="session_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        verify = await response.parse()
        assert_matches_type(VerifyStatusResponse, verify, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_status(self, async_client: AsyncCodeset) -> None:
        async with async_client.sessions.verify.with_streaming_response.status(
            job_id="job_id",
            session_id="session_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            verify = await response.parse()
            assert_matches_type(VerifyStatusResponse, verify, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_status(self, async_client: AsyncCodeset) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            await async_client.sessions.verify.with_raw_response.status(
                job_id="job_id",
                session_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `job_id` but received ''"):
            await async_client.sessions.verify.with_raw_response.status(
                job_id="",
                session_id="session_id",
            )
