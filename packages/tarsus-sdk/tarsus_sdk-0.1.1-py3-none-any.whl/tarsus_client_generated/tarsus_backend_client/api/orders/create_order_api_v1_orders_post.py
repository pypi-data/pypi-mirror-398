from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.order_model import OrderModel
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: OrderModel,
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

    json_project_id: None | str | Unset
    if isinstance(project_id, Unset):
        json_project_id = UNSET
    else:
        json_project_id = project_id
    params["project_id"] = json_project_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/orders",
        "params": params,
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | HTTPValidationError | None:
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
    body: OrderModel,
    project_id: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
    x_tenant_id: None | str | Unset = UNSET,
) -> Response[Any | HTTPValidationError]:
    """Create a new order

     Create a new order with variant and modification support.
    Requires authentication (customer user or backend user via API key).
    Customer users can only create orders for themselves.
    Validates variants exist, calculates line totals with modifications, and updates inventory.

    Args:
        project_id (None | str | Unset): Project/Tenant ID (optional, defaults to user's project)
        x_api_key (None | str | Unset):
        x_tenant_id (None | str | Unset): Tenant ID header
        body (OrderModel): Complete order with variant/modification support

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
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
    body: OrderModel,
    project_id: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
    x_tenant_id: None | str | Unset = UNSET,
) -> Any | HTTPValidationError | None:
    """Create a new order

     Create a new order with variant and modification support.
    Requires authentication (customer user or backend user via API key).
    Customer users can only create orders for themselves.
    Validates variants exist, calculates line totals with modifications, and updates inventory.

    Args:
        project_id (None | str | Unset): Project/Tenant ID (optional, defaults to user's project)
        x_api_key (None | str | Unset):
        x_tenant_id (None | str | Unset): Tenant ID header
        body (OrderModel): Complete order with variant/modification support

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        body=body,
        project_id=project_id,
        x_api_key=x_api_key,
        x_tenant_id=x_tenant_id,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    body: OrderModel,
    project_id: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
    x_tenant_id: None | str | Unset = UNSET,
) -> Response[Any | HTTPValidationError]:
    """Create a new order

     Create a new order with variant and modification support.
    Requires authentication (customer user or backend user via API key).
    Customer users can only create orders for themselves.
    Validates variants exist, calculates line totals with modifications, and updates inventory.

    Args:
        project_id (None | str | Unset): Project/Tenant ID (optional, defaults to user's project)
        x_api_key (None | str | Unset):
        x_tenant_id (None | str | Unset): Tenant ID header
        body (OrderModel): Complete order with variant/modification support

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
        project_id=project_id,
        x_api_key=x_api_key,
        x_tenant_id=x_tenant_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    body: OrderModel,
    project_id: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
    x_tenant_id: None | str | Unset = UNSET,
) -> Any | HTTPValidationError | None:
    """Create a new order

     Create a new order with variant and modification support.
    Requires authentication (customer user or backend user via API key).
    Customer users can only create orders for themselves.
    Validates variants exist, calculates line totals with modifications, and updates inventory.

    Args:
        project_id (None | str | Unset): Project/Tenant ID (optional, defaults to user's project)
        x_api_key (None | str | Unset):
        x_tenant_id (None | str | Unset): Tenant ID header
        body (OrderModel): Complete order with variant/modification support

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            project_id=project_id,
            x_api_key=x_api_key,
            x_tenant_id=x_tenant_id,
        )
    ).parsed
