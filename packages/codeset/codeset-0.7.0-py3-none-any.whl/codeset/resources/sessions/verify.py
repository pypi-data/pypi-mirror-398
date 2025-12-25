# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import time

import httpx

from ..._types import Body, Query, Headers, NotGiven, not_given
from ..._utils import check_timeout, get_remaining_timeout
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..._base_client import make_request_options
from ...types.sessions.verify_start_response import VerifyStartResponse
from ...types.sessions.verify_status_response import VerifyStatusResponse

__all__ = ["VerifyResource", "AsyncVerifyResource"]


class VerifyResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> VerifyResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/codeset-ai/codeset-sdk#accessing-raw-response-data-eg-headers
        """
        return VerifyResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> VerifyResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/codeset-ai/codeset-sdk#with_streaming_response
        """
        return VerifyResourceWithStreamingResponse(self)

    def start(
        self,
        session_id: str,
        *,
        poll_interval: float = 3.0,
        wait_for_completion: bool = True,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> VerifyStatusResponse:
        """
        Start verification (oracle) in a session - async

        Args:
          poll_interval: Interval in seconds between polling attempts while waiting for verification to complete (default: 3.0).

          wait_for_completion: Whether to poll until the verification is completed (default: True). If False, returns the current status immediately after creation.

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
            f"/sessions/{session_id}/verify",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=get_remaining_timeout(timeout, start_time),
            ),
            cast_to=VerifyStartResponse,
        )

        check_timeout(timeout, start_time)
        status_response = self.status(
            response.job_id,
            session_id=session_id,
            extra_headers=extra_headers,
            extra_query=extra_query,
            extra_body=extra_body,
            timeout=get_remaining_timeout(timeout, start_time),
        )

        if not wait_for_completion:
            return status_response

        while status_response.status != "completed":
            if status_response.status in ("error", "cancelled"):
                return status_response
            check_timeout(timeout, start_time)
            self._sleep(poll_interval)
            check_timeout(timeout, start_time)
            status_response = self.status(
                response.job_id,
                session_id=session_id,
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=get_remaining_timeout(timeout, start_time),
            )

        return status_response

    def status(
        self,
        job_id: str,
        *,
        session_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> VerifyStatusResponse:
        """
        Get a verification job, including the result if it's completed

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        if not job_id:
            raise ValueError(f"Expected a non-empty value for `job_id` but received {job_id!r}")
        return self._get(
            f"/sessions/{session_id}/verify/{job_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=VerifyStatusResponse,
        )


class AsyncVerifyResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncVerifyResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/codeset-ai/codeset-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncVerifyResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncVerifyResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/codeset-ai/codeset-sdk#with_streaming_response
        """
        return AsyncVerifyResourceWithStreamingResponse(self)

    async def start(
        self,
        session_id: str,
        *,
        poll_interval: float = 3.0,
        wait_for_completion: bool = True,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> VerifyStatusResponse:
        """
        Start verification (oracle) in a session - async

        Args:
          poll_interval: Interval in seconds between polling attempts while waiting for verification to complete (default: 3.0).

          wait_for_completion: Whether to poll until the verification is completed (default: True). If False, returns the current status immediately after creation.

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
            f"/sessions/{session_id}/verify",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=get_remaining_timeout(timeout, start_time),
            ),
            cast_to=VerifyStartResponse,
        )

        check_timeout(timeout, start_time)
        status_response = await self.status(
            response.job_id,
            session_id=session_id,
            extra_headers=extra_headers,
            extra_query=extra_query,
            extra_body=extra_body,
            timeout=get_remaining_timeout(timeout, start_time),
        )

        if not wait_for_completion:
            return status_response

        while status_response.status != "completed":
            if status_response.status in ("error", "cancelled"):
                return status_response
            check_timeout(timeout, start_time)
            await self._sleep(poll_interval)
            check_timeout(timeout, start_time)
            status_response = await self.status(
                response.job_id,
                session_id=session_id,
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=get_remaining_timeout(timeout, start_time),
            )

        return status_response

    async def status(
        self,
        job_id: str,
        *,
        session_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> VerifyStatusResponse:
        """
        Get a verification job, including the result if it's completed

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        if not job_id:
            raise ValueError(f"Expected a non-empty value for `job_id` but received {job_id!r}")
        return await self._get(
            f"/sessions/{session_id}/verify/{job_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=VerifyStatusResponse,
        )


class VerifyResourceWithRawResponse:
    def __init__(self, verify: VerifyResource) -> None:
        self._verify = verify

        self.start = to_raw_response_wrapper(
            verify.start,
        )
        self.status = to_raw_response_wrapper(
            verify.status,
        )


class AsyncVerifyResourceWithRawResponse:
    def __init__(self, verify: AsyncVerifyResource) -> None:
        self._verify = verify

        self.start = async_to_raw_response_wrapper(
            verify.start,
        )
        self.status = async_to_raw_response_wrapper(
            verify.status,
        )


class VerifyResourceWithStreamingResponse:
    def __init__(self, verify: VerifyResource) -> None:
        self._verify = verify

        self.start = to_streamed_response_wrapper(
            verify.start,
        )
        self.status = to_streamed_response_wrapper(
            verify.status,
        )


class AsyncVerifyResourceWithStreamingResponse:
    def __init__(self, verify: AsyncVerifyResource) -> None:
        self._verify = verify

        self.start = async_to_streamed_response_wrapper(
            verify.start,
        )
        self.status = async_to_streamed_response_wrapper(
            verify.status,
        )
