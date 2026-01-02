from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.update_user_full_api_v1_users_user_id_put_updates import UpdateUserFullApiV1UsersUserIdPutUpdates
from ...models.user_public import UserPublic
from ...types import UNSET, Response, Unset


def _get_kwargs(
    user_id: str,
    *,
    body: UpdateUserFullApiV1UsersUserIdPutUpdates,
    x_api_key: None | str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_api_key, Unset):
        headers["X-API-Key"] = x_api_key

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": "/api/v1/users/{user_id}".format(
            user_id=quote(str(user_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | HTTPValidationError | UserPublic | None:
    if response.status_code == 200:
        response_200 = UserPublic.from_dict(response.json())

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
) -> Response[Any | HTTPValidationError | UserPublic]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    user_id: str,
    *,
    client: AuthenticatedClient,
    body: UpdateUserFullApiV1UsersUserIdPutUpdates,
    x_api_key: None | str | Unset = UNSET,
) -> Response[Any | HTTPValidationError | UserPublic]:
    """Update user info (full update)

    Args:
        user_id (str):
        x_api_key (None | str | Unset):
        body (UpdateUserFullApiV1UsersUserIdPutUpdates):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError | UserPublic]
    """

    kwargs = _get_kwargs(
        user_id=user_id,
        body=body,
        x_api_key=x_api_key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    user_id: str,
    *,
    client: AuthenticatedClient,
    body: UpdateUserFullApiV1UsersUserIdPutUpdates,
    x_api_key: None | str | Unset = UNSET,
) -> Any | HTTPValidationError | UserPublic | None:
    """Update user info (full update)

    Args:
        user_id (str):
        x_api_key (None | str | Unset):
        body (UpdateUserFullApiV1UsersUserIdPutUpdates):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError | UserPublic
    """

    return sync_detailed(
        user_id=user_id,
        client=client,
        body=body,
        x_api_key=x_api_key,
    ).parsed


async def asyncio_detailed(
    user_id: str,
    *,
    client: AuthenticatedClient,
    body: UpdateUserFullApiV1UsersUserIdPutUpdates,
    x_api_key: None | str | Unset = UNSET,
) -> Response[Any | HTTPValidationError | UserPublic]:
    """Update user info (full update)

    Args:
        user_id (str):
        x_api_key (None | str | Unset):
        body (UpdateUserFullApiV1UsersUserIdPutUpdates):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError | UserPublic]
    """

    kwargs = _get_kwargs(
        user_id=user_id,
        body=body,
        x_api_key=x_api_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    user_id: str,
    *,
    client: AuthenticatedClient,
    body: UpdateUserFullApiV1UsersUserIdPutUpdates,
    x_api_key: None | str | Unset = UNSET,
) -> Any | HTTPValidationError | UserPublic | None:
    """Update user info (full update)

    Args:
        user_id (str):
        x_api_key (None | str | Unset):
        body (UpdateUserFullApiV1UsersUserIdPutUpdates):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError | UserPublic
    """

    return (
        await asyncio_detailed(
            user_id=user_id,
            client=client,
            body=body,
            x_api_key=x_api_key,
        )
    ).parsed
