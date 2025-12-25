# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from mobilerun import Mobilerun, AsyncMobilerun
from tests.utils import assert_matches_type
from mobilerun.types.credentials.packages.credentials import (
    FieldCreateResponse,
    FieldDeleteResponse,
    FieldUpdateResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestFields:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: Mobilerun) -> None:
        field = client.credentials.packages.credentials.fields.create(
            credential_name="credentialName",
            package_name="packageName",
            field_type="email",
            value="x",
        )
        assert_matches_type(FieldCreateResponse, field, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: Mobilerun) -> None:
        response = client.credentials.packages.credentials.fields.with_raw_response.create(
            credential_name="credentialName",
            package_name="packageName",
            field_type="email",
            value="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        field = response.parse()
        assert_matches_type(FieldCreateResponse, field, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: Mobilerun) -> None:
        with client.credentials.packages.credentials.fields.with_streaming_response.create(
            credential_name="credentialName",
            package_name="packageName",
            field_type="email",
            value="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            field = response.parse()
            assert_matches_type(FieldCreateResponse, field, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_create(self, client: Mobilerun) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `package_name` but received ''"):
            client.credentials.packages.credentials.fields.with_raw_response.create(
                credential_name="credentialName",
                package_name="",
                field_type="email",
                value="x",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `credential_name` but received ''"):
            client.credentials.packages.credentials.fields.with_raw_response.create(
                credential_name="",
                package_name="packageName",
                field_type="email",
                value="x",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update(self, client: Mobilerun) -> None:
        field = client.credentials.packages.credentials.fields.update(
            field_type="email",
            package_name="packageName",
            credential_name="credentialName",
            value="x",
        )
        assert_matches_type(FieldUpdateResponse, field, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update(self, client: Mobilerun) -> None:
        response = client.credentials.packages.credentials.fields.with_raw_response.update(
            field_type="email",
            package_name="packageName",
            credential_name="credentialName",
            value="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        field = response.parse()
        assert_matches_type(FieldUpdateResponse, field, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update(self, client: Mobilerun) -> None:
        with client.credentials.packages.credentials.fields.with_streaming_response.update(
            field_type="email",
            package_name="packageName",
            credential_name="credentialName",
            value="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            field = response.parse()
            assert_matches_type(FieldUpdateResponse, field, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_update(self, client: Mobilerun) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `package_name` but received ''"):
            client.credentials.packages.credentials.fields.with_raw_response.update(
                field_type="email",
                package_name="",
                credential_name="credentialName",
                value="x",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `credential_name` but received ''"):
            client.credentials.packages.credentials.fields.with_raw_response.update(
                field_type="email",
                package_name="packageName",
                credential_name="",
                value="x",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: Mobilerun) -> None:
        field = client.credentials.packages.credentials.fields.delete(
            field_type="email",
            package_name="packageName",
            credential_name="credentialName",
        )
        assert_matches_type(FieldDeleteResponse, field, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: Mobilerun) -> None:
        response = client.credentials.packages.credentials.fields.with_raw_response.delete(
            field_type="email",
            package_name="packageName",
            credential_name="credentialName",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        field = response.parse()
        assert_matches_type(FieldDeleteResponse, field, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: Mobilerun) -> None:
        with client.credentials.packages.credentials.fields.with_streaming_response.delete(
            field_type="email",
            package_name="packageName",
            credential_name="credentialName",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            field = response.parse()
            assert_matches_type(FieldDeleteResponse, field, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_delete(self, client: Mobilerun) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `package_name` but received ''"):
            client.credentials.packages.credentials.fields.with_raw_response.delete(
                field_type="email",
                package_name="",
                credential_name="credentialName",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `credential_name` but received ''"):
            client.credentials.packages.credentials.fields.with_raw_response.delete(
                field_type="email",
                package_name="packageName",
                credential_name="",
            )


class TestAsyncFields:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncMobilerun) -> None:
        field = await async_client.credentials.packages.credentials.fields.create(
            credential_name="credentialName",
            package_name="packageName",
            field_type="email",
            value="x",
        )
        assert_matches_type(FieldCreateResponse, field, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncMobilerun) -> None:
        response = await async_client.credentials.packages.credentials.fields.with_raw_response.create(
            credential_name="credentialName",
            package_name="packageName",
            field_type="email",
            value="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        field = await response.parse()
        assert_matches_type(FieldCreateResponse, field, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncMobilerun) -> None:
        async with async_client.credentials.packages.credentials.fields.with_streaming_response.create(
            credential_name="credentialName",
            package_name="packageName",
            field_type="email",
            value="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            field = await response.parse()
            assert_matches_type(FieldCreateResponse, field, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_create(self, async_client: AsyncMobilerun) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `package_name` but received ''"):
            await async_client.credentials.packages.credentials.fields.with_raw_response.create(
                credential_name="credentialName",
                package_name="",
                field_type="email",
                value="x",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `credential_name` but received ''"):
            await async_client.credentials.packages.credentials.fields.with_raw_response.create(
                credential_name="",
                package_name="packageName",
                field_type="email",
                value="x",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update(self, async_client: AsyncMobilerun) -> None:
        field = await async_client.credentials.packages.credentials.fields.update(
            field_type="email",
            package_name="packageName",
            credential_name="credentialName",
            value="x",
        )
        assert_matches_type(FieldUpdateResponse, field, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update(self, async_client: AsyncMobilerun) -> None:
        response = await async_client.credentials.packages.credentials.fields.with_raw_response.update(
            field_type="email",
            package_name="packageName",
            credential_name="credentialName",
            value="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        field = await response.parse()
        assert_matches_type(FieldUpdateResponse, field, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncMobilerun) -> None:
        async with async_client.credentials.packages.credentials.fields.with_streaming_response.update(
            field_type="email",
            package_name="packageName",
            credential_name="credentialName",
            value="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            field = await response.parse()
            assert_matches_type(FieldUpdateResponse, field, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_update(self, async_client: AsyncMobilerun) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `package_name` but received ''"):
            await async_client.credentials.packages.credentials.fields.with_raw_response.update(
                field_type="email",
                package_name="",
                credential_name="credentialName",
                value="x",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `credential_name` but received ''"):
            await async_client.credentials.packages.credentials.fields.with_raw_response.update(
                field_type="email",
                package_name="packageName",
                credential_name="",
                value="x",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncMobilerun) -> None:
        field = await async_client.credentials.packages.credentials.fields.delete(
            field_type="email",
            package_name="packageName",
            credential_name="credentialName",
        )
        assert_matches_type(FieldDeleteResponse, field, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncMobilerun) -> None:
        response = await async_client.credentials.packages.credentials.fields.with_raw_response.delete(
            field_type="email",
            package_name="packageName",
            credential_name="credentialName",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        field = await response.parse()
        assert_matches_type(FieldDeleteResponse, field, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncMobilerun) -> None:
        async with async_client.credentials.packages.credentials.fields.with_streaming_response.delete(
            field_type="email",
            package_name="packageName",
            credential_name="credentialName",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            field = await response.parse()
            assert_matches_type(FieldDeleteResponse, field, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_delete(self, async_client: AsyncMobilerun) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `package_name` but received ''"):
            await async_client.credentials.packages.credentials.fields.with_raw_response.delete(
                field_type="email",
                package_name="",
                credential_name="credentialName",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `credential_name` but received ''"):
            await async_client.credentials.packages.credentials.fields.with_raw_response.delete(
                field_type="email",
                package_name="packageName",
                credential_name="",
            )
