# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional

import httpx

from ..types import sample_list_params, sample_download_params
from .._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from .._utils import maybe_transform, async_maybe_transform
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .._base_client import make_request_options
from ..types.sample_list_response import SampleListResponse

__all__ = ["SamplesResource", "AsyncSamplesResource"]


class SamplesResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> SamplesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/codeset-ai/codeset-sdk#accessing-raw-response-data-eg-headers
        """
        return SamplesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> SamplesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/codeset-ai/codeset-sdk#with_streaming_response
        """
        return SamplesResourceWithStreamingResponse(self)

    def list(
        self,
        *,
        dataset: Optional[str] | Omit = omit,
        page: Optional[int] | Omit = omit,
        page_size: Optional[int] | Omit = omit,
        search: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SampleListResponse:
        """
        List available samples with optional pagination, optionally filtered by dataset

        Args:
          dataset: Filter samples by dataset name

          page: Page number (1-based). If not provided, returns all samples

          page_size: Number of samples per page (max 100). If not provided, returns all samples

          search: Search for samples by instance_id

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/samples",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "dataset": dataset,
                        "page": page,
                        "page_size": page_size,
                        "search": search,
                    },
                    sample_list_params.SampleListParams,
                ),
            ),
            cast_to=SampleListResponse,
        )

    def download(
        self,
        sample_id: str,
        *,
        dataset: str,
        version: Optional[int] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """
        Download the gz file for a specific sample

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not dataset:
            raise ValueError(f"Expected a non-empty value for `dataset` but received {dataset!r}")
        if not sample_id:
            raise ValueError(f"Expected a non-empty value for `sample_id` but received {sample_id!r}")
        return self._get(
            f"/samples/{dataset}/{sample_id}/download",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform({"version": version}, sample_download_params.SampleDownloadParams),
            ),
            cast_to=object,
        )


class AsyncSamplesResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncSamplesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/codeset-ai/codeset-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncSamplesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncSamplesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/codeset-ai/codeset-sdk#with_streaming_response
        """
        return AsyncSamplesResourceWithStreamingResponse(self)

    async def list(
        self,
        *,
        dataset: Optional[str] | Omit = omit,
        page: Optional[int] | Omit = omit,
        page_size: Optional[int] | Omit = omit,
        search: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SampleListResponse:
        """
        List available samples with optional pagination, optionally filtered by dataset

        Args:
          dataset: Filter samples by dataset name

          page: Page number (1-based). If not provided, returns all samples

          page_size: Number of samples per page (max 100). If not provided, returns all samples

          search: Search for samples by instance_id

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/samples",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "dataset": dataset,
                        "page": page,
                        "page_size": page_size,
                        "search": search,
                    },
                    sample_list_params.SampleListParams,
                ),
            ),
            cast_to=SampleListResponse,
        )

    async def download(
        self,
        sample_id: str,
        *,
        dataset: str,
        version: Optional[int] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """
        Download the gz file for a specific sample

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not dataset:
            raise ValueError(f"Expected a non-empty value for `dataset` but received {dataset!r}")
        if not sample_id:
            raise ValueError(f"Expected a non-empty value for `sample_id` but received {sample_id!r}")
        return await self._get(
            f"/samples/{dataset}/{sample_id}/download",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform({"version": version}, sample_download_params.SampleDownloadParams),
            ),
            cast_to=object,
        )


class SamplesResourceWithRawResponse:
    def __init__(self, samples: SamplesResource) -> None:
        self._samples = samples

        self.list = to_raw_response_wrapper(
            samples.list,
        )
        self.download = to_raw_response_wrapper(
            samples.download,
        )


class AsyncSamplesResourceWithRawResponse:
    def __init__(self, samples: AsyncSamplesResource) -> None:
        self._samples = samples

        self.list = async_to_raw_response_wrapper(
            samples.list,
        )
        self.download = async_to_raw_response_wrapper(
            samples.download,
        )


class SamplesResourceWithStreamingResponse:
    def __init__(self, samples: SamplesResource) -> None:
        self._samples = samples

        self.list = to_streamed_response_wrapper(
            samples.list,
        )
        self.download = to_streamed_response_wrapper(
            samples.download,
        )


class AsyncSamplesResourceWithStreamingResponse:
    def __init__(self, samples: AsyncSamplesResource) -> None:
        self._samples = samples

        self.list = async_to_streamed_response_wrapper(
            samples.list,
        )
        self.download = async_to_streamed_response_wrapper(
            samples.download,
        )
