from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.backend_user_create import BackendUserCreate
from ...models.backend_user_out import BackendUserOut
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    *,
    body: BackendUserCreate,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/backend/auth/register",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> BackendUserOut | HTTPValidationError | None:
    if response.status_code == 201:
        response_201 = BackendUserOut.from_dict(response.json())

        return response_201

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[BackendUserOut | HTTPValidationError]:
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
) -> Response[BackendUserOut | HTTPValidationError]:
    """Register Backend User

     Register a new backend/system user.

    **Password Requirements:**
    - Minimum 8 characters
    - Maximum 72 characters

    **Initial Setup (First User):**
    - If no backend users exist, allows registration of any role (including super_admin)
    - This enables initial system setup

    **After First User:**
    - If ALLOW_BACKEND_REGISTRATION is enabled, registration is allowed for all users
    - Otherwise, registration is disabled and new users must be created by admins via
    /api/v1/backend/users
    - The admin endpoint requires admin authentication

    **Configuration:**
    - Set ALLOW_BACKEND_REGISTRATION=true in environment to enable open registration
    - Default is False for security (requires admin creation via /api/v1/backend/users)

    **Development Note:**
    - For development, you can register the first user here
    - For production, consider creating the first super_admin manually via database

    Args:
        body (BackendUserCreate): Model for creating a new backend user.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[BackendUserOut | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: BackendUserCreate,
) -> BackendUserOut | HTTPValidationError | None:
    """Register Backend User

     Register a new backend/system user.

    **Password Requirements:**
    - Minimum 8 characters
    - Maximum 72 characters

    **Initial Setup (First User):**
    - If no backend users exist, allows registration of any role (including super_admin)
    - This enables initial system setup

    **After First User:**
    - If ALLOW_BACKEND_REGISTRATION is enabled, registration is allowed for all users
    - Otherwise, registration is disabled and new users must be created by admins via
    /api/v1/backend/users
    - The admin endpoint requires admin authentication

    **Configuration:**
    - Set ALLOW_BACKEND_REGISTRATION=true in environment to enable open registration
    - Default is False for security (requires admin creation via /api/v1/backend/users)

    **Development Note:**
    - For development, you can register the first user here
    - For production, consider creating the first super_admin manually via database

    Args:
        body (BackendUserCreate): Model for creating a new backend user.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        BackendUserOut | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: BackendUserCreate,
) -> Response[BackendUserOut | HTTPValidationError]:
    """Register Backend User

     Register a new backend/system user.

    **Password Requirements:**
    - Minimum 8 characters
    - Maximum 72 characters

    **Initial Setup (First User):**
    - If no backend users exist, allows registration of any role (including super_admin)
    - This enables initial system setup

    **After First User:**
    - If ALLOW_BACKEND_REGISTRATION is enabled, registration is allowed for all users
    - Otherwise, registration is disabled and new users must be created by admins via
    /api/v1/backend/users
    - The admin endpoint requires admin authentication

    **Configuration:**
    - Set ALLOW_BACKEND_REGISTRATION=true in environment to enable open registration
    - Default is False for security (requires admin creation via /api/v1/backend/users)

    **Development Note:**
    - For development, you can register the first user here
    - For production, consider creating the first super_admin manually via database

    Args:
        body (BackendUserCreate): Model for creating a new backend user.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[BackendUserOut | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: BackendUserCreate,
) -> BackendUserOut | HTTPValidationError | None:
    """Register Backend User

     Register a new backend/system user.

    **Password Requirements:**
    - Minimum 8 characters
    - Maximum 72 characters

    **Initial Setup (First User):**
    - If no backend users exist, allows registration of any role (including super_admin)
    - This enables initial system setup

    **After First User:**
    - If ALLOW_BACKEND_REGISTRATION is enabled, registration is allowed for all users
    - Otherwise, registration is disabled and new users must be created by admins via
    /api/v1/backend/users
    - The admin endpoint requires admin authentication

    **Configuration:**
    - Set ALLOW_BACKEND_REGISTRATION=true in environment to enable open registration
    - Default is False for security (requires admin creation via /api/v1/backend/users)

    **Development Note:**
    - For development, you can register the first user here
    - For production, consider creating the first super_admin manually via database

    Args:
        body (BackendUserCreate): Model for creating a new backend user.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        BackendUserOut | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
