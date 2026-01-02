from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.backend_user_create import BackendUserCreate
from ...models.backend_user_out import BackendUserOut
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response


def _get_kwargs(
    *,
    body: BackendUserCreate,
    secret: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    params: dict[str, Any] = {}

    params["secret"] = secret

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/backend/users/create-staging-admin",
        "params": params,
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
    client: AuthenticatedClient | Client,
    body: BackendUserCreate,
    secret: str,
) -> Response[Any | BackendUserOut | HTTPValidationError]:
    """[TEMPORARY] Create staging super_admin (one-time setup)

     TEMPORARY endpoint to create a super_admin for staging/testing.
    This bypasses normal authentication requirements.

    Secret key must match STAGING_ADMIN_SECRET environment variable.
    This endpoint should be removed or disabled in production.

    Args:
        secret (str): Secret key for one-time admin creation
        body (BackendUserCreate): Model for creating a new backend user.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | BackendUserOut | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
        secret=secret,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: BackendUserCreate,
    secret: str,
) -> Any | BackendUserOut | HTTPValidationError | None:
    """[TEMPORARY] Create staging super_admin (one-time setup)

     TEMPORARY endpoint to create a super_admin for staging/testing.
    This bypasses normal authentication requirements.

    Secret key must match STAGING_ADMIN_SECRET environment variable.
    This endpoint should be removed or disabled in production.

    Args:
        secret (str): Secret key for one-time admin creation
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
        secret=secret,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: BackendUserCreate,
    secret: str,
) -> Response[Any | BackendUserOut | HTTPValidationError]:
    """[TEMPORARY] Create staging super_admin (one-time setup)

     TEMPORARY endpoint to create a super_admin for staging/testing.
    This bypasses normal authentication requirements.

    Secret key must match STAGING_ADMIN_SECRET environment variable.
    This endpoint should be removed or disabled in production.

    Args:
        secret (str): Secret key for one-time admin creation
        body (BackendUserCreate): Model for creating a new backend user.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | BackendUserOut | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
        secret=secret,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: BackendUserCreate,
    secret: str,
) -> Any | BackendUserOut | HTTPValidationError | None:
    """[TEMPORARY] Create staging super_admin (one-time setup)

     TEMPORARY endpoint to create a super_admin for staging/testing.
    This bypasses normal authentication requirements.

    Secret key must match STAGING_ADMIN_SECRET environment variable.
    This endpoint should be removed or disabled in production.

    Args:
        secret (str): Secret key for one-time admin creation
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
            secret=secret,
        )
    ).parsed
