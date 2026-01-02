from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.google_auth_request import GoogleAuthRequest
from ...models.http_validation_error import HTTPValidationError
from ...models.token_response import TokenResponse
from ...types import Response


def _get_kwargs(
    *,
    body: GoogleAuthRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/backend/auth/google",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | TokenResponse | None:
    if response.status_code == 200:
        response_200 = TokenResponse.from_dict(response.json())

        return response_200

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[HTTPValidationError | TokenResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: GoogleAuthRequest,
) -> Response[HTTPValidationError | TokenResponse]:
    r"""Authenticate backend user with Google OAuth

     Authenticate a backend user (platform admin/developer) using Google OAuth2 ID token.

    This endpoint is for backend user authentication (platform admins/developers).
    For customer/end-user Google OAuth, use `/api/v1/auth/google`.

    **How it works:**
    1. Client obtains Google ID token from Google Sign-In
    2. Client sends ID token to this endpoint in request body: `{\"token\": \"id_token_here\"}`
    3. Server verifies the token with Google
    4. Server finds or creates the backend user (auto-registration)
    5. Server returns a JWT token for the application

    **Auto-Registration:**
    - If the user doesn't exist, they will be automatically created
    - First user gets `super_admin` role
    - Subsequent users get `developer` role (or based on ALLOW_BACKEND_REGISTRATION setting)
    - Email is automatically verified for Google OAuth users
    - Terms and privacy acceptance is handled via Google OAuth consent flow

    **Request Body:**
    ```json
    {
      \"token\": \"google_oauth2_id_token\"
    }
    ```

    **Response:**
    ```json
    {
      \"access_token\": \"jwt_token_here\",
      \"token_type\": \"bearer\",
      \"user_id\": \"user_id_here\",
      \"role\": \"super_admin\" | \"admin\" | \"developer\"
    }
    ```

    **Required Configuration:**
    - `GOOGLE_OAUTH_CLIENT_ID`: OAuth 2.0 Client ID from Google Cloud Console
    - This should be the same Client ID used by the admin frontend

    **For Developers:**
    This endpoint is used by the platform admin interface for Google Sign-In.
    External developers implementing their own apps should use `/api/v1/auth/google`
    for customer authentication.

    Args:
        body (GoogleAuthRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TokenResponse]
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
    body: GoogleAuthRequest,
) -> HTTPValidationError | TokenResponse | None:
    r"""Authenticate backend user with Google OAuth

     Authenticate a backend user (platform admin/developer) using Google OAuth2 ID token.

    This endpoint is for backend user authentication (platform admins/developers).
    For customer/end-user Google OAuth, use `/api/v1/auth/google`.

    **How it works:**
    1. Client obtains Google ID token from Google Sign-In
    2. Client sends ID token to this endpoint in request body: `{\"token\": \"id_token_here\"}`
    3. Server verifies the token with Google
    4. Server finds or creates the backend user (auto-registration)
    5. Server returns a JWT token for the application

    **Auto-Registration:**
    - If the user doesn't exist, they will be automatically created
    - First user gets `super_admin` role
    - Subsequent users get `developer` role (or based on ALLOW_BACKEND_REGISTRATION setting)
    - Email is automatically verified for Google OAuth users
    - Terms and privacy acceptance is handled via Google OAuth consent flow

    **Request Body:**
    ```json
    {
      \"token\": \"google_oauth2_id_token\"
    }
    ```

    **Response:**
    ```json
    {
      \"access_token\": \"jwt_token_here\",
      \"token_type\": \"bearer\",
      \"user_id\": \"user_id_here\",
      \"role\": \"super_admin\" | \"admin\" | \"developer\"
    }
    ```

    **Required Configuration:**
    - `GOOGLE_OAUTH_CLIENT_ID`: OAuth 2.0 Client ID from Google Cloud Console
    - This should be the same Client ID used by the admin frontend

    **For Developers:**
    This endpoint is used by the platform admin interface for Google Sign-In.
    External developers implementing their own apps should use `/api/v1/auth/google`
    for customer authentication.

    Args:
        body (GoogleAuthRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TokenResponse
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: GoogleAuthRequest,
) -> Response[HTTPValidationError | TokenResponse]:
    r"""Authenticate backend user with Google OAuth

     Authenticate a backend user (platform admin/developer) using Google OAuth2 ID token.

    This endpoint is for backend user authentication (platform admins/developers).
    For customer/end-user Google OAuth, use `/api/v1/auth/google`.

    **How it works:**
    1. Client obtains Google ID token from Google Sign-In
    2. Client sends ID token to this endpoint in request body: `{\"token\": \"id_token_here\"}`
    3. Server verifies the token with Google
    4. Server finds or creates the backend user (auto-registration)
    5. Server returns a JWT token for the application

    **Auto-Registration:**
    - If the user doesn't exist, they will be automatically created
    - First user gets `super_admin` role
    - Subsequent users get `developer` role (or based on ALLOW_BACKEND_REGISTRATION setting)
    - Email is automatically verified for Google OAuth users
    - Terms and privacy acceptance is handled via Google OAuth consent flow

    **Request Body:**
    ```json
    {
      \"token\": \"google_oauth2_id_token\"
    }
    ```

    **Response:**
    ```json
    {
      \"access_token\": \"jwt_token_here\",
      \"token_type\": \"bearer\",
      \"user_id\": \"user_id_here\",
      \"role\": \"super_admin\" | \"admin\" | \"developer\"
    }
    ```

    **Required Configuration:**
    - `GOOGLE_OAUTH_CLIENT_ID`: OAuth 2.0 Client ID from Google Cloud Console
    - This should be the same Client ID used by the admin frontend

    **For Developers:**
    This endpoint is used by the platform admin interface for Google Sign-In.
    External developers implementing their own apps should use `/api/v1/auth/google`
    for customer authentication.

    Args:
        body (GoogleAuthRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TokenResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: GoogleAuthRequest,
) -> HTTPValidationError | TokenResponse | None:
    r"""Authenticate backend user with Google OAuth

     Authenticate a backend user (platform admin/developer) using Google OAuth2 ID token.

    This endpoint is for backend user authentication (platform admins/developers).
    For customer/end-user Google OAuth, use `/api/v1/auth/google`.

    **How it works:**
    1. Client obtains Google ID token from Google Sign-In
    2. Client sends ID token to this endpoint in request body: `{\"token\": \"id_token_here\"}`
    3. Server verifies the token with Google
    4. Server finds or creates the backend user (auto-registration)
    5. Server returns a JWT token for the application

    **Auto-Registration:**
    - If the user doesn't exist, they will be automatically created
    - First user gets `super_admin` role
    - Subsequent users get `developer` role (or based on ALLOW_BACKEND_REGISTRATION setting)
    - Email is automatically verified for Google OAuth users
    - Terms and privacy acceptance is handled via Google OAuth consent flow

    **Request Body:**
    ```json
    {
      \"token\": \"google_oauth2_id_token\"
    }
    ```

    **Response:**
    ```json
    {
      \"access_token\": \"jwt_token_here\",
      \"token_type\": \"bearer\",
      \"user_id\": \"user_id_here\",
      \"role\": \"super_admin\" | \"admin\" | \"developer\"
    }
    ```

    **Required Configuration:**
    - `GOOGLE_OAUTH_CLIENT_ID`: OAuth 2.0 Client ID from Google Cloud Console
    - This should be the same Client ID used by the admin frontend

    **For Developers:**
    This endpoint is used by the platform admin interface for Google Sign-In.
    External developers implementing their own apps should use `/api/v1/auth/google`
    for customer authentication.

    Args:
        body (GoogleAuthRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TokenResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
