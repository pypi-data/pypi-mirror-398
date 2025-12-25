# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, Optional, cast

import pytest

from mobilerun import Mobilerun, AsyncMobilerun
from tests.utils import assert_matches_type
from mobilerun.types.devices import AppListResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestApps:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Mobilerun) -> None:
        app = client.devices.apps.list(
            device_id="deviceId",
        )
        assert_matches_type(Optional[AppListResponse], app, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: Mobilerun) -> None:
        app = client.devices.apps.list(
            device_id="deviceId",
            include_system_apps=True,
            x_device_display_id=0,
        )
        assert_matches_type(Optional[AppListResponse], app, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Mobilerun) -> None:
        response = client.devices.apps.with_raw_response.list(
            device_id="deviceId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        app = response.parse()
        assert_matches_type(Optional[AppListResponse], app, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Mobilerun) -> None:
        with client.devices.apps.with_streaming_response.list(
            device_id="deviceId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            app = response.parse()
            assert_matches_type(Optional[AppListResponse], app, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_list(self, client: Mobilerun) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `device_id` but received ''"):
            client.devices.apps.with_raw_response.list(
                device_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: Mobilerun) -> None:
        app = client.devices.apps.delete(
            package_name="packageName",
            device_id="deviceId",
        )
        assert app is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete_with_all_params(self, client: Mobilerun) -> None:
        app = client.devices.apps.delete(
            package_name="packageName",
            device_id="deviceId",
            x_device_display_id=0,
        )
        assert app is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: Mobilerun) -> None:
        response = client.devices.apps.with_raw_response.delete(
            package_name="packageName",
            device_id="deviceId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        app = response.parse()
        assert app is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: Mobilerun) -> None:
        with client.devices.apps.with_streaming_response.delete(
            package_name="packageName",
            device_id="deviceId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            app = response.parse()
            assert app is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_delete(self, client: Mobilerun) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `device_id` but received ''"):
            client.devices.apps.with_raw_response.delete(
                package_name="packageName",
                device_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `package_name` but received ''"):
            client.devices.apps.with_raw_response.delete(
                package_name="",
                device_id="deviceId",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_install(self, client: Mobilerun) -> None:
        app = client.devices.apps.install(
            device_id="deviceId",
            package_name="packageName",
        )
        assert app is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_install_with_all_params(self, client: Mobilerun) -> None:
        app = client.devices.apps.install(
            device_id="deviceId",
            package_name="packageName",
            x_device_display_id=0,
        )
        assert app is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_install(self, client: Mobilerun) -> None:
        response = client.devices.apps.with_raw_response.install(
            device_id="deviceId",
            package_name="packageName",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        app = response.parse()
        assert app is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_install(self, client: Mobilerun) -> None:
        with client.devices.apps.with_streaming_response.install(
            device_id="deviceId",
            package_name="packageName",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            app = response.parse()
            assert app is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_install(self, client: Mobilerun) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `device_id` but received ''"):
            client.devices.apps.with_raw_response.install(
                device_id="",
                package_name="packageName",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_start(self, client: Mobilerun) -> None:
        app = client.devices.apps.start(
            package_name="packageName",
            device_id="deviceId",
        )
        assert app is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_start_with_all_params(self, client: Mobilerun) -> None:
        app = client.devices.apps.start(
            package_name="packageName",
            device_id="deviceId",
            activity="activity",
            x_device_display_id=0,
        )
        assert app is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_start(self, client: Mobilerun) -> None:
        response = client.devices.apps.with_raw_response.start(
            package_name="packageName",
            device_id="deviceId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        app = response.parse()
        assert app is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_start(self, client: Mobilerun) -> None:
        with client.devices.apps.with_streaming_response.start(
            package_name="packageName",
            device_id="deviceId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            app = response.parse()
            assert app is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_start(self, client: Mobilerun) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `device_id` but received ''"):
            client.devices.apps.with_raw_response.start(
                package_name="packageName",
                device_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `package_name` but received ''"):
            client.devices.apps.with_raw_response.start(
                package_name="",
                device_id="deviceId",
            )


class TestAsyncApps:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncMobilerun) -> None:
        app = await async_client.devices.apps.list(
            device_id="deviceId",
        )
        assert_matches_type(Optional[AppListResponse], app, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncMobilerun) -> None:
        app = await async_client.devices.apps.list(
            device_id="deviceId",
            include_system_apps=True,
            x_device_display_id=0,
        )
        assert_matches_type(Optional[AppListResponse], app, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncMobilerun) -> None:
        response = await async_client.devices.apps.with_raw_response.list(
            device_id="deviceId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        app = await response.parse()
        assert_matches_type(Optional[AppListResponse], app, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncMobilerun) -> None:
        async with async_client.devices.apps.with_streaming_response.list(
            device_id="deviceId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            app = await response.parse()
            assert_matches_type(Optional[AppListResponse], app, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_list(self, async_client: AsyncMobilerun) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `device_id` but received ''"):
            await async_client.devices.apps.with_raw_response.list(
                device_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncMobilerun) -> None:
        app = await async_client.devices.apps.delete(
            package_name="packageName",
            device_id="deviceId",
        )
        assert app is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete_with_all_params(self, async_client: AsyncMobilerun) -> None:
        app = await async_client.devices.apps.delete(
            package_name="packageName",
            device_id="deviceId",
            x_device_display_id=0,
        )
        assert app is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncMobilerun) -> None:
        response = await async_client.devices.apps.with_raw_response.delete(
            package_name="packageName",
            device_id="deviceId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        app = await response.parse()
        assert app is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncMobilerun) -> None:
        async with async_client.devices.apps.with_streaming_response.delete(
            package_name="packageName",
            device_id="deviceId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            app = await response.parse()
            assert app is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_delete(self, async_client: AsyncMobilerun) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `device_id` but received ''"):
            await async_client.devices.apps.with_raw_response.delete(
                package_name="packageName",
                device_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `package_name` but received ''"):
            await async_client.devices.apps.with_raw_response.delete(
                package_name="",
                device_id="deviceId",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_install(self, async_client: AsyncMobilerun) -> None:
        app = await async_client.devices.apps.install(
            device_id="deviceId",
            package_name="packageName",
        )
        assert app is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_install_with_all_params(self, async_client: AsyncMobilerun) -> None:
        app = await async_client.devices.apps.install(
            device_id="deviceId",
            package_name="packageName",
            x_device_display_id=0,
        )
        assert app is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_install(self, async_client: AsyncMobilerun) -> None:
        response = await async_client.devices.apps.with_raw_response.install(
            device_id="deviceId",
            package_name="packageName",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        app = await response.parse()
        assert app is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_install(self, async_client: AsyncMobilerun) -> None:
        async with async_client.devices.apps.with_streaming_response.install(
            device_id="deviceId",
            package_name="packageName",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            app = await response.parse()
            assert app is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_install(self, async_client: AsyncMobilerun) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `device_id` but received ''"):
            await async_client.devices.apps.with_raw_response.install(
                device_id="",
                package_name="packageName",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_start(self, async_client: AsyncMobilerun) -> None:
        app = await async_client.devices.apps.start(
            package_name="packageName",
            device_id="deviceId",
        )
        assert app is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_start_with_all_params(self, async_client: AsyncMobilerun) -> None:
        app = await async_client.devices.apps.start(
            package_name="packageName",
            device_id="deviceId",
            activity="activity",
            x_device_display_id=0,
        )
        assert app is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_start(self, async_client: AsyncMobilerun) -> None:
        response = await async_client.devices.apps.with_raw_response.start(
            package_name="packageName",
            device_id="deviceId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        app = await response.parse()
        assert app is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_start(self, async_client: AsyncMobilerun) -> None:
        async with async_client.devices.apps.with_streaming_response.start(
            package_name="packageName",
            device_id="deviceId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            app = await response.parse()
            assert app is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_start(self, async_client: AsyncMobilerun) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `device_id` but received ''"):
            await async_client.devices.apps.with_raw_response.start(
                package_name="packageName",
                device_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `package_name` but received ''"):
            await async_client.devices.apps.with_raw_response.start(
                package_name="",
                device_id="deviceId",
            )
