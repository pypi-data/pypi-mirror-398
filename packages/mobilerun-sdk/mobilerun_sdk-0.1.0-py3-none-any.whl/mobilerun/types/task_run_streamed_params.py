# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Iterable, Optional
from typing_extensions import Literal, Required, Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo
from .llm_model import LlmModel

__all__ = ["TaskRunStreamedParams", "Credential"]


class TaskRunStreamedParams(TypedDict, total=False):
    llm_model: Required[Annotated[LlmModel, PropertyInfo(alias="llmModel")]]

    task: Required[str]

    apps: SequenceNotStr[str]

    credentials: Iterable[Credential]

    device_id: Annotated[Optional[str], PropertyInfo(alias="deviceId")]
    """The ID of the device to run the task on."""

    display_id: Annotated[int, PropertyInfo(alias="displayId")]
    """The display ID of the device to run the task on."""

    execution_timeout: Annotated[int, PropertyInfo(alias="executionTimeout")]

    files: SequenceNotStr[str]

    max_steps: Annotated[int, PropertyInfo(alias="maxSteps")]

    output_schema: Annotated[Optional[Dict[str, object]], PropertyInfo(alias="outputSchema")]

    reasoning: bool

    temperature: float

    vision: bool

    vpn_country: Annotated[
        Optional[Literal["US", "BR", "FR", "DE", "IN", "JP", "KR", "ZA"]], PropertyInfo(alias="vpnCountry")
    ]


class Credential(TypedDict, total=False):
    credential_names: Required[Annotated[SequenceNotStr[str], PropertyInfo(alias="credentialNames")]]

    package_name: Required[Annotated[str, PropertyInfo(alias="packageName")]]
