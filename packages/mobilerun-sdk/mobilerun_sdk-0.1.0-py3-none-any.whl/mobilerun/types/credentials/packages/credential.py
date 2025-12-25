# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from ...._models import BaseModel

__all__ = ["Credential", "Field"]


class Field(BaseModel):
    field_type: Literal[
        "email", "username", "password", "api_token", "phone_number", "two_factor_secret", "backup_codes"
    ] = FieldInfo(alias="fieldType")

    value: str


class Credential(BaseModel):
    credential_name: str = FieldInfo(alias="credentialName")

    fields: List[Field]

    package_name: str = FieldInfo(alias="packageName")

    secret_path: str = FieldInfo(alias="secretPath")

    user_id: str = FieldInfo(alias="userId")
