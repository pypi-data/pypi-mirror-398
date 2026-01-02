from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.api_key_public import APIKeyPublic
from ...models.api_key_update import APIKeyUpdate
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    key_id: str,
    *,
    body: APIKeyUpdate,
    x_api_key: None | str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_api_key, Unset):
        headers["X-API-Key"] = x_api_key

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": "/api/v1/backend/api-keys/{key_id}".format(
            key_id=quote(str(key_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> APIKeyPublic | Any | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = APIKeyPublic.from_dict(response.json())

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
) -> Response[APIKeyPublic | Any | HTTPValidationError]:
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
    body: APIKeyUpdate,
    x_api_key: None | str | Unset = UNSET,
) -> Response[APIKeyPublic | Any | HTTPValidationError]:
    """Update API key permissions

     Updates an API key's permissions (allowed_endpoints).
    The full key is never returned - only metadata.
    Developers can only update their own keys.

    Args:
        key_id (str):
        x_api_key (None | str | Unset):
        body (APIKeyUpdate): Model for updating an API key.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[APIKeyPublic | Any | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        key_id=key_id,
        body=body,
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
    body: APIKeyUpdate,
    x_api_key: None | str | Unset = UNSET,
) -> APIKeyPublic | Any | HTTPValidationError | None:
    """Update API key permissions

     Updates an API key's permissions (allowed_endpoints).
    The full key is never returned - only metadata.
    Developers can only update their own keys.

    Args:
        key_id (str):
        x_api_key (None | str | Unset):
        body (APIKeyUpdate): Model for updating an API key.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        APIKeyPublic | Any | HTTPValidationError
    """

    return sync_detailed(
        key_id=key_id,
        client=client,
        body=body,
        x_api_key=x_api_key,
    ).parsed


async def asyncio_detailed(
    key_id: str,
    *,
    client: AuthenticatedClient,
    body: APIKeyUpdate,
    x_api_key: None | str | Unset = UNSET,
) -> Response[APIKeyPublic | Any | HTTPValidationError]:
    """Update API key permissions

     Updates an API key's permissions (allowed_endpoints).
    The full key is never returned - only metadata.
    Developers can only update their own keys.

    Args:
        key_id (str):
        x_api_key (None | str | Unset):
        body (APIKeyUpdate): Model for updating an API key.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[APIKeyPublic | Any | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        key_id=key_id,
        body=body,
        x_api_key=x_api_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    key_id: str,
    *,
    client: AuthenticatedClient,
    body: APIKeyUpdate,
    x_api_key: None | str | Unset = UNSET,
) -> APIKeyPublic | Any | HTTPValidationError | None:
    """Update API key permissions

     Updates an API key's permissions (allowed_endpoints).
    The full key is never returned - only metadata.
    Developers can only update their own keys.

    Args:
        key_id (str):
        x_api_key (None | str | Unset):
        body (APIKeyUpdate): Model for updating an API key.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        APIKeyPublic | Any | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            key_id=key_id,
            client=client,
            body=body,
            x_api_key=x_api_key,
        )
    ).parsed
