# Tasks

Types:

```python
from mobilerun.types import (
    LlmModel,
    Task,
    TaskCreate,
    TaskStatus,
    TaskRetrieveResponse,
    TaskListResponse,
    TaskGetStatusResponse,
    TaskGetTrajectoryResponse,
    TaskRunResponse,
    TaskStopResponse,
)
```

Methods:

- <code title="get /tasks/{task_id}">client.tasks.<a href="./src/mobilerun/resources/tasks/tasks.py">retrieve</a>(task_id) -> <a href="./src/mobilerun/types/task_retrieve_response.py">TaskRetrieveResponse</a></code>
- <code title="get /tasks/">client.tasks.<a href="./src/mobilerun/resources/tasks/tasks.py">list</a>(\*\*<a href="src/mobilerun/types/task_list_params.py">params</a>) -> <a href="./src/mobilerun/types/task_list_response.py">TaskListResponse</a></code>
- <code title="get /tasks/{task_id}/attach">client.tasks.<a href="./src/mobilerun/resources/tasks/tasks.py">attach</a>(task_id) -> None</code>
- <code title="get /tasks/{task_id}/status">client.tasks.<a href="./src/mobilerun/resources/tasks/tasks.py">get_status</a>(task_id) -> <a href="./src/mobilerun/types/task_get_status_response.py">TaskGetStatusResponse</a></code>
- <code title="get /tasks/{task_id}/trajectory">client.tasks.<a href="./src/mobilerun/resources/tasks/tasks.py">get_trajectory</a>(task_id) -> <a href="./src/mobilerun/types/task_get_trajectory_response.py">TaskGetTrajectoryResponse</a></code>
- <code title="post /tasks/">client.tasks.<a href="./src/mobilerun/resources/tasks/tasks.py">run</a>(\*\*<a href="src/mobilerun/types/task_run_params.py">params</a>) -> <a href="./src/mobilerun/types/task_run_response.py">TaskRunResponse</a></code>
- <code title="post /tasks/stream">client.tasks.<a href="./src/mobilerun/resources/tasks/tasks.py">run_streamed</a>(\*\*<a href="src/mobilerun/types/task_run_streamed_params.py">params</a>) -> None</code>
- <code title="post /tasks/{task_id}/cancel">client.tasks.<a href="./src/mobilerun/resources/tasks/tasks.py">stop</a>(task_id) -> <a href="./src/mobilerun/types/task_stop_response.py">TaskStopResponse</a></code>

## Screenshots

Types:

```python
from mobilerun.types.tasks import MediaResponse, ScreenshotListResponse
```

Methods:

- <code title="get /tasks/{task_id}/screenshots/{index}">client.tasks.screenshots.<a href="./src/mobilerun/resources/tasks/screenshots.py">retrieve</a>(index, \*, task_id) -> <a href="./src/mobilerun/types/tasks/media_response.py">MediaResponse</a></code>
- <code title="get /tasks/{task_id}/screenshots">client.tasks.screenshots.<a href="./src/mobilerun/resources/tasks/screenshots.py">list</a>(task_id) -> <a href="./src/mobilerun/types/tasks/screenshot_list_response.py">ScreenshotListResponse</a></code>

## UiStates

Types:

```python
from mobilerun.types.tasks import UiStateListResponse
```

Methods:

- <code title="get /tasks/{task_id}/ui_states/{index}">client.tasks.ui_states.<a href="./src/mobilerun/resources/tasks/ui_states.py">retrieve</a>(index, \*, task_id) -> <a href="./src/mobilerun/types/tasks/media_response.py">MediaResponse</a></code>
- <code title="get /tasks/{task_id}/ui_states">client.tasks.ui_states.<a href="./src/mobilerun/resources/tasks/ui_states.py">list</a>(task_id) -> <a href="./src/mobilerun/types/tasks/ui_state_list_response.py">UiStateListResponse</a></code>

# Devices

Types:

```python
from mobilerun.types import Device, DeviceListResponse
```

Methods:

- <code title="post /devices">client.devices.<a href="./src/mobilerun/resources/devices/devices.py">create</a>(\*\*<a href="src/mobilerun/types/device_create_params.py">params</a>) -> <a href="./src/mobilerun/types/device.py">Device</a></code>
- <code title="get /devices/{deviceId}">client.devices.<a href="./src/mobilerun/resources/devices/devices.py">retrieve</a>(device_id) -> <a href="./src/mobilerun/types/device.py">Device</a></code>
- <code title="get /devices">client.devices.<a href="./src/mobilerun/resources/devices/devices.py">list</a>(\*\*<a href="src/mobilerun/types/device_list_params.py">params</a>) -> <a href="./src/mobilerun/types/device_list_response.py">DeviceListResponse</a></code>
- <code title="delete /devices/{deviceId}">client.devices.<a href="./src/mobilerun/resources/devices/devices.py">terminate</a>(device_id) -> None</code>
- <code title="get /devices/{deviceId}/wait">client.devices.<a href="./src/mobilerun/resources/devices/devices.py">wait_ready</a>(device_id) -> <a href="./src/mobilerun/types/device.py">Device</a></code>

## Actions

Methods:

- <code title="post /devices/{deviceId}/global">client.devices.actions.<a href="./src/mobilerun/resources/devices/actions.py">global\_</a>(device_id, \*\*<a href="src/mobilerun/types/devices/action_global_params.py">params</a>) -> None</code>
- <code title="post /devices/{deviceId}/swipe">client.devices.actions.<a href="./src/mobilerun/resources/devices/actions.py">swipe</a>(device_id, \*\*<a href="src/mobilerun/types/devices/action_swipe_params.py">params</a>) -> None</code>
- <code title="post /devices/{deviceId}/tap">client.devices.actions.<a href="./src/mobilerun/resources/devices/actions.py">tap</a>(device_id, \*\*<a href="src/mobilerun/types/devices/action_tap_params.py">params</a>) -> None</code>

## State

Types:

```python
from mobilerun.types.devices import StateScreenshotResponse, StateTimeResponse
```

Methods:

- <code title="get /devices/{deviceId}/screenshot">client.devices.state.<a href="./src/mobilerun/resources/devices/state.py">screenshot</a>(device_id, \*\*<a href="src/mobilerun/types/devices/state_screenshot_params.py">params</a>) -> str</code>
- <code title="get /devices/{deviceId}/time">client.devices.state.<a href="./src/mobilerun/resources/devices/state.py">time</a>(device_id) -> str</code>
- <code title="get /devices/{deviceId}/ui-state">client.devices.state.<a href="./src/mobilerun/resources/devices/state.py">ui</a>(device_id, \*\*<a href="src/mobilerun/types/devices/state_ui_params.py">params</a>) -> object</code>

## Apps

Types:

```python
from mobilerun.types.devices import AppListResponse
```

Methods:

- <code title="get /devices/{deviceId}/apps">client.devices.apps.<a href="./src/mobilerun/resources/devices/apps.py">list</a>(device_id, \*\*<a href="src/mobilerun/types/devices/app_list_params.py">params</a>) -> <a href="./src/mobilerun/types/devices/app_list_response.py">Optional[AppListResponse]</a></code>
- <code title="delete /devices/{deviceId}/apps/{packageName}">client.devices.apps.<a href="./src/mobilerun/resources/devices/apps.py">delete</a>(package_name, \*, device_id) -> None</code>
- <code title="post /devices/{deviceId}/apps">client.devices.apps.<a href="./src/mobilerun/resources/devices/apps.py">install</a>(device_id, \*\*<a href="src/mobilerun/types/devices/app_install_params.py">params</a>) -> None</code>
- <code title="put /devices/{deviceId}/apps/{packageName}">client.devices.apps.<a href="./src/mobilerun/resources/devices/apps.py">start</a>(package_name, \*, device_id, \*\*<a href="src/mobilerun/types/devices/app_start_params.py">params</a>) -> None</code>

## Packages

Types:

```python
from mobilerun.types.devices import PackageListResponse
```

Methods:

- <code title="get /devices/{deviceId}/packages">client.devices.packages.<a href="./src/mobilerun/resources/devices/packages.py">list</a>(device_id, \*\*<a href="src/mobilerun/types/devices/package_list_params.py">params</a>) -> <a href="./src/mobilerun/types/devices/package_list_response.py">Optional[PackageListResponse]</a></code>

## Keyboard

Methods:

- <code title="delete /devices/{deviceId}/keyboard">client.devices.keyboard.<a href="./src/mobilerun/resources/devices/keyboard.py">clear</a>(device_id) -> None</code>
- <code title="put /devices/{deviceId}/keyboard">client.devices.keyboard.<a href="./src/mobilerun/resources/devices/keyboard.py">key</a>(device_id, \*\*<a href="src/mobilerun/types/devices/keyboard_key_params.py">params</a>) -> None</code>
- <code title="post /devices/{deviceId}/keyboard">client.devices.keyboard.<a href="./src/mobilerun/resources/devices/keyboard.py">write</a>(device_id, \*\*<a href="src/mobilerun/types/devices/keyboard_write_params.py">params</a>) -> None</code>

# Apps

Types:

```python
from mobilerun.types import AppListResponse
```

Methods:

- <code title="get /apps">client.apps.<a href="./src/mobilerun/resources/apps.py">list</a>(\*\*<a href="src/mobilerun/types/app_list_params.py">params</a>) -> <a href="./src/mobilerun/types/app_list_response.py">AppListResponse</a></code>

# Credentials

Types:

```python
from mobilerun.types import CredentialListResponse
```

Methods:

- <code title="get /credentials">client.credentials.<a href="./src/mobilerun/resources/credentials/credentials.py">list</a>() -> <a href="./src/mobilerun/types/credential_list_response.py">CredentialListResponse</a></code>

## Packages

Types:

```python
from mobilerun.types.credentials import PackageCreateResponse, PackageListResponse
```

Methods:

- <code title="post /credentials/packages">client.credentials.packages.<a href="./src/mobilerun/resources/credentials/packages/packages.py">create</a>(\*\*<a href="src/mobilerun/types/credentials/package_create_params.py">params</a>) -> <a href="./src/mobilerun/types/credentials/package_create_response.py">PackageCreateResponse</a></code>
- <code title="get /credentials/packages/{packageName}">client.credentials.packages.<a href="./src/mobilerun/resources/credentials/packages/packages.py">list</a>(package_name) -> <a href="./src/mobilerun/types/credentials/package_list_response.py">PackageListResponse</a></code>

### Credentials

Types:

```python
from mobilerun.types.credentials.packages import (
    Credential,
    CredentialCreateResponse,
    CredentialRetrieveResponse,
    CredentialDeleteResponse,
)
```

Methods:

- <code title="post /credentials/packages/{packageName}">client.credentials.packages.credentials.<a href="./src/mobilerun/resources/credentials/packages/credentials/credentials.py">create</a>(package_name, \*\*<a href="src/mobilerun/types/credentials/packages/credential_create_params.py">params</a>) -> <a href="./src/mobilerun/types/credentials/packages/credential_create_response.py">CredentialCreateResponse</a></code>
- <code title="get /credentials/packages/{packageName}/credentials/{credentialName}">client.credentials.packages.credentials.<a href="./src/mobilerun/resources/credentials/packages/credentials/credentials.py">retrieve</a>(credential_name, \*, package_name) -> <a href="./src/mobilerun/types/credentials/packages/credential_retrieve_response.py">CredentialRetrieveResponse</a></code>
- <code title="delete /credentials/packages/{packageName}/credentials/{credentialName}">client.credentials.packages.credentials.<a href="./src/mobilerun/resources/credentials/packages/credentials/credentials.py">delete</a>(credential_name, \*, package_name) -> <a href="./src/mobilerun/types/credentials/packages/credential_delete_response.py">CredentialDeleteResponse</a></code>

#### Fields

Types:

```python
from mobilerun.types.credentials.packages.credentials import (
    FieldCreateResponse,
    FieldUpdateResponse,
    FieldDeleteResponse,
)
```

Methods:

- <code title="post /credentials/packages/{packageName}/credentials/{credentialName}/fields">client.credentials.packages.credentials.fields.<a href="./src/mobilerun/resources/credentials/packages/credentials/fields.py">create</a>(credential_name, \*, package_name, \*\*<a href="src/mobilerun/types/credentials/packages/credentials/field_create_params.py">params</a>) -> <a href="./src/mobilerun/types/credentials/packages/credentials/field_create_response.py">FieldCreateResponse</a></code>
- <code title="patch /credentials/packages/{packageName}/credentials/{credentialName}/fields/{fieldType}">client.credentials.packages.credentials.fields.<a href="./src/mobilerun/resources/credentials/packages/credentials/fields.py">update</a>(field_type, \*, package_name, credential_name, \*\*<a href="src/mobilerun/types/credentials/packages/credentials/field_update_params.py">params</a>) -> <a href="./src/mobilerun/types/credentials/packages/credentials/field_update_response.py">FieldUpdateResponse</a></code>
- <code title="delete /credentials/packages/{packageName}/credentials/{credentialName}/fields/{fieldType}">client.credentials.packages.credentials.fields.<a href="./src/mobilerun/resources/credentials/packages/credentials/fields.py">delete</a>(field_type, \*, package_name, credential_name) -> <a href="./src/mobilerun/types/credentials/packages/credentials/field_delete_response.py">FieldDeleteResponse</a></code>

# Hooks

Types:

```python
from mobilerun.types import (
    HookRetrieveResponse,
    HookUpdateResponse,
    HookListResponse,
    HookGetSampleDataResponse,
    HookPerformResponse,
    HookSubscribeResponse,
    HookUnsubscribeResponse,
)
```

Methods:

- <code title="get /hooks/{hook_id}">client.hooks.<a href="./src/mobilerun/resources/hooks.py">retrieve</a>(hook_id) -> <a href="./src/mobilerun/types/hook_retrieve_response.py">HookRetrieveResponse</a></code>
- <code title="post /hooks/{hook_id}/edit">client.hooks.<a href="./src/mobilerun/resources/hooks.py">update</a>(hook_id, \*\*<a href="src/mobilerun/types/hook_update_params.py">params</a>) -> <a href="./src/mobilerun/types/hook_update_response.py">HookUpdateResponse</a></code>
- <code title="get /hooks/">client.hooks.<a href="./src/mobilerun/resources/hooks.py">list</a>(\*\*<a href="src/mobilerun/types/hook_list_params.py">params</a>) -> <a href="./src/mobilerun/types/hook_list_response.py">HookListResponse</a></code>
- <code title="get /hooks/sample">client.hooks.<a href="./src/mobilerun/resources/hooks.py">get_sample_data</a>() -> <a href="./src/mobilerun/types/hook_get_sample_data_response.py">HookGetSampleDataResponse</a></code>
- <code title="post /hooks/perform">client.hooks.<a href="./src/mobilerun/resources/hooks.py">perform</a>() -> <a href="./src/mobilerun/types/hook_perform_response.py">HookPerformResponse</a></code>
- <code title="post /hooks/subscribe">client.hooks.<a href="./src/mobilerun/resources/hooks.py">subscribe</a>(\*\*<a href="src/mobilerun/types/hook_subscribe_params.py">params</a>) -> <a href="./src/mobilerun/types/hook_subscribe_response.py">HookSubscribeResponse</a></code>
- <code title="post /hooks/{hook_id}/unsubscribe">client.hooks.<a href="./src/mobilerun/resources/hooks.py">unsubscribe</a>(hook_id) -> <a href="./src/mobilerun/types/hook_unsubscribe_response.py">HookUnsubscribeResponse</a></code>
