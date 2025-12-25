# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from mobilerun import Mobilerun, AsyncMobilerun

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestKeyboard:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_clear(self, client: Mobilerun) -> None:
        keyboard = client.devices.keyboard.clear(
            device_id="deviceId",
        )
        assert keyboard is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_clear_with_all_params(self, client: Mobilerun) -> None:
        keyboard = client.devices.keyboard.clear(
            device_id="deviceId",
            x_device_display_id=0,
        )
        assert keyboard is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_clear(self, client: Mobilerun) -> None:
        response = client.devices.keyboard.with_raw_response.clear(
            device_id="deviceId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        keyboard = response.parse()
        assert keyboard is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_clear(self, client: Mobilerun) -> None:
        with client.devices.keyboard.with_streaming_response.clear(
            device_id="deviceId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            keyboard = response.parse()
            assert keyboard is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_clear(self, client: Mobilerun) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `device_id` but received ''"):
            client.devices.keyboard.with_raw_response.clear(
                device_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_key(self, client: Mobilerun) -> None:
        keyboard = client.devices.keyboard.key(
            device_id="deviceId",
            key=0,
        )
        assert keyboard is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_key_with_all_params(self, client: Mobilerun) -> None:
        keyboard = client.devices.keyboard.key(
            device_id="deviceId",
            key=0,
            x_device_display_id=0,
        )
        assert keyboard is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_key(self, client: Mobilerun) -> None:
        response = client.devices.keyboard.with_raw_response.key(
            device_id="deviceId",
            key=0,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        keyboard = response.parse()
        assert keyboard is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_key(self, client: Mobilerun) -> None:
        with client.devices.keyboard.with_streaming_response.key(
            device_id="deviceId",
            key=0,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            keyboard = response.parse()
            assert keyboard is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_key(self, client: Mobilerun) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `device_id` but received ''"):
            client.devices.keyboard.with_raw_response.key(
                device_id="",
                key=0,
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_write(self, client: Mobilerun) -> None:
        keyboard = client.devices.keyboard.write(
            device_id="deviceId",
            clear=True,
            text="text",
        )
        assert keyboard is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_write_with_all_params(self, client: Mobilerun) -> None:
        keyboard = client.devices.keyboard.write(
            device_id="deviceId",
            clear=True,
            text="text",
            x_device_display_id=0,
        )
        assert keyboard is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_write(self, client: Mobilerun) -> None:
        response = client.devices.keyboard.with_raw_response.write(
            device_id="deviceId",
            clear=True,
            text="text",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        keyboard = response.parse()
        assert keyboard is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_write(self, client: Mobilerun) -> None:
        with client.devices.keyboard.with_streaming_response.write(
            device_id="deviceId",
            clear=True,
            text="text",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            keyboard = response.parse()
            assert keyboard is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_write(self, client: Mobilerun) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `device_id` but received ''"):
            client.devices.keyboard.with_raw_response.write(
                device_id="",
                clear=True,
                text="text",
            )


class TestAsyncKeyboard:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_clear(self, async_client: AsyncMobilerun) -> None:
        keyboard = await async_client.devices.keyboard.clear(
            device_id="deviceId",
        )
        assert keyboard is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_clear_with_all_params(self, async_client: AsyncMobilerun) -> None:
        keyboard = await async_client.devices.keyboard.clear(
            device_id="deviceId",
            x_device_display_id=0,
        )
        assert keyboard is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_clear(self, async_client: AsyncMobilerun) -> None:
        response = await async_client.devices.keyboard.with_raw_response.clear(
            device_id="deviceId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        keyboard = await response.parse()
        assert keyboard is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_clear(self, async_client: AsyncMobilerun) -> None:
        async with async_client.devices.keyboard.with_streaming_response.clear(
            device_id="deviceId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            keyboard = await response.parse()
            assert keyboard is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_clear(self, async_client: AsyncMobilerun) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `device_id` but received ''"):
            await async_client.devices.keyboard.with_raw_response.clear(
                device_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_key(self, async_client: AsyncMobilerun) -> None:
        keyboard = await async_client.devices.keyboard.key(
            device_id="deviceId",
            key=0,
        )
        assert keyboard is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_key_with_all_params(self, async_client: AsyncMobilerun) -> None:
        keyboard = await async_client.devices.keyboard.key(
            device_id="deviceId",
            key=0,
            x_device_display_id=0,
        )
        assert keyboard is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_key(self, async_client: AsyncMobilerun) -> None:
        response = await async_client.devices.keyboard.with_raw_response.key(
            device_id="deviceId",
            key=0,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        keyboard = await response.parse()
        assert keyboard is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_key(self, async_client: AsyncMobilerun) -> None:
        async with async_client.devices.keyboard.with_streaming_response.key(
            device_id="deviceId",
            key=0,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            keyboard = await response.parse()
            assert keyboard is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_key(self, async_client: AsyncMobilerun) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `device_id` but received ''"):
            await async_client.devices.keyboard.with_raw_response.key(
                device_id="",
                key=0,
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_write(self, async_client: AsyncMobilerun) -> None:
        keyboard = await async_client.devices.keyboard.write(
            device_id="deviceId",
            clear=True,
            text="text",
        )
        assert keyboard is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_write_with_all_params(self, async_client: AsyncMobilerun) -> None:
        keyboard = await async_client.devices.keyboard.write(
            device_id="deviceId",
            clear=True,
            text="text",
            x_device_display_id=0,
        )
        assert keyboard is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_write(self, async_client: AsyncMobilerun) -> None:
        response = await async_client.devices.keyboard.with_raw_response.write(
            device_id="deviceId",
            clear=True,
            text="text",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        keyboard = await response.parse()
        assert keyboard is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_write(self, async_client: AsyncMobilerun) -> None:
        async with async_client.devices.keyboard.with_streaming_response.write(
            device_id="deviceId",
            clear=True,
            text="text",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            keyboard = await response.parse()
            assert keyboard is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_write(self, async_client: AsyncMobilerun) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `device_id` but received ''"):
            await async_client.devices.keyboard.with_raw_response.write(
                device_id="",
                clear=True,
                text="text",
            )
