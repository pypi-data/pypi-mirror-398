from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.collection_list_response import CollectionListResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    collection_name: str,
    *,
    limit: int | Unset = 100,
    cursor: None | str | Unset = UNSET,
    order_by: None | str | Unset = UNSET,
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

    params["limit"] = limit

    json_cursor: None | str | Unset
    if isinstance(cursor, Unset):
        json_cursor = UNSET
    else:
        json_cursor = cursor
    params["cursor"] = json_cursor

    json_order_by: None | str | Unset
    if isinstance(order_by, Unset):
        json_order_by = UNSET
    else:
        json_order_by = order_by
    params["order_by"] = json_order_by

    json_project_id: None | str | Unset
    if isinstance(project_id, Unset):
        json_project_id = UNSET
    else:
        json_project_id = project_id
    params["project_id"] = json_project_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/collections/{collection_name}/records".format(
            collection_name=quote(str(collection_name), safe=""),
        ),
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | CollectionListResponse | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = CollectionListResponse.from_dict(response.json())

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
) -> Response[Any | CollectionListResponse | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    collection_name: str,
    *,
    client: AuthenticatedClient,
    limit: int | Unset = 100,
    cursor: None | str | Unset = UNSET,
    order_by: None | str | Unset = UNSET,
    project_id: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
    x_tenant_id: None | str | Unset = UNSET,
) -> Response[Any | CollectionListResponse | HTTPValidationError]:
    """List records in a collection

     List records in a collection with optional filtering and cursor-based pagination.

    **Filtering:**
    - Supports simple equality filters via query parameters
    - Example: `?status=done&priority=high`
    - Only single-field equality filters are supported (no composite indexes needed)
    - Complex queries (multiple filters + custom ordering) will return 400 error with guidance

    **Pagination:**
    - Uses cursor-based pagination (ULID-based)
    - Use `next_page_token` from response to get next page
    - Example: `?cursor=01ARZ3NDEKTSV4RRFFQ69G5FAV`

    **Ordering:**
    - Default: ordered by creation time (via ULID 'id' field)
    - Custom ordering requires composite indexes and is not supported yet
    - Use default ordering or fetch and sort in memory

    **Limits:**
    - Maximum 100 records per request

    Args:
        collection_name (str):
        limit (int | Unset): Maximum number of records to return (max 100) Default: 100.
        cursor (None | str | Unset): Pagination cursor (ULID from previous response's
            next_page_token)
        order_by (None | str | Unset): Field to order by (default: 'id' for creation time
            ordering)
        project_id (None | str | Unset): Project/Tenant ID (optional, defaults to user's project)
        x_api_key (None | str | Unset):
        x_tenant_id (None | str | Unset): Tenant ID header

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | CollectionListResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        collection_name=collection_name,
        limit=limit,
        cursor=cursor,
        order_by=order_by,
        project_id=project_id,
        x_api_key=x_api_key,
        x_tenant_id=x_tenant_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    collection_name: str,
    *,
    client: AuthenticatedClient,
    limit: int | Unset = 100,
    cursor: None | str | Unset = UNSET,
    order_by: None | str | Unset = UNSET,
    project_id: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
    x_tenant_id: None | str | Unset = UNSET,
) -> Any | CollectionListResponse | HTTPValidationError | None:
    """List records in a collection

     List records in a collection with optional filtering and cursor-based pagination.

    **Filtering:**
    - Supports simple equality filters via query parameters
    - Example: `?status=done&priority=high`
    - Only single-field equality filters are supported (no composite indexes needed)
    - Complex queries (multiple filters + custom ordering) will return 400 error with guidance

    **Pagination:**
    - Uses cursor-based pagination (ULID-based)
    - Use `next_page_token` from response to get next page
    - Example: `?cursor=01ARZ3NDEKTSV4RRFFQ69G5FAV`

    **Ordering:**
    - Default: ordered by creation time (via ULID 'id' field)
    - Custom ordering requires composite indexes and is not supported yet
    - Use default ordering or fetch and sort in memory

    **Limits:**
    - Maximum 100 records per request

    Args:
        collection_name (str):
        limit (int | Unset): Maximum number of records to return (max 100) Default: 100.
        cursor (None | str | Unset): Pagination cursor (ULID from previous response's
            next_page_token)
        order_by (None | str | Unset): Field to order by (default: 'id' for creation time
            ordering)
        project_id (None | str | Unset): Project/Tenant ID (optional, defaults to user's project)
        x_api_key (None | str | Unset):
        x_tenant_id (None | str | Unset): Tenant ID header

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | CollectionListResponse | HTTPValidationError
    """

    return sync_detailed(
        collection_name=collection_name,
        client=client,
        limit=limit,
        cursor=cursor,
        order_by=order_by,
        project_id=project_id,
        x_api_key=x_api_key,
        x_tenant_id=x_tenant_id,
    ).parsed


async def asyncio_detailed(
    collection_name: str,
    *,
    client: AuthenticatedClient,
    limit: int | Unset = 100,
    cursor: None | str | Unset = UNSET,
    order_by: None | str | Unset = UNSET,
    project_id: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
    x_tenant_id: None | str | Unset = UNSET,
) -> Response[Any | CollectionListResponse | HTTPValidationError]:
    """List records in a collection

     List records in a collection with optional filtering and cursor-based pagination.

    **Filtering:**
    - Supports simple equality filters via query parameters
    - Example: `?status=done&priority=high`
    - Only single-field equality filters are supported (no composite indexes needed)
    - Complex queries (multiple filters + custom ordering) will return 400 error with guidance

    **Pagination:**
    - Uses cursor-based pagination (ULID-based)
    - Use `next_page_token` from response to get next page
    - Example: `?cursor=01ARZ3NDEKTSV4RRFFQ69G5FAV`

    **Ordering:**
    - Default: ordered by creation time (via ULID 'id' field)
    - Custom ordering requires composite indexes and is not supported yet
    - Use default ordering or fetch and sort in memory

    **Limits:**
    - Maximum 100 records per request

    Args:
        collection_name (str):
        limit (int | Unset): Maximum number of records to return (max 100) Default: 100.
        cursor (None | str | Unset): Pagination cursor (ULID from previous response's
            next_page_token)
        order_by (None | str | Unset): Field to order by (default: 'id' for creation time
            ordering)
        project_id (None | str | Unset): Project/Tenant ID (optional, defaults to user's project)
        x_api_key (None | str | Unset):
        x_tenant_id (None | str | Unset): Tenant ID header

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | CollectionListResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        collection_name=collection_name,
        limit=limit,
        cursor=cursor,
        order_by=order_by,
        project_id=project_id,
        x_api_key=x_api_key,
        x_tenant_id=x_tenant_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    collection_name: str,
    *,
    client: AuthenticatedClient,
    limit: int | Unset = 100,
    cursor: None | str | Unset = UNSET,
    order_by: None | str | Unset = UNSET,
    project_id: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
    x_tenant_id: None | str | Unset = UNSET,
) -> Any | CollectionListResponse | HTTPValidationError | None:
    """List records in a collection

     List records in a collection with optional filtering and cursor-based pagination.

    **Filtering:**
    - Supports simple equality filters via query parameters
    - Example: `?status=done&priority=high`
    - Only single-field equality filters are supported (no composite indexes needed)
    - Complex queries (multiple filters + custom ordering) will return 400 error with guidance

    **Pagination:**
    - Uses cursor-based pagination (ULID-based)
    - Use `next_page_token` from response to get next page
    - Example: `?cursor=01ARZ3NDEKTSV4RRFFQ69G5FAV`

    **Ordering:**
    - Default: ordered by creation time (via ULID 'id' field)
    - Custom ordering requires composite indexes and is not supported yet
    - Use default ordering or fetch and sort in memory

    **Limits:**
    - Maximum 100 records per request

    Args:
        collection_name (str):
        limit (int | Unset): Maximum number of records to return (max 100) Default: 100.
        cursor (None | str | Unset): Pagination cursor (ULID from previous response's
            next_page_token)
        order_by (None | str | Unset): Field to order by (default: 'id' for creation time
            ordering)
        project_id (None | str | Unset): Project/Tenant ID (optional, defaults to user's project)
        x_api_key (None | str | Unset):
        x_tenant_id (None | str | Unset): Tenant ID header

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | CollectionListResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            collection_name=collection_name,
            client=client,
            limit=limit,
            cursor=cursor,
            order_by=order_by,
            project_id=project_id,
            x_api_key=x_api_key,
            x_tenant_id=x_tenant_id,
        )
    ).parsed
