from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.platform_key_create import PlatformKeyCreate
from ...models.platform_key_public import PlatformKeyPublic
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: PlatformKeyCreate,
    x_api_key: None | str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_api_key, Unset):
        headers["X-API-Key"] = x_api_key

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/backend/platform-keys",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | HTTPValidationError | PlatformKeyPublic | None:
    if response.status_code == 201:
        response_201 = PlatformKeyPublic.from_dict(response.json())

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
) -> Response[Any | HTTPValidationError | PlatformKeyPublic]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    body: PlatformKeyCreate,
    x_api_key: None | str | Unset = UNSET,
) -> Response[Any | HTTPValidationError | PlatformKeyPublic]:
    """Create a new platform key

     Creates a new platform key.
    Only super_admin and admin can create platform keys.
    Only one key of each type can exist.

    Args:
        x_api_key (None | str | Unset):
        body (PlatformKeyCreate): Model for creating a new platform key

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError | PlatformKeyPublic]
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
    body: PlatformKeyCreate,
    x_api_key: None | str | Unset = UNSET,
) -> Any | HTTPValidationError | PlatformKeyPublic | None:
    """Create a new platform key

     Creates a new platform key.
    Only super_admin and admin can create platform keys.
    Only one key of each type can exist.

    Args:
        x_api_key (None | str | Unset):
        body (PlatformKeyCreate): Model for creating a new platform key

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError | PlatformKeyPublic
    """

    return sync_detailed(
        client=client,
        body=body,
        x_api_key=x_api_key,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    body: PlatformKeyCreate,
    x_api_key: None | str | Unset = UNSET,
) -> Response[Any | HTTPValidationError | PlatformKeyPublic]:
    """Create a new platform key

     Creates a new platform key.
    Only super_admin and admin can create platform keys.
    Only one key of each type can exist.

    Args:
        x_api_key (None | str | Unset):
        body (PlatformKeyCreate): Model for creating a new platform key

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError | PlatformKeyPublic]
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
    body: PlatformKeyCreate,
    x_api_key: None | str | Unset = UNSET,
) -> Any | HTTPValidationError | PlatformKeyPublic | None:
    """Create a new platform key

     Creates a new platform key.
    Only super_admin and admin can create platform keys.
    Only one key of each type can exist.

    Args:
        x_api_key (None | str | Unset):
        body (PlatformKeyCreate): Model for creating a new platform key

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError | PlatformKeyPublic
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            x_api_key=x_api_key,
        )
    ).parsed
