from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    channels: str,
    project_id: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
    x_tenant_id: None | str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_api_key, Unset):
        headers["X-API-Key"] = x_api_key

    if not isinstance(x_tenant_id, Unset):
        headers["X-Tenant-ID"] = x_tenant_id

    params: dict[str, Any] = {}

    params["channels"] = channels

    json_project_id: None | str | Unset
    if isinstance(project_id, Unset):
        json_project_id = UNSET
    else:
        json_project_id = project_id
    params["project_id"] = json_project_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/realtime/events",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = response.json()
        return response_200

    if response.status_code == 404:
        response_404 = cast(Any, None)
        return response_404

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Any | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    channels: str,
    project_id: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
    x_tenant_id: None | str | Unset = UNSET,
) -> Response[Any | HTTPValidationError]:
    r"""Stream Events

     Server-Sent Events (SSE) endpoint for real-time event streaming.

    Subscribes to Redis channels and streams events as they occur.

    **Usage:**
    ```javascript
    const eventSource = new EventSource('/api/v1/realtime/events?channels=tasks,orders');
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('Event:', data);
    };
    ```

    **Query Parameters:**
    - `channels`: Comma-separated list of channel names (e.g., 'tasks,orders')

    **Headers:**
    - `X-API-Key`: Your API key (required)
    - `X-Tenant-ID`: Your project/tenant ID (required)

    **Event Format:**
    ```json
    {
      \"event\": \"record.created\" | \"record.updated\" | \"record.deleted\",
      \"collection\": \"tasks\",
      \"tenant_id\": \"proj-123\",
      \"record_id\": \"01ARZ3NDEKTSV4RRFFQ69G5FAV\",
      \"data\": { ... },
      \"timestamp\": \"2025-01-15T10:30:00Z\"
    }
    ```

    **Heartbeats:**
    The connection sends a heartbeat every 15 seconds to keep the connection alive.

    Args:
        channels (str): Comma-separated list of channels to subscribe to (e.g.,
            'tasks,orders,chat_messages')
        project_id (None | str | Unset): Project/Tenant ID (optional, defaults to user's project)
        x_api_key (None | str | Unset):
        x_tenant_id (None | str | Unset): Tenant ID header

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        channels=channels,
        project_id=project_id,
        x_api_key=x_api_key,
        x_tenant_id=x_tenant_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    channels: str,
    project_id: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
    x_tenant_id: None | str | Unset = UNSET,
) -> Any | HTTPValidationError | None:
    r"""Stream Events

     Server-Sent Events (SSE) endpoint for real-time event streaming.

    Subscribes to Redis channels and streams events as they occur.

    **Usage:**
    ```javascript
    const eventSource = new EventSource('/api/v1/realtime/events?channels=tasks,orders');
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('Event:', data);
    };
    ```

    **Query Parameters:**
    - `channels`: Comma-separated list of channel names (e.g., 'tasks,orders')

    **Headers:**
    - `X-API-Key`: Your API key (required)
    - `X-Tenant-ID`: Your project/tenant ID (required)

    **Event Format:**
    ```json
    {
      \"event\": \"record.created\" | \"record.updated\" | \"record.deleted\",
      \"collection\": \"tasks\",
      \"tenant_id\": \"proj-123\",
      \"record_id\": \"01ARZ3NDEKTSV4RRFFQ69G5FAV\",
      \"data\": { ... },
      \"timestamp\": \"2025-01-15T10:30:00Z\"
    }
    ```

    **Heartbeats:**
    The connection sends a heartbeat every 15 seconds to keep the connection alive.

    Args:
        channels (str): Comma-separated list of channels to subscribe to (e.g.,
            'tasks,orders,chat_messages')
        project_id (None | str | Unset): Project/Tenant ID (optional, defaults to user's project)
        x_api_key (None | str | Unset):
        x_tenant_id (None | str | Unset): Tenant ID header

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        channels=channels,
        project_id=project_id,
        x_api_key=x_api_key,
        x_tenant_id=x_tenant_id,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    channels: str,
    project_id: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
    x_tenant_id: None | str | Unset = UNSET,
) -> Response[Any | HTTPValidationError]:
    r"""Stream Events

     Server-Sent Events (SSE) endpoint for real-time event streaming.

    Subscribes to Redis channels and streams events as they occur.

    **Usage:**
    ```javascript
    const eventSource = new EventSource('/api/v1/realtime/events?channels=tasks,orders');
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('Event:', data);
    };
    ```

    **Query Parameters:**
    - `channels`: Comma-separated list of channel names (e.g., 'tasks,orders')

    **Headers:**
    - `X-API-Key`: Your API key (required)
    - `X-Tenant-ID`: Your project/tenant ID (required)

    **Event Format:**
    ```json
    {
      \"event\": \"record.created\" | \"record.updated\" | \"record.deleted\",
      \"collection\": \"tasks\",
      \"tenant_id\": \"proj-123\",
      \"record_id\": \"01ARZ3NDEKTSV4RRFFQ69G5FAV\",
      \"data\": { ... },
      \"timestamp\": \"2025-01-15T10:30:00Z\"
    }
    ```

    **Heartbeats:**
    The connection sends a heartbeat every 15 seconds to keep the connection alive.

    Args:
        channels (str): Comma-separated list of channels to subscribe to (e.g.,
            'tasks,orders,chat_messages')
        project_id (None | str | Unset): Project/Tenant ID (optional, defaults to user's project)
        x_api_key (None | str | Unset):
        x_tenant_id (None | str | Unset): Tenant ID header

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        channels=channels,
        project_id=project_id,
        x_api_key=x_api_key,
        x_tenant_id=x_tenant_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    channels: str,
    project_id: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
    x_tenant_id: None | str | Unset = UNSET,
) -> Any | HTTPValidationError | None:
    r"""Stream Events

     Server-Sent Events (SSE) endpoint for real-time event streaming.

    Subscribes to Redis channels and streams events as they occur.

    **Usage:**
    ```javascript
    const eventSource = new EventSource('/api/v1/realtime/events?channels=tasks,orders');
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('Event:', data);
    };
    ```

    **Query Parameters:**
    - `channels`: Comma-separated list of channel names (e.g., 'tasks,orders')

    **Headers:**
    - `X-API-Key`: Your API key (required)
    - `X-Tenant-ID`: Your project/tenant ID (required)

    **Event Format:**
    ```json
    {
      \"event\": \"record.created\" | \"record.updated\" | \"record.deleted\",
      \"collection\": \"tasks\",
      \"tenant_id\": \"proj-123\",
      \"record_id\": \"01ARZ3NDEKTSV4RRFFQ69G5FAV\",
      \"data\": { ... },
      \"timestamp\": \"2025-01-15T10:30:00Z\"
    }
    ```

    **Heartbeats:**
    The connection sends a heartbeat every 15 seconds to keep the connection alive.

    Args:
        channels (str): Comma-separated list of channels to subscribe to (e.g.,
            'tasks,orders,chat_messages')
        project_id (None | str | Unset): Project/Tenant ID (optional, defaults to user's project)
        x_api_key (None | str | Unset):
        x_tenant_id (None | str | Unset): Tenant ID header

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            channels=channels,
            project_id=project_id,
            x_api_key=x_api_key,
            x_tenant_id=x_tenant_id,
        )
    ).parsed
