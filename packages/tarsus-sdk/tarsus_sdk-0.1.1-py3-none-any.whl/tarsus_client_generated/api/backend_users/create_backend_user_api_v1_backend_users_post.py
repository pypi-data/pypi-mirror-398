from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.backend_user_create import BackendUserCreate
from ...models.backend_user_out import BackendUserOut
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: BackendUserCreate,
    x_api_key: None | str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_api_key, Unset):
        headers["X-API-Key"] = x_api_key

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/backend/users",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | BackendUserOut | HTTPValidationError | None:
    if response.status_code == 201:
        response_201 = BackendUserOut.from_dict(response.json())

        return response_201

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
) -> Response[Any | BackendUserOut | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    body: BackendUserCreate,
    x_api_key: None | str | Unset = UNSET,
) -> Response[Any | BackendUserOut | HTTPValidationError]:
    """Create a new backend user

     Creates a new backend user.
    Requires super_admin or admin role.
    Only super_admin can create new super_admin users.

    Args:
        x_api_key (None | str | Unset):
        body (BackendUserCreate): Model for creating a new backend user.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | BackendUserOut | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
        x_api_key=x_api_key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    body: BackendUserCreate,
    x_api_key: None | str | Unset = UNSET,
) -> Any | BackendUserOut | HTTPValidationError | None:
    """Create a new backend user

     Creates a new backend user.
    Requires super_admin or admin role.
    Only super_admin can create new super_admin users.

    Args:
        x_api_key (None | str | Unset):
        body (BackendUserCreate): Model for creating a new backend user.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | BackendUserOut | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        body=body,
        x_api_key=x_api_key,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    body: BackendUserCreate,
    x_api_key: None | str | Unset = UNSET,
) -> Response[Any | BackendUserOut | HTTPValidationError]:
    """Create a new backend user

     Creates a new backend user.
    Requires super_admin or admin role.
    Only super_admin can create new super_admin users.

    Args:
        x_api_key (None | str | Unset):
        body (BackendUserCreate): Model for creating a new backend user.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | BackendUserOut | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
        x_api_key=x_api_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    body: BackendUserCreate,
    x_api_key: None | str | Unset = UNSET,
) -> Any | BackendUserOut | HTTPValidationError | None:
    """Create a new backend user

     Creates a new backend user.
    Requires super_admin or admin role.
    Only super_admin can create new super_admin users.

    Args:
        x_api_key (None | str | Unset):
        body (BackendUserCreate): Model for creating a new backend user.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | BackendUserOut | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            x_api_key=x_api_key,
        )
    ).parsed
