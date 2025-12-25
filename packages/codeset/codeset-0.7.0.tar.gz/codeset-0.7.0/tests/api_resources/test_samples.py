# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from codeset import Codeset, AsyncCodeset
from tests.utils import assert_matches_type
from codeset.types import SampleListResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestSamples:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Codeset) -> None:
        sample = client.samples.list()
        assert_matches_type(SampleListResponse, sample, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: Codeset) -> None:
        sample = client.samples.list(
            dataset="dataset",
            page=1,
            page_size=1,
            search="search",
        )
        assert_matches_type(SampleListResponse, sample, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Codeset) -> None:
        response = client.samples.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sample = response.parse()
        assert_matches_type(SampleListResponse, sample, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Codeset) -> None:
        with client.samples.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sample = response.parse()
            assert_matches_type(SampleListResponse, sample, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_download(self, client: Codeset) -> None:
        sample = client.samples.download(
            sample_id="sample_id",
            dataset="dataset",
        )
        assert_matches_type(object, sample, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_download_with_all_params(self, client: Codeset) -> None:
        sample = client.samples.download(
            sample_id="sample_id",
            dataset="dataset",
            version=0,
        )
        assert_matches_type(object, sample, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_download(self, client: Codeset) -> None:
        response = client.samples.with_raw_response.download(
            sample_id="sample_id",
            dataset="dataset",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sample = response.parse()
        assert_matches_type(object, sample, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_download(self, client: Codeset) -> None:
        with client.samples.with_streaming_response.download(
            sample_id="sample_id",
            dataset="dataset",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sample = response.parse()
            assert_matches_type(object, sample, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_download(self, client: Codeset) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `dataset` but received ''"):
            client.samples.with_raw_response.download(
                sample_id="sample_id",
                dataset="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `sample_id` but received ''"):
            client.samples.with_raw_response.download(
                sample_id="",
                dataset="dataset",
            )


class TestAsyncSamples:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncCodeset) -> None:
        sample = await async_client.samples.list()
        assert_matches_type(SampleListResponse, sample, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncCodeset) -> None:
        sample = await async_client.samples.list(
            dataset="dataset",
            page=1,
            page_size=1,
            search="search",
        )
        assert_matches_type(SampleListResponse, sample, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncCodeset) -> None:
        response = await async_client.samples.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sample = await response.parse()
        assert_matches_type(SampleListResponse, sample, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncCodeset) -> None:
        async with async_client.samples.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sample = await response.parse()
            assert_matches_type(SampleListResponse, sample, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_download(self, async_client: AsyncCodeset) -> None:
        sample = await async_client.samples.download(
            sample_id="sample_id",
            dataset="dataset",
        )
        assert_matches_type(object, sample, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_download_with_all_params(self, async_client: AsyncCodeset) -> None:
        sample = await async_client.samples.download(
            sample_id="sample_id",
            dataset="dataset",
            version=0,
        )
        assert_matches_type(object, sample, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_download(self, async_client: AsyncCodeset) -> None:
        response = await async_client.samples.with_raw_response.download(
            sample_id="sample_id",
            dataset="dataset",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sample = await response.parse()
        assert_matches_type(object, sample, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_download(self, async_client: AsyncCodeset) -> None:
        async with async_client.samples.with_streaming_response.download(
            sample_id="sample_id",
            dataset="dataset",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sample = await response.parse()
            assert_matches_type(object, sample, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_download(self, async_client: AsyncCodeset) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `dataset` but received ''"):
            await async_client.samples.with_raw_response.download(
                sample_id="sample_id",
                dataset="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `sample_id` but received ''"):
            await async_client.samples.with_raw_response.download(
                sample_id="",
                dataset="dataset",
            )
