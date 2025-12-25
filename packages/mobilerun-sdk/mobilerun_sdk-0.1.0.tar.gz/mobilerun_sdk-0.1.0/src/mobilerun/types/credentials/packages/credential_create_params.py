# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable
from typing_extensions import Literal, Required, Annotated, TypedDict

from ...._utils import PropertyInfo

__all__ = ["CredentialCreateParams", "Field"]


class CredentialCreateParams(TypedDict, total=False):
    credential_name: Required[Annotated[str, PropertyInfo(alias="credentialName")]]

    fields: Required[Iterable[Field]]


class Field(TypedDict, total=False):
    field_type: Required[
        Annotated[
            Literal["email", "username", "password", "api_token", "phone_number", "two_factor_secret", "backup_codes"],
            PropertyInfo(alias="fieldType"),
        ]
    ]

    value: Required[str]
