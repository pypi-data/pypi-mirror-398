# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import time

import httpx

from .verify import (
    VerifyResource,
    AsyncVerifyResource,
    VerifyResourceWithRawResponse,
    AsyncVerifyResourceWithRawResponse,
    VerifyResourceWithStreamingResponse,
    AsyncVerifyResourceWithStreamingResponse,
)
from ...types import session_create_params, session_str_replace_params, session_execute_command_params
from ..._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from ..._utils import check_timeout, maybe_transform, async_maybe_transform, get_remaining_timeout
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..._exceptions import CodesetError
from ..._base_client import make_request_options
from ...types.session import Session
from ...types.interaction import Interaction
from ...types.session_list_response import SessionListResponse
from ...types.session_close_response import SessionCloseResponse
from ...types.session_create_response import SessionCreateResponse
from ...types.session_str_replace_response import SessionStrReplaceResponse
from ...types.session_execute_command_response import SessionExecuteCommandResponse

__all__ = ["SessionsResource", "AsyncSessionsResource"]


class SessionsResource(SyncAPIResource):
    @cached_property
    def verify(self) -> VerifyResource:
        return VerifyResource(self._client)

    @cached_property
    def with_raw_response(self) -> SessionsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/codeset-ai/codeset-sdk#accessing-raw-response-data-eg-headers
        """
        return SessionsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> SessionsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/codeset-ai/codeset-sdk#with_streaming_response
        """
        return SessionsResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        dataset: str,
        sample_id: str,
        ttl_minutes: int | Omit = omit,
        poll_interval: float = 3.0,
        wait_for_ready: bool = True,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Session:
        """
        Create a new session

        Args:
          dataset: Dataset name for the sample.

          sample_id: Identifier of the sample to use for this session.

          ttl_minutes: Time to live for the session in minutes (default: 30).

          poll_interval: Interval in seconds between polling attempts while waiting for session to be ready (default: 3.0).

          wait_for_ready: Whether to poll until the session is ready (default: True). If False, returns the session immediately after creation.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        start_time = time.time()

        check_timeout(timeout, start_time)
        response = self._post(
            "/sessions",
            body=maybe_transform(
                {
                    "dataset": dataset,
                    "sample_id": sample_id,
                    "ttl_minutes": ttl_minutes,
                },
                session_create_params.SessionCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=get_remaining_timeout(timeout, start_time),
            ),
            cast_to=SessionCreateResponse,
        )

        check_timeout(timeout, start_time)
        session = self.retrieve(
            response.session_id,
            extra_headers=extra_headers,
            extra_query=extra_query,
            extra_body=extra_body,
            timeout=get_remaining_timeout(timeout, start_time),
        )

        if not wait_for_ready:
            return session

        while session.status != "ready":
            if session.status in ("error", "closed"):
                return session
            check_timeout(timeout, start_time)
            self._sleep(poll_interval)
            check_timeout(timeout, start_time)
            session = self.retrieve(
                response.session_id,
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=get_remaining_timeout(timeout, start_time),
            )

        return session

    def retrieve(
        self,
        session_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Session:
        """
        Get session details

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        return self._get(
            f"/sessions/{session_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Session,
        )

    def list(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SessionListResponse:
        """List environment sessions"""
        return self._get(
            "/sessions",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SessionListResponse,
        )

    def close(
        self,
        session_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SessionCloseResponse:
        """
        Close/delete an environment session

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        return self._delete(
            f"/sessions/{session_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SessionCloseResponse,
        )

    def execute_command(
        self,
        session_id: str,
        *,
        command: str,
        command_timeout: int | Omit = omit,
        poll_interval: float = 3.0,
        wait_for_completion: bool = True,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Interaction:
        """
        Start command execution in an environment (async)

        Args:
          command: The bash command to execute.

          command_timeout: Timeout for command execution in seconds (default: 300).

          poll_interval: Interval in seconds between polling attempts while waiting for command to complete (default: 3.0).

          wait_for_completion: Whether to poll until the command is completed (default: True). If False, returns the interaction immediately after creation.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        start_time = time.time()

        check_timeout(timeout, start_time)
        response = self._post(
            f"/sessions/{session_id}/exec",
            body=maybe_transform(
                {
                    "command": command,
                    "command_timeout": command_timeout,
                },
                session_execute_command_params.SessionExecuteCommandParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=get_remaining_timeout(timeout, start_time),
            ),
            cast_to=SessionExecuteCommandResponse,
        )

        interaction_id = response.interaction_id

        check_timeout(timeout, start_time)
        interaction = self.get_interaction(
            session_id,
            interaction_id,
            extra_headers=extra_headers,
            extra_query=extra_query,
            extra_body=extra_body,
            timeout=get_remaining_timeout(timeout, start_time),
        )

        if not wait_for_completion:
            return interaction

        while interaction.exit_code is None:
            check_timeout(timeout, start_time)
            self._sleep(poll_interval)
            check_timeout(timeout, start_time)
            interaction = self.get_interaction(
                session_id,
                interaction_id,
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=get_remaining_timeout(timeout, start_time),
            )

        if interaction.exit_code == -1000:
            raise CodesetError(interaction.message or "Command execution failed")

        return interaction

    def get_interaction(
        self,
        session_id: str,
        interaction_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Interaction:
        """
        Get interaction details by ID

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        if not interaction_id:
            raise ValueError(f"Expected a non-empty value for `interaction_id` but received {interaction_id!r}")
        return self._get(
            f"/sessions/{session_id}/interactions/{interaction_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Interaction,
        )

    def str_replace(
        self,
        session_id: str,
        *,
        file_path: str,
        str_to_insert: str,
        str_to_replace: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SessionStrReplaceResponse:
        """
        Replace a string in a file within the session environment

        Args:
          file_path: Path to the file where replacement should be performed.

          str_to_insert: String to insert as replacement.

          str_to_replace: String to be replaced.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        return self._post(
            f"/sessions/{session_id}/str_replace",
            body=maybe_transform(
                {
                    "file_path": file_path,
                    "str_to_insert": str_to_insert,
                    "str_to_replace": str_to_replace,
                },
                session_str_replace_params.SessionStrReplaceParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SessionStrReplaceResponse,
        )


class AsyncSessionsResource(AsyncAPIResource):
    @cached_property
    def verify(self) -> AsyncVerifyResource:
        return AsyncVerifyResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncSessionsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/codeset-ai/codeset-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncSessionsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncSessionsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/codeset-ai/codeset-sdk#with_streaming_response
        """
        return AsyncSessionsResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        dataset: str,
        sample_id: str,
        ttl_minutes: int | Omit = omit,
        poll_interval: float = 3.0,
        wait_for_ready: bool = True,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Session:
        """
        Create a new session

        Args:
          dataset: Dataset name for the sample.

          sample_id: Identifier of the sample to use for this session.

          ttl_minutes: Time to live for the session in minutes (default: 30).

          poll_interval: Interval in seconds between polling attempts while waiting for session to be ready (default: 3.0).

          wait_for_ready: Whether to poll until the session is ready (default: True). If False, returns the session immediately after creation.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        start_time = time.time()

        check_timeout(timeout, start_time)
        response = await self._post(
            "/sessions",
            body=await async_maybe_transform(
                {
                    "dataset": dataset,
                    "sample_id": sample_id,
                    "ttl_minutes": ttl_minutes,
                },
                session_create_params.SessionCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=get_remaining_timeout(timeout, start_time),
            ),
            cast_to=SessionCreateResponse,
        )

        check_timeout(timeout, start_time)
        session = await self.retrieve(
            response.session_id,
            extra_headers=extra_headers,
            extra_query=extra_query,
            extra_body=extra_body,
            timeout=get_remaining_timeout(timeout, start_time),
        )

        if not wait_for_ready:
            return session

        while session.status != "ready":
            if session.status in ("error", "closed"):
                return session
            check_timeout(timeout, start_time)
            await self._sleep(poll_interval)
            check_timeout(timeout, start_time)
            session = await self.retrieve(
                response.session_id,
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=get_remaining_timeout(timeout, start_time),
            )

        return session

    async def retrieve(
        self,
        session_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Session:
        """
        Get session details

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        return await self._get(
            f"/sessions/{session_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Session,
        )

    async def list(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SessionListResponse:
        """List environment sessions"""
        return await self._get(
            "/sessions",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SessionListResponse,
        )

    async def close(
        self,
        session_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SessionCloseResponse:
        """
        Close/delete an environment session

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        return await self._delete(
            f"/sessions/{session_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SessionCloseResponse,
        )

    async def execute_command(
        self,
        session_id: str,
        *,
        command: str,
        command_timeout: int | Omit = omit,
        poll_interval: float = 3.0,
        wait_for_completion: bool = True,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Interaction:
        """
        Start command execution in an environment (async)

        Args:
          command: The bash command to execute.

          command_timeout: Timeout for command execution in seconds (default: 300).

          poll_interval: Interval in seconds between polling attempts while waiting for command to complete (default: 3.0).

          wait_for_completion: Whether to poll until the command is completed (default: True). If False, returns the interaction immediately after creation.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        start_time = time.time()

        check_timeout(timeout, start_time)
        response = await self._post(
            f"/sessions/{session_id}/exec",
            body=await async_maybe_transform(
                {
                    "command": command,
                    "command_timeout": command_timeout,
                },
                session_execute_command_params.SessionExecuteCommandParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=get_remaining_timeout(timeout, start_time),
            ),
            cast_to=SessionExecuteCommandResponse,
        )

        interaction_id = response.interaction_id

        check_timeout(timeout, start_time)
        interaction = await self.get_interaction(
            session_id,
            interaction_id,
            extra_headers=extra_headers,
            extra_query=extra_query,
            extra_body=extra_body,
            timeout=get_remaining_timeout(timeout, start_time),
        )

        if not wait_for_completion:
            return interaction

        while interaction.exit_code is None:
            check_timeout(timeout, start_time)
            await self._sleep(poll_interval)
            check_timeout(timeout, start_time)
            interaction = await self.get_interaction(
                session_id,
                interaction_id,
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=get_remaining_timeout(timeout, start_time),
            )

        if interaction.exit_code == -1000:
            raise CodesetError(interaction.message or "Command execution failed")

        return interaction

    async def get_interaction(
        self,
        session_id: str,
        interaction_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Interaction:
        """
        Get interaction details by ID

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        if not interaction_id:
            raise ValueError(f"Expected a non-empty value for `interaction_id` but received {interaction_id!r}")
        return await self._get(
            f"/sessions/{session_id}/interactions/{interaction_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Interaction,
        )

    async def str_replace(
        self,
        session_id: str,
        *,
        file_path: str,
        str_to_insert: str,
        str_to_replace: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SessionStrReplaceResponse:
        """
        Replace a string in a file within the session environment

        Args:
          file_path: Path to the file where replacement should be performed.

          str_to_insert: String to insert as replacement.

          str_to_replace: String to be replaced.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        return await self._post(
            f"/sessions/{session_id}/str_replace",
            body=await async_maybe_transform(
                {
                    "file_path": file_path,
                    "str_to_insert": str_to_insert,
                    "str_to_replace": str_to_replace,
                },
                session_str_replace_params.SessionStrReplaceParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SessionStrReplaceResponse,
        )


class SessionsResourceWithRawResponse:
    def __init__(self, sessions: SessionsResource) -> None:
        self._sessions = sessions

        self.create = to_raw_response_wrapper(
            sessions.create,
        )
        self.retrieve = to_raw_response_wrapper(
            sessions.retrieve,
        )
        self.list = to_raw_response_wrapper(
            sessions.list,
        )
        self.close = to_raw_response_wrapper(
            sessions.close,
        )
        self.execute_command = to_raw_response_wrapper(
            sessions.execute_command,
        )
        self.str_replace = to_raw_response_wrapper(
            sessions.str_replace,
        )

    @cached_property
    def verify(self) -> VerifyResourceWithRawResponse:
        return VerifyResourceWithRawResponse(self._sessions.verify)


class AsyncSessionsResourceWithRawResponse:
    def __init__(self, sessions: AsyncSessionsResource) -> None:
        self._sessions = sessions

        self.create = async_to_raw_response_wrapper(
            sessions.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            sessions.retrieve,
        )
        self.list = async_to_raw_response_wrapper(
            sessions.list,
        )
        self.close = async_to_raw_response_wrapper(
            sessions.close,
        )
        self.execute_command = async_to_raw_response_wrapper(
            sessions.execute_command,
        )
        self.str_replace = async_to_raw_response_wrapper(
            sessions.str_replace,
        )

    @cached_property
    def verify(self) -> AsyncVerifyResourceWithRawResponse:
        return AsyncVerifyResourceWithRawResponse(self._sessions.verify)


class SessionsResourceWithStreamingResponse:
    def __init__(self, sessions: SessionsResource) -> None:
        self._sessions = sessions

        self.create = to_streamed_response_wrapper(
            sessions.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            sessions.retrieve,
        )
        self.list = to_streamed_response_wrapper(
            sessions.list,
        )
        self.close = to_streamed_response_wrapper(
            sessions.close,
        )
        self.execute_command = to_streamed_response_wrapper(
            sessions.execute_command,
        )
        self.str_replace = to_streamed_response_wrapper(
            sessions.str_replace,
        )

    @cached_property
    def verify(self) -> VerifyResourceWithStreamingResponse:
        return VerifyResourceWithStreamingResponse(self._sessions.verify)


class AsyncSessionsResourceWithStreamingResponse:
    def __init__(self, sessions: AsyncSessionsResource) -> None:
        self._sessions = sessions

        self.create = async_to_streamed_response_wrapper(
            sessions.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            sessions.retrieve,
        )
        self.list = async_to_streamed_response_wrapper(
            sessions.list,
        )
        self.close = async_to_streamed_response_wrapper(
            sessions.close,
        )
        self.execute_command = async_to_streamed_response_wrapper(
            sessions.execute_command,
        )
        self.str_replace = async_to_streamed_response_wrapper(
            sessions.str_replace,
        )

    @cached_property
    def verify(self) -> AsyncVerifyResourceWithStreamingResponse:
        return AsyncVerifyResourceWithStreamingResponse(self._sessions.verify)
