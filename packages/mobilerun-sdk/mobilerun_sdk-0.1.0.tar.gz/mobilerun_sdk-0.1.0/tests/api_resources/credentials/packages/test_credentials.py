# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from mobilerun import Mobilerun, AsyncMobilerun
from tests.utils import assert_matches_type
from mobilerun.types.credentials.packages import (
    CredentialCreateResponse,
    CredentialDeleteResponse,
    CredentialRetrieveResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestCredentials:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: Mobilerun) -> None:
        credential = client.credentials.packages.credentials.create(
            package_name="packageName",
            credential_name="26f1kl_-n-71",
            fields=[
                {
                    "field_type": "email",
                    "value": "x",
                }
            ],
        )
        assert_matches_type(CredentialCreateResponse, credential, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: Mobilerun) -> None:
        response = client.credentials.packages.credentials.with_raw_response.create(
            package_name="packageName",
            credential_name="26f1kl_-n-71",
            fields=[
                {
                    "field_type": "email",
                    "value": "x",
                }
            ],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        credential = response.parse()
        assert_matches_type(CredentialCreateResponse, credential, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: Mobilerun) -> None:
        with client.credentials.packages.credentials.with_streaming_response.create(
            package_name="packageName",
            credential_name="26f1kl_-n-71",
            fields=[
                {
                    "field_type": "email",
                    "value": "x",
                }
            ],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            credential = response.parse()
            assert_matches_type(CredentialCreateResponse, credential, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_create(self, client: Mobilerun) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `package_name` but received ''"):
            client.credentials.packages.credentials.with_raw_response.create(
                package_name="",
                credential_name="26f1kl_-n-71",
                fields=[
                    {
                        "field_type": "email",
                        "value": "x",
                    }
                ],
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: Mobilerun) -> None:
        credential = client.credentials.packages.credentials.retrieve(
            credential_name="credentialName",
            package_name="packageName",
        )
        assert_matches_type(CredentialRetrieveResponse, credential, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: Mobilerun) -> None:
        response = client.credentials.packages.credentials.with_raw_response.retrieve(
            credential_name="credentialName",
            package_name="packageName",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        credential = response.parse()
        assert_matches_type(CredentialRetrieveResponse, credential, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: Mobilerun) -> None:
        with client.credentials.packages.credentials.with_streaming_response.retrieve(
            credential_name="credentialName",
            package_name="packageName",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            credential = response.parse()
            assert_matches_type(CredentialRetrieveResponse, credential, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: Mobilerun) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `package_name` but received ''"):
            client.credentials.packages.credentials.with_raw_response.retrieve(
                credential_name="credentialName",
                package_name="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `credential_name` but received ''"):
            client.credentials.packages.credentials.with_raw_response.retrieve(
                credential_name="",
                package_name="packageName",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: Mobilerun) -> None:
        credential = client.credentials.packages.credentials.delete(
            credential_name="credentialName",
            package_name="packageName",
        )
        assert_matches_type(CredentialDeleteResponse, credential, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: Mobilerun) -> None:
        response = client.credentials.packages.credentials.with_raw_response.delete(
            credential_name="credentialName",
            package_name="packageName",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        credential = response.parse()
        assert_matches_type(CredentialDeleteResponse, credential, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: Mobilerun) -> None:
        with client.credentials.packages.credentials.with_streaming_response.delete(
            credential_name="credentialName",
            package_name="packageName",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            credential = response.parse()
            assert_matches_type(CredentialDeleteResponse, credential, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_delete(self, client: Mobilerun) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `package_name` but received ''"):
            client.credentials.packages.credentials.with_raw_response.delete(
                credential_name="credentialName",
                package_name="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `credential_name` but received ''"):
            client.credentials.packages.credentials.with_raw_response.delete(
                credential_name="",
                package_name="packageName",
            )


class TestAsyncCredentials:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncMobilerun) -> None:
        credential = await async_client.credentials.packages.credentials.create(
            package_name="packageName",
            credential_name="26f1kl_-n-71",
            fields=[
                {
                    "field_type": "email",
                    "value": "x",
                }
            ],
        )
        assert_matches_type(CredentialCreateResponse, credential, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncMobilerun) -> None:
        response = await async_client.credentials.packages.credentials.with_raw_response.create(
            package_name="packageName",
            credential_name="26f1kl_-n-71",
            fields=[
                {
                    "field_type": "email",
                    "value": "x",
                }
            ],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        credential = await response.parse()
        assert_matches_type(CredentialCreateResponse, credential, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncMobilerun) -> None:
        async with async_client.credentials.packages.credentials.with_streaming_response.create(
            package_name="packageName",
            credential_name="26f1kl_-n-71",
            fields=[
                {
                    "field_type": "email",
                    "value": "x",
                }
            ],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            credential = await response.parse()
            assert_matches_type(CredentialCreateResponse, credential, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_create(self, async_client: AsyncMobilerun) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `package_name` but received ''"):
            await async_client.credentials.packages.credentials.with_raw_response.create(
                package_name="",
                credential_name="26f1kl_-n-71",
                fields=[
                    {
                        "field_type": "email",
                        "value": "x",
                    }
                ],
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncMobilerun) -> None:
        credential = await async_client.credentials.packages.credentials.retrieve(
            credential_name="credentialName",
            package_name="packageName",
        )
        assert_matches_type(CredentialRetrieveResponse, credential, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncMobilerun) -> None:
        response = await async_client.credentials.packages.credentials.with_raw_response.retrieve(
            credential_name="credentialName",
            package_name="packageName",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        credential = await response.parse()
        assert_matches_type(CredentialRetrieveResponse, credential, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncMobilerun) -> None:
        async with async_client.credentials.packages.credentials.with_streaming_response.retrieve(
            credential_name="credentialName",
            package_name="packageName",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            credential = await response.parse()
            assert_matches_type(CredentialRetrieveResponse, credential, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncMobilerun) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `package_name` but received ''"):
            await async_client.credentials.packages.credentials.with_raw_response.retrieve(
                credential_name="credentialName",
                package_name="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `credential_name` but received ''"):
            await async_client.credentials.packages.credentials.with_raw_response.retrieve(
                credential_name="",
                package_name="packageName",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncMobilerun) -> None:
        credential = await async_client.credentials.packages.credentials.delete(
            credential_name="credentialName",
            package_name="packageName",
        )
        assert_matches_type(CredentialDeleteResponse, credential, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncMobilerun) -> None:
        response = await async_client.credentials.packages.credentials.with_raw_response.delete(
            credential_name="credentialName",
            package_name="packageName",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        credential = await response.parse()
        assert_matches_type(CredentialDeleteResponse, credential, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncMobilerun) -> None:
        async with async_client.credentials.packages.credentials.with_streaming_response.delete(
            credential_name="credentialName",
            package_name="packageName",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            credential = await response.parse()
            assert_matches_type(CredentialDeleteResponse, credential, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_delete(self, async_client: AsyncMobilerun) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `package_name` but received ''"):
            await async_client.credentials.packages.credentials.with_raw_response.delete(
                credential_name="credentialName",
                package_name="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `credential_name` but received ''"):
            await async_client.credentials.packages.credentials.with_raw_response.delete(
                credential_name="",
                package_name="packageName",
            )
