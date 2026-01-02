from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.platform_key_public import PlatformKeyPublic
from ...types import UNSET, Response, Unset


def _get_kwargs(
    key_id: str,
    *,
    x_api_key: None | str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_api_key, Unset):
        headers["X-API-Key"] = x_api_key

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/backend/platform-keys/{key_id}".format(
            key_id=quote(str(key_id), safe=""),
        ),
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | HTTPValidationError | PlatformKeyPublic | None:
    if response.status_code == 200:
        response_200 = PlatformKeyPublic.from_dict(response.json())

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
) -> Response[Any | HTTPValidationError | PlatformKeyPublic]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    key_id: str,
    *,
    client: AuthenticatedClient,
    x_api_key: None | str | Unset = UNSET,
) -> Response[Any | HTTPValidationError | PlatformKeyPublic]:
    """Get a specific platform key

     Gets a specific platform key by ID.
    Credentials are never returned.

    Args:
        key_id (str):
        x_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError | PlatformKeyPublic]
    """

    kwargs = _get_kwargs(
        key_id=key_id,
        x_api_key=x_api_key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    key_id: str,
    *,
    client: AuthenticatedClient,
    x_api_key: None | str | Unset = UNSET,
) -> Any | HTTPValidationError | PlatformKeyPublic | None:
    """Get a specific platform key

     Gets a specific platform key by ID.
    Credentials are never returned.

    Args:
        key_id (str):
        x_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError | PlatformKeyPublic
    """

    return sync_detailed(
        key_id=key_id,
        client=client,
        x_api_key=x_api_key,
    ).parsed


async def asyncio_detailed(
    key_id: str,
    *,
    client: AuthenticatedClient,
    x_api_key: None | str | Unset = UNSET,
) -> Response[Any | HTTPValidationError | PlatformKeyPublic]:
    """Get a specific platform key

     Gets a specific platform key by ID.
    Credentials are never returned.

    Args:
        key_id (str):
        x_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError | PlatformKeyPublic]
    """

    kwargs = _get_kwargs(
        key_id=key_id,
        x_api_key=x_api_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    key_id: str,
    *,
    client: AuthenticatedClient,
    x_api_key: None | str | Unset = UNSET,
) -> Any | HTTPValidationError | PlatformKeyPublic | None:
    """Get a specific platform key

     Gets a specific platform key by ID.
    Credentials are never returned.

    Args:
        key_id (str):
        x_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError | PlatformKeyPublic
    """

    return (
        await asyncio_detailed(
            key_id=key_id,
            client=client,
            x_api_key=x_api_key,
        )
    ).parsed
