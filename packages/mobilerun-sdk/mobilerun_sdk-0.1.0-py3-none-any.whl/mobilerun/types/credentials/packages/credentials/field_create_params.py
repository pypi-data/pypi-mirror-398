# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Required, Annotated, TypedDict

from ....._utils import PropertyInfo

__all__ = ["FieldCreateParams"]


class FieldCreateParams(TypedDict, total=False):
    package_name: Required[Annotated[str, PropertyInfo(alias="packageName")]]

    field_type: Required[
        Annotated[
            Literal["email", "username", "password", "api_token", "phone_number", "two_factor_secret", "backup_codes"],
            PropertyInfo(alias="fieldType"),
        ]
    ]

    value: Required[str]
