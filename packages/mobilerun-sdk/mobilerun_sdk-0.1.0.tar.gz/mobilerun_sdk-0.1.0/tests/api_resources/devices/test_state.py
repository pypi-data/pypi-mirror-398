# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from mobilerun import Mobilerun, AsyncMobilerun
from tests.utils import assert_matches_type

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestState:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_screenshot(self, client: Mobilerun) -> None:
        state = client.devices.state.screenshot(
            device_id="deviceId",
        )
        assert_matches_type(str, state, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_screenshot_with_all_params(self, client: Mobilerun) -> None:
        state = client.devices.state.screenshot(
            device_id="deviceId",
            hide_overlay=True,
            x_device_display_id=0,
        )
        assert_matches_type(str, state, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_screenshot(self, client: Mobilerun) -> None:
        response = client.devices.state.with_raw_response.screenshot(
            device_id="deviceId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        state = response.parse()
        assert_matches_type(str, state, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_screenshot(self, client: Mobilerun) -> None:
        with client.devices.state.with_streaming_response.screenshot(
            device_id="deviceId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            state = response.parse()
            assert_matches_type(str, state, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_screenshot(self, client: Mobilerun) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `device_id` but received ''"):
            client.devices.state.with_raw_response.screenshot(
                device_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_time(self, client: Mobilerun) -> None:
        state = client.devices.state.time(
            device_id="deviceId",
        )
        assert_matches_type(str, state, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_time_with_all_params(self, client: Mobilerun) -> None:
        state = client.devices.state.time(
            device_id="deviceId",
            x_device_display_id=0,
        )
        assert_matches_type(str, state, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_time(self, client: Mobilerun) -> None:
        response = client.devices.state.with_raw_response.time(
            device_id="deviceId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        state = response.parse()
        assert_matches_type(str, state, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_time(self, client: Mobilerun) -> None:
        with client.devices.state.with_streaming_response.time(
            device_id="deviceId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            state = response.parse()
            assert_matches_type(str, state, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_time(self, client: Mobilerun) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `device_id` but received ''"):
            client.devices.state.with_raw_response.time(
                device_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_ui(self, client: Mobilerun) -> None:
        state = client.devices.state.ui(
            device_id="deviceId",
        )
        assert_matches_type(object, state, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_ui_with_all_params(self, client: Mobilerun) -> None:
        state = client.devices.state.ui(
            device_id="deviceId",
            filter=True,
            x_device_display_id=0,
        )
        assert_matches_type(object, state, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_ui(self, client: Mobilerun) -> None:
        response = client.devices.state.with_raw_response.ui(
            device_id="deviceId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        state = response.parse()
        assert_matches_type(object, state, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_ui(self, client: Mobilerun) -> None:
        with client.devices.state.with_streaming_response.ui(
            device_id="deviceId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            state = response.parse()
            assert_matches_type(object, state, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_ui(self, client: Mobilerun) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `device_id` but received ''"):
            client.devices.state.with_raw_response.ui(
                device_id="",
            )


class TestAsyncState:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_screenshot(self, async_client: AsyncMobilerun) -> None:
        state = await async_client.devices.state.screenshot(
            device_id="deviceId",
        )
        assert_matches_type(str, state, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_screenshot_with_all_params(self, async_client: AsyncMobilerun) -> None:
        state = await async_client.devices.state.screenshot(
            device_id="deviceId",
            hide_overlay=True,
            x_device_display_id=0,
        )
        assert_matches_type(str, state, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_screenshot(self, async_client: AsyncMobilerun) -> None:
        response = await async_client.devices.state.with_raw_response.screenshot(
            device_id="deviceId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        state = await response.parse()
        assert_matches_type(str, state, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_screenshot(self, async_client: AsyncMobilerun) -> None:
        async with async_client.devices.state.with_streaming_response.screenshot(
            device_id="deviceId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            state = await response.parse()
            assert_matches_type(str, state, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_screenshot(self, async_client: AsyncMobilerun) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `device_id` but received ''"):
            await async_client.devices.state.with_raw_response.screenshot(
                device_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_time(self, async_client: AsyncMobilerun) -> None:
        state = await async_client.devices.state.time(
            device_id="deviceId",
        )
        assert_matches_type(str, state, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_time_with_all_params(self, async_client: AsyncMobilerun) -> None:
        state = await async_client.devices.state.time(
            device_id="deviceId",
            x_device_display_id=0,
        )
        assert_matches_type(str, state, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_time(self, async_client: AsyncMobilerun) -> None:
        response = await async_client.devices.state.with_raw_response.time(
            device_id="deviceId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        state = await response.parse()
        assert_matches_type(str, state, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_time(self, async_client: AsyncMobilerun) -> None:
        async with async_client.devices.state.with_streaming_response.time(
            device_id="deviceId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            state = await response.parse()
            assert_matches_type(str, state, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_time(self, async_client: AsyncMobilerun) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `device_id` but received ''"):
            await async_client.devices.state.with_raw_response.time(
                device_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_ui(self, async_client: AsyncMobilerun) -> None:
        state = await async_client.devices.state.ui(
            device_id="deviceId",
        )
        assert_matches_type(object, state, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_ui_with_all_params(self, async_client: AsyncMobilerun) -> None:
        state = await async_client.devices.state.ui(
            device_id="deviceId",
            filter=True,
            x_device_display_id=0,
        )
        assert_matches_type(object, state, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_ui(self, async_client: AsyncMobilerun) -> None:
        response = await async_client.devices.state.with_raw_response.ui(
            device_id="deviceId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        state = await response.parse()
        assert_matches_type(object, state, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_ui(self, async_client: AsyncMobilerun) -> None:
        async with async_client.devices.state.with_streaming_response.ui(
            device_id="deviceId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            state = await response.parse()
            assert_matches_type(object, state, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_ui(self, async_client: AsyncMobilerun) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `device_id` but received ''"):
            await async_client.devices.state.with_raw_response.ui(
                device_id="",
            )
