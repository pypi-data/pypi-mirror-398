# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing_extensions import Literal

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["PackageCreateResponse", "Data"]


class Data(BaseModel):
    package_name: str = FieldInfo(alias="packageName")


class PackageCreateResponse(BaseModel):
    data: Data

    message: str

    success: Literal[True]
