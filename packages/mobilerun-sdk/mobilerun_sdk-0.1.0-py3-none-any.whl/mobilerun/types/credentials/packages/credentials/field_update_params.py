# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from ....._utils import PropertyInfo

__all__ = ["FieldUpdateParams"]


class FieldUpdateParams(TypedDict, total=False):
    package_name: Required[Annotated[str, PropertyInfo(alias="packageName")]]

    credential_name: Required[Annotated[str, PropertyInfo(alias="credentialName")]]

    value: Required[str]
