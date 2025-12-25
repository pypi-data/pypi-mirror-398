# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from .._models import BaseModel
from .task_status import TaskStatus

__all__ = ["TaskGetStatusResponse"]


class TaskGetStatusResponse(BaseModel):
    status: TaskStatus
    """The status of the task"""
