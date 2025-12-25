# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Union, Optional
from typing_extensions import Literal, TypeAlias

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = [
    "TaskGetTrajectoryResponse",
    "Trajectory",
    "TrajectoryTrajectoryCreatedEvent",
    "TrajectoryTrajectoryCreatedEventData",
    "TrajectoryTrajectoryExceptionEvent",
    "TrajectoryTrajectoryExceptionEventData",
    "TrajectoryTrajectoryCancelEvent",
    "TrajectoryTrajectoryCancelEventData",
    "TrajectoryTrajectoryScreenshotEvent",
    "TrajectoryTrajectoryScreenshotEventData",
    "TrajectoryTrajectoryStartEvent",
    "TrajectoryTrajectoryStopEvent",
    "TrajectoryTrajectoryResultEvent",
    "TrajectoryTrajectoryManagerInputEvent",
    "TrajectoryTrajectoryManagerPlanEvent",
    "TrajectoryTrajectoryManagerPlanEventData",
    "TrajectoryTrajectoryExecutorInputEvent",
    "TrajectoryTrajectoryExecutorInputEventData",
    "TrajectoryTrajectoryExecutorResultEvent",
    "TrajectoryTrajectoryExecutorResultEventData",
    "TrajectoryTrajectoryScripterExecutorInputEvent",
    "TrajectoryTrajectoryScripterExecutorInputEventData",
    "TrajectoryTrajectoryScripterExecutorResultEvent",
    "TrajectoryTrajectoryScripterExecutorResultEventData",
    "TrajectoryTrajectoryPlanCreatedEvent",
    "TrajectoryTrajectoryPlanInputEvent",
    "TrajectoryTrajectoryPlanThinkingEvent",
    "TrajectoryTrajectoryTaskThinkingEvent",
    "TrajectoryTrajectoryTaskThinkingEventData",
    "TrajectoryTrajectoryTaskThinkingEventDataUsage",
    "TrajectoryTrajectoryTaskExecutionEvent",
    "TrajectoryTrajectoryTaskExecutionEventData",
    "TrajectoryTrajectoryTaskExecutionResultEvent",
    "TrajectoryTrajectoryTaskExecutionResultEventData",
    "TrajectoryTrajectoryTaskEndEvent",
    "TrajectoryTrajectoryTaskEndEventData",
    "TrajectoryTrajectoryCodeActExecuteEvent",
    "TrajectoryTrajectoryCodeActExecuteEventData",
    "TrajectoryTrajectoryCodeActResultEvent",
    "TrajectoryTrajectoryCodeActResultEventData",
    "TrajectoryTrajectoryTapActionEvent",
    "TrajectoryTrajectoryTapActionEventData",
    "TrajectoryTrajectorySwipeActionEvent",
    "TrajectoryTrajectorySwipeActionEventData",
    "TrajectoryTrajectoryDragActionEvent",
    "TrajectoryTrajectoryDragActionEventData",
    "TrajectoryTrajectoryInputTextActionEvent",
    "TrajectoryTrajectoryInputTextActionEventData",
    "TrajectoryTrajectoryKeyPressActionEvent",
    "TrajectoryTrajectoryKeyPressActionEventData",
    "TrajectoryTrajectoryStartAppEvent",
    "TrajectoryTrajectoryStartAppEventData",
    "TrajectoryTrajectoryRecordUiStateEvent",
    "TrajectoryTrajectoryRecordUiStateEventData",
    "TrajectoryTrajectoryWaitEvent",
    "TrajectoryTrajectoryWaitEventData",
    "TrajectoryTrajectoryManagerContextEvent",
    "TrajectoryTrajectoryManagerResponseEvent",
    "TrajectoryTrajectoryManagerResponseEventData",
    "TrajectoryTrajectoryManagerResponseEventDataUsage",
    "TrajectoryTrajectoryManagerPlanDetailsEvent",
    "TrajectoryTrajectoryManagerPlanDetailsEventData",
    "TrajectoryTrajectoryExecutorContextEvent",
    "TrajectoryTrajectoryExecutorContextEventData",
    "TrajectoryTrajectoryExecutorResponseEvent",
    "TrajectoryTrajectoryExecutorResponseEventData",
    "TrajectoryTrajectoryExecutorResponseEventDataUsage",
    "TrajectoryTrajectoryExecutorActionEvent",
    "TrajectoryTrajectoryExecutorActionEventData",
    "TrajectoryTrajectoryExecutorActionResultEvent",
    "TrajectoryTrajectoryExecutorActionResultEventData",
    "TrajectoryTrajectoryScripterInputEvent",
    "TrajectoryTrajectoryScripterThinkingEvent",
    "TrajectoryTrajectoryScripterThinkingEventData",
    "TrajectoryTrajectoryScripterThinkingEventDataUsage",
    "TrajectoryTrajectoryScripterExecutionEvent",
    "TrajectoryTrajectoryScripterExecutionEventData",
    "TrajectoryTrajectoryScripterExecutionResultEvent",
    "TrajectoryTrajectoryScripterExecutionResultEventData",
    "TrajectoryTrajectoryScripterEndEvent",
    "TrajectoryTrajectoryScripterEndEventData",
    "TrajectoryTrajectoryTextManipulatorInputEvent",
    "TrajectoryTrajectoryTextManipulatorInputEventData",
    "TrajectoryTrajectoryTextManipulatorResultEvent",
    "TrajectoryTrajectoryTextManipulatorResultEventData",
]


class TrajectoryTrajectoryCreatedEventData(BaseModel):
    id: str

    token: str

    stream_url: str = FieldInfo(alias="streamUrl")


class TrajectoryTrajectoryCreatedEvent(BaseModel):
    data: TrajectoryTrajectoryCreatedEventData

    event: Literal["CreatedEvent"]


class TrajectoryTrajectoryExceptionEventData(BaseModel):
    exception: str


class TrajectoryTrajectoryExceptionEvent(BaseModel):
    data: TrajectoryTrajectoryExceptionEventData

    event: Literal["ExceptionEvent"]


class TrajectoryTrajectoryCancelEventData(BaseModel):
    reason: str


class TrajectoryTrajectoryCancelEvent(BaseModel):
    data: TrajectoryTrajectoryCancelEventData

    event: Literal["CancelEvent"]


class TrajectoryTrajectoryScreenshotEventData(BaseModel):
    index: int

    url: str


class TrajectoryTrajectoryScreenshotEvent(BaseModel):
    data: TrajectoryTrajectoryScreenshotEventData

    event: Literal["ScreenshotEvent"]


class TrajectoryTrajectoryStartEvent(BaseModel):
    data: object
    """Implicit entry event sent to kick off a `Workflow.run()`."""

    event: Literal["StartEvent"]


class TrajectoryTrajectoryStopEvent(BaseModel):
    data: object
    """Terminal event that signals the workflow has completed.

    The `result` property contains the return value of the workflow run. When a
    custom stop event subclass is used, the workflow result is that event instance
    itself.

    Examples:
    `python # default stop event: result holds the value return StopEvent(result={"answer": 42}) `

        Subclassing to provide a custom result:

        ```python
        class MyStopEv(StopEvent):
            pass

        @step
        async def my_step(self, ctx: Context, ev: StartEvent) -> MyStopEv:
            return MyStopEv(result={"answer": 42})
    """

    event: Literal["StopEvent"]


class TrajectoryTrajectoryResultEvent(BaseModel):
    data: Dict[str, object]

    event: Literal["ResultEvent"]


class TrajectoryTrajectoryManagerInputEvent(BaseModel):
    data: object
    """Trigger Manager workflow for planning"""

    event: Literal["ManagerInputEvent"]


class TrajectoryTrajectoryManagerPlanEventData(BaseModel):
    """Coordination event from ManagerAgent to DroidAgent.

    Used for workflow step routing only (NOT streamed to frontend).
    For internal events with memory_update metadata, see ManagerPlanDetailsEvent.
    """

    current_subgoal: str

    plan: str

    thought: str

    manager_answer: Optional[str] = None

    success: Optional[bool] = None


class TrajectoryTrajectoryManagerPlanEvent(BaseModel):
    data: TrajectoryTrajectoryManagerPlanEventData
    """Coordination event from ManagerAgent to DroidAgent.

    Used for workflow step routing only (NOT streamed to frontend). For internal
    events with memory_update metadata, see ManagerPlanDetailsEvent.
    """

    event: Literal["ManagerPlanEvent"]


class TrajectoryTrajectoryExecutorInputEventData(BaseModel):
    """Trigger Executor workflow for action execution"""

    current_subgoal: str


class TrajectoryTrajectoryExecutorInputEvent(BaseModel):
    data: TrajectoryTrajectoryExecutorInputEventData
    """Trigger Executor workflow for action execution"""

    event: Literal["ExecutorInputEvent"]


class TrajectoryTrajectoryExecutorResultEventData(BaseModel):
    """Executor finished with action result."""

    action: Dict[str, object]

    error: str

    outcome: bool

    summary: str


class TrajectoryTrajectoryExecutorResultEvent(BaseModel):
    data: TrajectoryTrajectoryExecutorResultEventData
    """Executor finished with action result."""

    event: Literal["ExecutorResultEvent"]


class TrajectoryTrajectoryScripterExecutorInputEventData(BaseModel):
    """Trigger ScripterAgent workflow for off-device operations"""

    task: str


class TrajectoryTrajectoryScripterExecutorInputEvent(BaseModel):
    data: TrajectoryTrajectoryScripterExecutorInputEventData
    """Trigger ScripterAgent workflow for off-device operations"""

    event: Literal["ScripterExecutorInputEvent"]


class TrajectoryTrajectoryScripterExecutorResultEventData(BaseModel):
    """Scripter finished."""

    code_executions: int

    message: str

    success: bool

    task: str


class TrajectoryTrajectoryScripterExecutorResultEvent(BaseModel):
    data: TrajectoryTrajectoryScripterExecutorResultEventData
    """Scripter finished."""

    event: Literal["ScripterExecutorResultEvent"]


class TrajectoryTrajectoryPlanCreatedEvent(BaseModel):
    data: Dict[str, object]

    event: Literal["PlanCreatedEvent"]


class TrajectoryTrajectoryPlanInputEvent(BaseModel):
    data: Dict[str, object]

    event: Literal["PlanInputEvent"]


class TrajectoryTrajectoryPlanThinkingEvent(BaseModel):
    data: Dict[str, object]

    event: Literal["PlanThinkingEvent"]


class TrajectoryTrajectoryTaskThinkingEventDataUsage(BaseModel):
    request_tokens: int

    requests: int

    response_tokens: int

    total_tokens: int


class TrajectoryTrajectoryTaskThinkingEventData(BaseModel):
    """LLM response received."""

    thought: str

    code: Optional[str] = None

    usage: Optional[TrajectoryTrajectoryTaskThinkingEventDataUsage] = None


class TrajectoryTrajectoryTaskThinkingEvent(BaseModel):
    data: TrajectoryTrajectoryTaskThinkingEventData
    """LLM response received."""

    event: Literal["TaskThinkingEvent"]


class TrajectoryTrajectoryTaskExecutionEventData(BaseModel):
    """Code ready to execute (internal event)."""

    code: str


class TrajectoryTrajectoryTaskExecutionEvent(BaseModel):
    data: TrajectoryTrajectoryTaskExecutionEventData
    """Code ready to execute (internal event)."""

    event: Literal["TaskExecutionEvent"]


class TrajectoryTrajectoryTaskExecutionResultEventData(BaseModel):
    """Code execution result (internal event)."""

    output: str


class TrajectoryTrajectoryTaskExecutionResultEvent(BaseModel):
    data: TrajectoryTrajectoryTaskExecutionResultEventData
    """Code execution result (internal event)."""

    event: Literal["TaskExecutionResultEvent"]


class TrajectoryTrajectoryTaskEndEventData(BaseModel):
    """CodeAct finished."""

    reason: str

    success: bool

    code_executions: Optional[int] = None


class TrajectoryTrajectoryTaskEndEvent(BaseModel):
    data: TrajectoryTrajectoryTaskEndEventData
    """CodeAct finished."""

    event: Literal["TaskEndEvent"]


class TrajectoryTrajectoryCodeActExecuteEventData(BaseModel):
    instruction: str


class TrajectoryTrajectoryCodeActExecuteEvent(BaseModel):
    data: TrajectoryTrajectoryCodeActExecuteEventData

    event: Literal["CodeActExecuteEvent"]


class TrajectoryTrajectoryCodeActResultEventData(BaseModel):
    instruction: str

    reason: str

    success: bool


class TrajectoryTrajectoryCodeActResultEvent(BaseModel):
    data: TrajectoryTrajectoryCodeActResultEventData

    event: Literal["CodeActResultEvent"]


class TrajectoryTrajectoryTapActionEventData(BaseModel):
    """Event for tap actions with coordinates"""

    action_type: str

    description: str

    x: int

    y: int

    element_bounds: Optional[str] = None

    element_index: Optional[int] = None

    element_text: Optional[str] = None


class TrajectoryTrajectoryTapActionEvent(BaseModel):
    data: TrajectoryTrajectoryTapActionEventData
    """Event for tap actions with coordinates"""

    event: Literal["TapActionEvent"]


class TrajectoryTrajectorySwipeActionEventData(BaseModel):
    """Event for swipe actions with coordinates"""

    action_type: str

    description: str

    duration_ms: int

    end_x: int

    end_y: int

    start_x: int

    start_y: int


class TrajectoryTrajectorySwipeActionEvent(BaseModel):
    data: TrajectoryTrajectorySwipeActionEventData
    """Event for swipe actions with coordinates"""

    event: Literal["SwipeActionEvent"]


class TrajectoryTrajectoryDragActionEventData(BaseModel):
    """Event for drag actions with coordinates"""

    action_type: str

    description: str

    duration_ms: int

    end_x: int

    end_y: int

    start_x: int

    start_y: int


class TrajectoryTrajectoryDragActionEvent(BaseModel):
    data: TrajectoryTrajectoryDragActionEventData
    """Event for drag actions with coordinates"""

    event: Literal["DragActionEvent"]


class TrajectoryTrajectoryInputTextActionEventData(BaseModel):
    """Event for text input actions"""

    action_type: str

    description: str

    text: str


class TrajectoryTrajectoryInputTextActionEvent(BaseModel):
    data: TrajectoryTrajectoryInputTextActionEventData
    """Event for text input actions"""

    event: Literal["InputTextActionEvent"]


class TrajectoryTrajectoryKeyPressActionEventData(BaseModel):
    """Event for key press actions"""

    action_type: str

    description: str

    keycode: int

    key_name: Optional[str] = None


class TrajectoryTrajectoryKeyPressActionEvent(BaseModel):
    data: TrajectoryTrajectoryKeyPressActionEventData
    """Event for key press actions"""

    event: Literal["KeyPressActionEvent"]


class TrajectoryTrajectoryStartAppEventData(BaseModel):
    """\"Event for starting an app"""

    action_type: str

    description: str

    package: str

    activity: Optional[str] = None


class TrajectoryTrajectoryStartAppEvent(BaseModel):
    data: TrajectoryTrajectoryStartAppEventData
    """\"Event for starting an app"""

    event: Literal["StartAppEvent"]


class TrajectoryTrajectoryRecordUiStateEventData(BaseModel):
    index: int

    url: str


class TrajectoryTrajectoryRecordUiStateEvent(BaseModel):
    data: TrajectoryTrajectoryRecordUiStateEventData

    event: Literal["RecordUIStateEvent"]


class TrajectoryTrajectoryWaitEventData(BaseModel):
    """Event for wait/sleep actions"""

    action_type: str

    description: str

    duration: float


class TrajectoryTrajectoryWaitEvent(BaseModel):
    data: TrajectoryTrajectoryWaitEventData
    """Event for wait/sleep actions"""

    event: Literal["WaitEvent"]


class TrajectoryTrajectoryManagerContextEvent(BaseModel):
    data: object
    """Context prepared, ready for LLM call."""

    event: Literal["ManagerContextEvent"]


class TrajectoryTrajectoryManagerResponseEventDataUsage(BaseModel):
    request_tokens: int

    requests: int

    response_tokens: int

    total_tokens: int


class TrajectoryTrajectoryManagerResponseEventData(BaseModel):
    """LLM response received, ready for parsing."""

    response: str

    usage: Optional[TrajectoryTrajectoryManagerResponseEventDataUsage] = None


class TrajectoryTrajectoryManagerResponseEvent(BaseModel):
    data: TrajectoryTrajectoryManagerResponseEventData
    """LLM response received, ready for parsing."""

    event: Literal["ManagerResponseEvent"]


class TrajectoryTrajectoryManagerPlanDetailsEventData(BaseModel):
    """Plan parsed and ready (internal event with full details)."""

    plan: str

    subgoal: str

    thought: str

    answer: Optional[str] = None

    full_response: Optional[str] = None

    memory_update: Optional[str] = None

    progress_summary: Optional[str] = None

    success: Optional[bool] = None


class TrajectoryTrajectoryManagerPlanDetailsEvent(BaseModel):
    data: TrajectoryTrajectoryManagerPlanDetailsEventData
    """Plan parsed and ready (internal event with full details)."""

    event: Literal["ManagerPlanDetailsEvent"]


class TrajectoryTrajectoryExecutorContextEventData(BaseModel):
    """Context prepared, ready for LLM call."""

    subgoal: str


class TrajectoryTrajectoryExecutorContextEvent(BaseModel):
    data: TrajectoryTrajectoryExecutorContextEventData
    """Context prepared, ready for LLM call."""

    event: Literal["ExecutorContextEvent"]


class TrajectoryTrajectoryExecutorResponseEventDataUsage(BaseModel):
    request_tokens: int

    requests: int

    response_tokens: int

    total_tokens: int


class TrajectoryTrajectoryExecutorResponseEventData(BaseModel):
    """LLM response received, ready for parsing."""

    response: str

    usage: Optional[TrajectoryTrajectoryExecutorResponseEventDataUsage] = None


class TrajectoryTrajectoryExecutorResponseEvent(BaseModel):
    data: TrajectoryTrajectoryExecutorResponseEventData
    """LLM response received, ready for parsing."""

    event: Literal["ExecutorResponseEvent"]


class TrajectoryTrajectoryExecutorActionEventData(BaseModel):
    """Action parsed, ready to execute."""

    action_json: str

    description: str

    thought: str

    full_response: Optional[str] = None


class TrajectoryTrajectoryExecutorActionEvent(BaseModel):
    data: TrajectoryTrajectoryExecutorActionEventData
    """Action parsed, ready to execute."""

    event: Literal["ExecutorActionEvent"]


class TrajectoryTrajectoryExecutorActionResultEventData(BaseModel):
    """Action execution result (internal event with full details)."""

    action: Dict[str, object]

    error: str

    success: bool

    summary: str

    full_response: Optional[str] = None

    thought: Optional[str] = None


class TrajectoryTrajectoryExecutorActionResultEvent(BaseModel):
    data: TrajectoryTrajectoryExecutorActionResultEventData
    """Action execution result (internal event with full details)."""

    event: Literal["ExecutorActionResultEvent"]


class TrajectoryTrajectoryScripterInputEvent(BaseModel):
    data: object
    """Input ready for LLM."""

    event: Literal["ScripterInputEvent"]


class TrajectoryTrajectoryScripterThinkingEventDataUsage(BaseModel):
    request_tokens: int

    requests: int

    response_tokens: int

    total_tokens: int


class TrajectoryTrajectoryScripterThinkingEventData(BaseModel):
    """LLM response received."""

    thought: str

    code: Optional[str] = None

    full_response: Optional[str] = None

    usage: Optional[TrajectoryTrajectoryScripterThinkingEventDataUsage] = None


class TrajectoryTrajectoryScripterThinkingEvent(BaseModel):
    data: TrajectoryTrajectoryScripterThinkingEventData
    """LLM response received."""

    event: Literal["ScripterThinkingEvent"]


class TrajectoryTrajectoryScripterExecutionEventData(BaseModel):
    """Code ready to execute."""

    code: str


class TrajectoryTrajectoryScripterExecutionEvent(BaseModel):
    data: TrajectoryTrajectoryScripterExecutionEventData
    """Code ready to execute."""

    event: Literal["ScripterExecutionEvent"]


class TrajectoryTrajectoryScripterExecutionResultEventData(BaseModel):
    """Code execution result."""

    output: str


class TrajectoryTrajectoryScripterExecutionResultEvent(BaseModel):
    data: TrajectoryTrajectoryScripterExecutionResultEventData
    """Code execution result."""

    event: Literal["ScripterExecutionResultEvent"]


class TrajectoryTrajectoryScripterEndEventData(BaseModel):
    """Scripter finished."""

    message: str

    success: bool

    code_executions: Optional[int] = None


class TrajectoryTrajectoryScripterEndEvent(BaseModel):
    data: TrajectoryTrajectoryScripterEndEventData
    """Scripter finished."""

    event: Literal["ScripterEndEvent"]


class TrajectoryTrajectoryTextManipulatorInputEventData(BaseModel):
    """Trigger TextManipulatorAgent workflow for text manipulation"""

    task: str


class TrajectoryTrajectoryTextManipulatorInputEvent(BaseModel):
    data: TrajectoryTrajectoryTextManipulatorInputEventData
    """Trigger TextManipulatorAgent workflow for text manipulation"""

    event: Literal["TextManipulatorInputEvent"]


class TrajectoryTrajectoryTextManipulatorResultEventData(BaseModel):
    code_ran: str

    task: str

    text_to_type: str


class TrajectoryTrajectoryTextManipulatorResultEvent(BaseModel):
    data: TrajectoryTrajectoryTextManipulatorResultEventData

    event: Literal["TextManipulatorResultEvent"]


Trajectory: TypeAlias = Union[
    TrajectoryTrajectoryCreatedEvent,
    TrajectoryTrajectoryExceptionEvent,
    TrajectoryTrajectoryCancelEvent,
    TrajectoryTrajectoryScreenshotEvent,
    TrajectoryTrajectoryStartEvent,
    TrajectoryTrajectoryStopEvent,
    TrajectoryTrajectoryResultEvent,
    TrajectoryTrajectoryManagerInputEvent,
    TrajectoryTrajectoryManagerPlanEvent,
    TrajectoryTrajectoryExecutorInputEvent,
    TrajectoryTrajectoryExecutorResultEvent,
    TrajectoryTrajectoryScripterExecutorInputEvent,
    TrajectoryTrajectoryScripterExecutorResultEvent,
    TrajectoryTrajectoryPlanCreatedEvent,
    TrajectoryTrajectoryPlanInputEvent,
    TrajectoryTrajectoryPlanThinkingEvent,
    TrajectoryTrajectoryTaskThinkingEvent,
    TrajectoryTrajectoryTaskExecutionEvent,
    TrajectoryTrajectoryTaskExecutionResultEvent,
    TrajectoryTrajectoryTaskEndEvent,
    TrajectoryTrajectoryCodeActExecuteEvent,
    TrajectoryTrajectoryCodeActResultEvent,
    TrajectoryTrajectoryTapActionEvent,
    TrajectoryTrajectorySwipeActionEvent,
    TrajectoryTrajectoryDragActionEvent,
    TrajectoryTrajectoryInputTextActionEvent,
    TrajectoryTrajectoryKeyPressActionEvent,
    TrajectoryTrajectoryStartAppEvent,
    TrajectoryTrajectoryRecordUiStateEvent,
    TrajectoryTrajectoryWaitEvent,
    TrajectoryTrajectoryManagerContextEvent,
    TrajectoryTrajectoryManagerResponseEvent,
    TrajectoryTrajectoryManagerPlanDetailsEvent,
    TrajectoryTrajectoryExecutorContextEvent,
    TrajectoryTrajectoryExecutorResponseEvent,
    TrajectoryTrajectoryExecutorActionEvent,
    TrajectoryTrajectoryExecutorActionResultEvent,
    TrajectoryTrajectoryScripterInputEvent,
    TrajectoryTrajectoryScripterThinkingEvent,
    TrajectoryTrajectoryScripterExecutionEvent,
    TrajectoryTrajectoryScripterExecutionResultEvent,
    TrajectoryTrajectoryScripterEndEvent,
    TrajectoryTrajectoryTextManipulatorInputEvent,
    TrajectoryTrajectoryTextManipulatorResultEvent,
]


class TaskGetTrajectoryResponse(BaseModel):
    trajectory: List[Trajectory]
    """The trajectory of the task"""
