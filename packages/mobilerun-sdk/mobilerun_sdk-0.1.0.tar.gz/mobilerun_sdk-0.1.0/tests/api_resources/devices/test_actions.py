# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from mobilerun import Mobilerun, AsyncMobilerun

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestActions:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_global(self, client: Mobilerun) -> None:
        action = client.devices.actions.global_(
            device_id="deviceId",
            action=0,
        )
        assert action is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_global_with_all_params(self, client: Mobilerun) -> None:
        action = client.devices.actions.global_(
            device_id="deviceId",
            action=0,
            x_device_display_id=0,
        )
        assert action is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_global(self, client: Mobilerun) -> None:
        response = client.devices.actions.with_raw_response.global_(
            device_id="deviceId",
            action=0,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        action = response.parse()
        assert action is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_global(self, client: Mobilerun) -> None:
        with client.devices.actions.with_streaming_response.global_(
            device_id="deviceId",
            action=0,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            action = response.parse()
            assert action is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_global(self, client: Mobilerun) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `device_id` but received ''"):
            client.devices.actions.with_raw_response.global_(
                device_id="",
                action=0,
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_swipe(self, client: Mobilerun) -> None:
        action = client.devices.actions.swipe(
            device_id="deviceId",
            duration=10,
            end_x=0,
            end_y=0,
            start_x=0,
            start_y=0,
        )
        assert action is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_swipe_with_all_params(self, client: Mobilerun) -> None:
        action = client.devices.actions.swipe(
            device_id="deviceId",
            duration=10,
            end_x=0,
            end_y=0,
            start_x=0,
            start_y=0,
            x_device_display_id=0,
        )
        assert action is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_swipe(self, client: Mobilerun) -> None:
        response = client.devices.actions.with_raw_response.swipe(
            device_id="deviceId",
            duration=10,
            end_x=0,
            end_y=0,
            start_x=0,
            start_y=0,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        action = response.parse()
        assert action is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_swipe(self, client: Mobilerun) -> None:
        with client.devices.actions.with_streaming_response.swipe(
            device_id="deviceId",
            duration=10,
            end_x=0,
            end_y=0,
            start_x=0,
            start_y=0,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            action = response.parse()
            assert action is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_swipe(self, client: Mobilerun) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `device_id` but received ''"):
            client.devices.actions.with_raw_response.swipe(
                device_id="",
                duration=10,
                end_x=0,
                end_y=0,
                start_x=0,
                start_y=0,
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_tap(self, client: Mobilerun) -> None:
        action = client.devices.actions.tap(
            device_id="deviceId",
            x=0,
            y=0,
        )
        assert action is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_tap_with_all_params(self, client: Mobilerun) -> None:
        action = client.devices.actions.tap(
            device_id="deviceId",
            x=0,
            y=0,
            x_device_display_id=0,
        )
        assert action is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_tap(self, client: Mobilerun) -> None:
        response = client.devices.actions.with_raw_response.tap(
            device_id="deviceId",
            x=0,
            y=0,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        action = response.parse()
        assert action is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_tap(self, client: Mobilerun) -> None:
        with client.devices.actions.with_streaming_response.tap(
            device_id="deviceId",
            x=0,
            y=0,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            action = response.parse()
            assert action is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_tap(self, client: Mobilerun) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `device_id` but received ''"):
            client.devices.actions.with_raw_response.tap(
                device_id="",
                x=0,
                y=0,
            )


class TestAsyncActions:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_global(self, async_client: AsyncMobilerun) -> None:
        action = await async_client.devices.actions.global_(
            device_id="deviceId",
            action=0,
        )
        assert action is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_global_with_all_params(self, async_client: AsyncMobilerun) -> None:
        action = await async_client.devices.actions.global_(
            device_id="deviceId",
            action=0,
            x_device_display_id=0,
        )
        assert action is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_global(self, async_client: AsyncMobilerun) -> None:
        response = await async_client.devices.actions.with_raw_response.global_(
            device_id="deviceId",
            action=0,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        action = await response.parse()
        assert action is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_global(self, async_client: AsyncMobilerun) -> None:
        async with async_client.devices.actions.with_streaming_response.global_(
            device_id="deviceId",
            action=0,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            action = await response.parse()
            assert action is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_global(self, async_client: AsyncMobilerun) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `device_id` but received ''"):
            await async_client.devices.actions.with_raw_response.global_(
                device_id="",
                action=0,
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_swipe(self, async_client: AsyncMobilerun) -> None:
        action = await async_client.devices.actions.swipe(
            device_id="deviceId",
            duration=10,
            end_x=0,
            end_y=0,
            start_x=0,
            start_y=0,
        )
        assert action is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_swipe_with_all_params(self, async_client: AsyncMobilerun) -> None:
        action = await async_client.devices.actions.swipe(
            device_id="deviceId",
            duration=10,
            end_x=0,
            end_y=0,
            start_x=0,
            start_y=0,
            x_device_display_id=0,
        )
        assert action is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_swipe(self, async_client: AsyncMobilerun) -> None:
        response = await async_client.devices.actions.with_raw_response.swipe(
            device_id="deviceId",
            duration=10,
            end_x=0,
            end_y=0,
            start_x=0,
            start_y=0,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        action = await response.parse()
        assert action is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_swipe(self, async_client: AsyncMobilerun) -> None:
        async with async_client.devices.actions.with_streaming_response.swipe(
            device_id="deviceId",
            duration=10,
            end_x=0,
            end_y=0,
            start_x=0,
            start_y=0,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            action = await response.parse()
            assert action is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_swipe(self, async_client: AsyncMobilerun) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `device_id` but received ''"):
            await async_client.devices.actions.with_raw_response.swipe(
                device_id="",
                duration=10,
                end_x=0,
                end_y=0,
                start_x=0,
                start_y=0,
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_tap(self, async_client: AsyncMobilerun) -> None:
        action = await async_client.devices.actions.tap(
            device_id="deviceId",
            x=0,
            y=0,
        )
        assert action is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_tap_with_all_params(self, async_client: AsyncMobilerun) -> None:
        action = await async_client.devices.actions.tap(
            device_id="deviceId",
            x=0,
            y=0,
            x_device_display_id=0,
        )
        assert action is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_tap(self, async_client: AsyncMobilerun) -> None:
        response = await async_client.devices.actions.with_raw_response.tap(
            device_id="deviceId",
            x=0,
            y=0,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        action = await response.parse()
        assert action is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_tap(self, async_client: AsyncMobilerun) -> None:
        async with async_client.devices.actions.with_streaming_response.tap(
            device_id="deviceId",
            x=0,
            y=0,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            action = await response.parse()
            assert action is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_tap(self, async_client: AsyncMobilerun) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `device_id` but received ''"):
            await async_client.devices.actions.with_raw_response.tap(
                device_id="",
                x=0,
                y=0,
            )
