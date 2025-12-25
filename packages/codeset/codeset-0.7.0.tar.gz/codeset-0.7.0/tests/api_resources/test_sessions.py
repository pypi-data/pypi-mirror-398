# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from codeset import Codeset, AsyncCodeset
from tests.utils import assert_matches_type
from codeset.types import (
    Session,
    SessionListResponse,
    SessionCloseResponse,
    SessionCreateResponse,
    SessionStrReplaceResponse,
    SessionExecuteCommandResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestSessions:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: Codeset) -> None:
        session = client.sessions.create(
            dataset="dataset",
            sample_id="sample_id",
        )
        assert_matches_type(SessionCreateResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_with_all_params(self, client: Codeset) -> None:
        session = client.sessions.create(
            dataset="dataset",
            sample_id="sample_id",
            ttl_minutes=0,
        )
        assert_matches_type(SessionCreateResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: Codeset) -> None:
        response = client.sessions.with_raw_response.create(
            dataset="dataset",
            sample_id="sample_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        session = response.parse()
        assert_matches_type(SessionCreateResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: Codeset) -> None:
        with client.sessions.with_streaming_response.create(
            dataset="dataset",
            sample_id="sample_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            session = response.parse()
            assert_matches_type(SessionCreateResponse, session, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: Codeset) -> None:
        session = client.sessions.retrieve(
            "session_id",
        )
        assert_matches_type(Session, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: Codeset) -> None:
        response = client.sessions.with_raw_response.retrieve(
            "session_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        session = response.parse()
        assert_matches_type(Session, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: Codeset) -> None:
        with client.sessions.with_streaming_response.retrieve(
            "session_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            session = response.parse()
            assert_matches_type(Session, session, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: Codeset) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            client.sessions.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Codeset) -> None:
        session = client.sessions.list()
        assert_matches_type(SessionListResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Codeset) -> None:
        response = client.sessions.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        session = response.parse()
        assert_matches_type(SessionListResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Codeset) -> None:
        with client.sessions.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            session = response.parse()
            assert_matches_type(SessionListResponse, session, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_close(self, client: Codeset) -> None:
        session = client.sessions.close(
            "session_id",
        )
        assert_matches_type(SessionCloseResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_close(self, client: Codeset) -> None:
        response = client.sessions.with_raw_response.close(
            "session_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        session = response.parse()
        assert_matches_type(SessionCloseResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_close(self, client: Codeset) -> None:
        with client.sessions.with_streaming_response.close(
            "session_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            session = response.parse()
            assert_matches_type(SessionCloseResponse, session, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_close(self, client: Codeset) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            client.sessions.with_raw_response.close(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_execute_command(self, client: Codeset) -> None:
        session = client.sessions.execute_command(
            session_id="session_id",
            command="command",
        )
        assert_matches_type(SessionExecuteCommandResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_execute_command_with_all_params(self, client: Codeset) -> None:
        session = client.sessions.execute_command(
            session_id="session_id",
            command="command",
            command_timeout=0,
        )
        assert_matches_type(SessionExecuteCommandResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_execute_command(self, client: Codeset) -> None:
        response = client.sessions.with_raw_response.execute_command(
            session_id="session_id",
            command="command",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        session = response.parse()
        assert_matches_type(SessionExecuteCommandResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_execute_command(self, client: Codeset) -> None:
        with client.sessions.with_streaming_response.execute_command(
            session_id="session_id",
            command="command",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            session = response.parse()
            assert_matches_type(SessionExecuteCommandResponse, session, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_execute_command(self, client: Codeset) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            client.sessions.with_raw_response.execute_command(
                session_id="",
                command="command",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_str_replace(self, client: Codeset) -> None:
        session = client.sessions.str_replace(
            session_id="session_id",
            file_path="file_path",
            str_to_insert="str_to_insert",
            str_to_replace="str_to_replace",
        )
        assert_matches_type(SessionStrReplaceResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_str_replace(self, client: Codeset) -> None:
        response = client.sessions.with_raw_response.str_replace(
            session_id="session_id",
            file_path="file_path",
            str_to_insert="str_to_insert",
            str_to_replace="str_to_replace",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        session = response.parse()
        assert_matches_type(SessionStrReplaceResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_str_replace(self, client: Codeset) -> None:
        with client.sessions.with_streaming_response.str_replace(
            session_id="session_id",
            file_path="file_path",
            str_to_insert="str_to_insert",
            str_to_replace="str_to_replace",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            session = response.parse()
            assert_matches_type(SessionStrReplaceResponse, session, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_str_replace(self, client: Codeset) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            client.sessions.with_raw_response.str_replace(
                session_id="",
                file_path="file_path",
                str_to_insert="str_to_insert",
                str_to_replace="str_to_replace",
            )


class TestAsyncSessions:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncCodeset) -> None:
        session = await async_client.sessions.create(
            dataset="dataset",
            sample_id="sample_id",
        )
        assert_matches_type(SessionCreateResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncCodeset) -> None:
        session = await async_client.sessions.create(
            dataset="dataset",
            sample_id="sample_id",
            ttl_minutes=0,
        )
        assert_matches_type(SessionCreateResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncCodeset) -> None:
        response = await async_client.sessions.with_raw_response.create(
            dataset="dataset",
            sample_id="sample_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        session = await response.parse()
        assert_matches_type(SessionCreateResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncCodeset) -> None:
        async with async_client.sessions.with_streaming_response.create(
            dataset="dataset",
            sample_id="sample_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            session = await response.parse()
            assert_matches_type(SessionCreateResponse, session, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncCodeset) -> None:
        session = await async_client.sessions.retrieve(
            "session_id",
        )
        assert_matches_type(Session, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncCodeset) -> None:
        response = await async_client.sessions.with_raw_response.retrieve(
            "session_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        session = await response.parse()
        assert_matches_type(Session, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncCodeset) -> None:
        async with async_client.sessions.with_streaming_response.retrieve(
            "session_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            session = await response.parse()
            assert_matches_type(Session, session, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncCodeset) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            await async_client.sessions.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncCodeset) -> None:
        session = await async_client.sessions.list()
        assert_matches_type(SessionListResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncCodeset) -> None:
        response = await async_client.sessions.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        session = await response.parse()
        assert_matches_type(SessionListResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncCodeset) -> None:
        async with async_client.sessions.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            session = await response.parse()
            assert_matches_type(SessionListResponse, session, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_close(self, async_client: AsyncCodeset) -> None:
        session = await async_client.sessions.close(
            "session_id",
        )
        assert_matches_type(SessionCloseResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_close(self, async_client: AsyncCodeset) -> None:
        response = await async_client.sessions.with_raw_response.close(
            "session_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        session = await response.parse()
        assert_matches_type(SessionCloseResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_close(self, async_client: AsyncCodeset) -> None:
        async with async_client.sessions.with_streaming_response.close(
            "session_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            session = await response.parse()
            assert_matches_type(SessionCloseResponse, session, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_close(self, async_client: AsyncCodeset) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            await async_client.sessions.with_raw_response.close(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_execute_command(self, async_client: AsyncCodeset) -> None:
        session = await async_client.sessions.execute_command(
            session_id="session_id",
            command="command",
        )
        assert_matches_type(SessionExecuteCommandResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_execute_command_with_all_params(self, async_client: AsyncCodeset) -> None:
        session = await async_client.sessions.execute_command(
            session_id="session_id",
            command="command",
            command_timeout=0,
        )
        assert_matches_type(SessionExecuteCommandResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_execute_command(self, async_client: AsyncCodeset) -> None:
        response = await async_client.sessions.with_raw_response.execute_command(
            session_id="session_id",
            command="command",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        session = await response.parse()
        assert_matches_type(SessionExecuteCommandResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_execute_command(self, async_client: AsyncCodeset) -> None:
        async with async_client.sessions.with_streaming_response.execute_command(
            session_id="session_id",
            command="command",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            session = await response.parse()
            assert_matches_type(SessionExecuteCommandResponse, session, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_execute_command(self, async_client: AsyncCodeset) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            await async_client.sessions.with_raw_response.execute_command(
                session_id="",
                command="command",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_str_replace(self, async_client: AsyncCodeset) -> None:
        session = await async_client.sessions.str_replace(
            session_id="session_id",
            file_path="file_path",
            str_to_insert="str_to_insert",
            str_to_replace="str_to_replace",
        )
        assert_matches_type(SessionStrReplaceResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_str_replace(self, async_client: AsyncCodeset) -> None:
        response = await async_client.sessions.with_raw_response.str_replace(
            session_id="session_id",
            file_path="file_path",
            str_to_insert="str_to_insert",
            str_to_replace="str_to_replace",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        session = await response.parse()
        assert_matches_type(SessionStrReplaceResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_str_replace(self, async_client: AsyncCodeset) -> None:
        async with async_client.sessions.with_streaming_response.str_replace(
            session_id="session_id",
            file_path="file_path",
            str_to_insert="str_to_insert",
            str_to_replace="str_to_replace",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            session = await response.parse()
            assert_matches_type(SessionStrReplaceResponse, session, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_str_replace(self, async_client: AsyncCodeset) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            await async_client.sessions.with_raw_response.str_replace(
                session_id="",
                file_path="file_path",
                str_to_insert="str_to_insert",
                str_to_replace="str_to_replace",
            )
