# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from mobilerun import Mobilerun, AsyncMobilerun
from tests.utils import assert_matches_type
from mobilerun.types import (
    HookListResponse,
    HookUpdateResponse,
    HookPerformResponse,
    HookRetrieveResponse,
    HookSubscribeResponse,
    HookUnsubscribeResponse,
    HookGetSampleDataResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestHooks:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: Mobilerun) -> None:
        hook = client.hooks.retrieve(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(HookRetrieveResponse, hook, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: Mobilerun) -> None:
        response = client.hooks.with_raw_response.retrieve(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        hook = response.parse()
        assert_matches_type(HookRetrieveResponse, hook, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: Mobilerun) -> None:
        with client.hooks.with_streaming_response.retrieve(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            hook = response.parse()
            assert_matches_type(HookRetrieveResponse, hook, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: Mobilerun) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `hook_id` but received ''"):
            client.hooks.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update(self, client: Mobilerun) -> None:
        hook = client.hooks.update(
            hook_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(HookUpdateResponse, hook, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_with_all_params(self, client: Mobilerun) -> None:
        hook = client.hooks.update(
            hook_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            events=["string"],
            state="state",
        )
        assert_matches_type(HookUpdateResponse, hook, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update(self, client: Mobilerun) -> None:
        response = client.hooks.with_raw_response.update(
            hook_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        hook = response.parse()
        assert_matches_type(HookUpdateResponse, hook, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update(self, client: Mobilerun) -> None:
        with client.hooks.with_streaming_response.update(
            hook_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            hook = response.parse()
            assert_matches_type(HookUpdateResponse, hook, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_update(self, client: Mobilerun) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `hook_id` but received ''"):
            client.hooks.with_raw_response.update(
                hook_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Mobilerun) -> None:
        hook = client.hooks.list()
        assert_matches_type(HookListResponse, hook, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: Mobilerun) -> None:
        hook = client.hooks.list(
            order_by="orderBy",
            order_by_direction="asc",
            page=1,
            page_size=1,
        )
        assert_matches_type(HookListResponse, hook, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Mobilerun) -> None:
        response = client.hooks.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        hook = response.parse()
        assert_matches_type(HookListResponse, hook, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Mobilerun) -> None:
        with client.hooks.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            hook = response.parse()
            assert_matches_type(HookListResponse, hook, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_sample_data(self, client: Mobilerun) -> None:
        hook = client.hooks.get_sample_data()
        assert_matches_type(HookGetSampleDataResponse, hook, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_get_sample_data(self, client: Mobilerun) -> None:
        response = client.hooks.with_raw_response.get_sample_data()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        hook = response.parse()
        assert_matches_type(HookGetSampleDataResponse, hook, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_get_sample_data(self, client: Mobilerun) -> None:
        with client.hooks.with_streaming_response.get_sample_data() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            hook = response.parse()
            assert_matches_type(HookGetSampleDataResponse, hook, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_perform(self, client: Mobilerun) -> None:
        hook = client.hooks.perform()
        assert_matches_type(HookPerformResponse, hook, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_perform(self, client: Mobilerun) -> None:
        response = client.hooks.with_raw_response.perform()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        hook = response.parse()
        assert_matches_type(HookPerformResponse, hook, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_perform(self, client: Mobilerun) -> None:
        with client.hooks.with_streaming_response.perform() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            hook = response.parse()
            assert_matches_type(HookPerformResponse, hook, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_subscribe(self, client: Mobilerun) -> None:
        hook = client.hooks.subscribe(
            target_url="https://example.com",
        )
        assert_matches_type(HookSubscribeResponse, hook, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_subscribe_with_all_params(self, client: Mobilerun) -> None:
        hook = client.hooks.subscribe(
            target_url="https://example.com",
            events=["string"],
            service="service",
        )
        assert_matches_type(HookSubscribeResponse, hook, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_subscribe(self, client: Mobilerun) -> None:
        response = client.hooks.with_raw_response.subscribe(
            target_url="https://example.com",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        hook = response.parse()
        assert_matches_type(HookSubscribeResponse, hook, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_subscribe(self, client: Mobilerun) -> None:
        with client.hooks.with_streaming_response.subscribe(
            target_url="https://example.com",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            hook = response.parse()
            assert_matches_type(HookSubscribeResponse, hook, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_unsubscribe(self, client: Mobilerun) -> None:
        hook = client.hooks.unsubscribe(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(HookUnsubscribeResponse, hook, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_unsubscribe(self, client: Mobilerun) -> None:
        response = client.hooks.with_raw_response.unsubscribe(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        hook = response.parse()
        assert_matches_type(HookUnsubscribeResponse, hook, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_unsubscribe(self, client: Mobilerun) -> None:
        with client.hooks.with_streaming_response.unsubscribe(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            hook = response.parse()
            assert_matches_type(HookUnsubscribeResponse, hook, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_unsubscribe(self, client: Mobilerun) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `hook_id` but received ''"):
            client.hooks.with_raw_response.unsubscribe(
                "",
            )


class TestAsyncHooks:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncMobilerun) -> None:
        hook = await async_client.hooks.retrieve(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(HookRetrieveResponse, hook, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncMobilerun) -> None:
        response = await async_client.hooks.with_raw_response.retrieve(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        hook = await response.parse()
        assert_matches_type(HookRetrieveResponse, hook, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncMobilerun) -> None:
        async with async_client.hooks.with_streaming_response.retrieve(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            hook = await response.parse()
            assert_matches_type(HookRetrieveResponse, hook, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncMobilerun) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `hook_id` but received ''"):
            await async_client.hooks.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update(self, async_client: AsyncMobilerun) -> None:
        hook = await async_client.hooks.update(
            hook_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(HookUpdateResponse, hook, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncMobilerun) -> None:
        hook = await async_client.hooks.update(
            hook_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            events=["string"],
            state="state",
        )
        assert_matches_type(HookUpdateResponse, hook, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update(self, async_client: AsyncMobilerun) -> None:
        response = await async_client.hooks.with_raw_response.update(
            hook_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        hook = await response.parse()
        assert_matches_type(HookUpdateResponse, hook, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncMobilerun) -> None:
        async with async_client.hooks.with_streaming_response.update(
            hook_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            hook = await response.parse()
            assert_matches_type(HookUpdateResponse, hook, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_update(self, async_client: AsyncMobilerun) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `hook_id` but received ''"):
            await async_client.hooks.with_raw_response.update(
                hook_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncMobilerun) -> None:
        hook = await async_client.hooks.list()
        assert_matches_type(HookListResponse, hook, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncMobilerun) -> None:
        hook = await async_client.hooks.list(
            order_by="orderBy",
            order_by_direction="asc",
            page=1,
            page_size=1,
        )
        assert_matches_type(HookListResponse, hook, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncMobilerun) -> None:
        response = await async_client.hooks.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        hook = await response.parse()
        assert_matches_type(HookListResponse, hook, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncMobilerun) -> None:
        async with async_client.hooks.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            hook = await response.parse()
            assert_matches_type(HookListResponse, hook, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_sample_data(self, async_client: AsyncMobilerun) -> None:
        hook = await async_client.hooks.get_sample_data()
        assert_matches_type(HookGetSampleDataResponse, hook, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_get_sample_data(self, async_client: AsyncMobilerun) -> None:
        response = await async_client.hooks.with_raw_response.get_sample_data()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        hook = await response.parse()
        assert_matches_type(HookGetSampleDataResponse, hook, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_get_sample_data(self, async_client: AsyncMobilerun) -> None:
        async with async_client.hooks.with_streaming_response.get_sample_data() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            hook = await response.parse()
            assert_matches_type(HookGetSampleDataResponse, hook, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_perform(self, async_client: AsyncMobilerun) -> None:
        hook = await async_client.hooks.perform()
        assert_matches_type(HookPerformResponse, hook, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_perform(self, async_client: AsyncMobilerun) -> None:
        response = await async_client.hooks.with_raw_response.perform()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        hook = await response.parse()
        assert_matches_type(HookPerformResponse, hook, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_perform(self, async_client: AsyncMobilerun) -> None:
        async with async_client.hooks.with_streaming_response.perform() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            hook = await response.parse()
            assert_matches_type(HookPerformResponse, hook, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_subscribe(self, async_client: AsyncMobilerun) -> None:
        hook = await async_client.hooks.subscribe(
            target_url="https://example.com",
        )
        assert_matches_type(HookSubscribeResponse, hook, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_subscribe_with_all_params(self, async_client: AsyncMobilerun) -> None:
        hook = await async_client.hooks.subscribe(
            target_url="https://example.com",
            events=["string"],
            service="service",
        )
        assert_matches_type(HookSubscribeResponse, hook, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_subscribe(self, async_client: AsyncMobilerun) -> None:
        response = await async_client.hooks.with_raw_response.subscribe(
            target_url="https://example.com",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        hook = await response.parse()
        assert_matches_type(HookSubscribeResponse, hook, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_subscribe(self, async_client: AsyncMobilerun) -> None:
        async with async_client.hooks.with_streaming_response.subscribe(
            target_url="https://example.com",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            hook = await response.parse()
            assert_matches_type(HookSubscribeResponse, hook, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_unsubscribe(self, async_client: AsyncMobilerun) -> None:
        hook = await async_client.hooks.unsubscribe(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(HookUnsubscribeResponse, hook, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_unsubscribe(self, async_client: AsyncMobilerun) -> None:
        response = await async_client.hooks.with_raw_response.unsubscribe(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        hook = await response.parse()
        assert_matches_type(HookUnsubscribeResponse, hook, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_unsubscribe(self, async_client: AsyncMobilerun) -> None:
        async with async_client.hooks.with_streaming_response.unsubscribe(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            hook = await response.parse()
            assert_matches_type(HookUnsubscribeResponse, hook, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_unsubscribe(self, async_client: AsyncMobilerun) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `hook_id` but received ''"):
            await async_client.hooks.with_raw_response.unsubscribe(
                "",
            )
