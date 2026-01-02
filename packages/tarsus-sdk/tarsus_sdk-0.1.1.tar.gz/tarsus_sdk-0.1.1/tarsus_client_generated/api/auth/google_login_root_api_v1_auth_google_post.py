from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.google_auth_request import GoogleAuthRequest
from ...models.http_validation_error import HTTPValidationError
from ...models.token import Token
from ...types import Response


def _get_kwargs(
    *,
    body: GoogleAuthRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/auth/google",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | Token | None:
    if response.status_code == 200:
        response_200 = Token.from_dict(response.json())

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
) -> Response[HTTPValidationError | Token]:
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
) -> Response[HTTPValidationError | Token]:
    r"""Authenticate customer user with Google OAuth

     Authenticate a customer user using Google OAuth2 ID token.

    This endpoint is for customer/end-user authentication (not backend users).
    For backend user Google OAuth, use `/api/v1/backend/auth/google`.

    **How it works:**
    1. Client obtains Google ID token from Google Sign-In
    2. Client sends ID token to this endpoint in request body: `{\"token\": \"id_token_here\"}`
    3. Server verifies the token with Google
    4. Server finds or creates the customer user
    5. Server returns a JWT token for API access

    **Auto-Registration:**
    - If user doesn't exist, they are automatically created
    - Email is marked as verified for Google OAuth users
    - User profile (name) is populated from Google account
    - Google OAuth users don't require a password

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
      \"user_id\": \"user_id_here\"
    }
    ```

    **Required Configuration:**
    - `GOOGLE_OAUTH_CLIENT_ID`: OAuth 2.0 Client ID from Google Cloud Console
    - This should be the same Client ID used by the client application

    **For Developers:**
    This endpoint can be used by external applications to implement Google Sign-In
    for their customers. The endpoint automatically handles user creation and
    returns a JWT token that can be used for authenticated API requests.

    **Example Usage:**
    ```javascript
    // After getting Google ID token from Google Sign-In
    const response = await fetch('https://api.example.com/api/v1/auth/google', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        token: googleIdToken
      })
    });
    const data = await response.json();
    // Use data.access_token for authenticated API requests
    ```

    Args:
        body (GoogleAuthRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | Token]
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
) -> HTTPValidationError | Token | None:
    r"""Authenticate customer user with Google OAuth

     Authenticate a customer user using Google OAuth2 ID token.

    This endpoint is for customer/end-user authentication (not backend users).
    For backend user Google OAuth, use `/api/v1/backend/auth/google`.

    **How it works:**
    1. Client obtains Google ID token from Google Sign-In
    2. Client sends ID token to this endpoint in request body: `{\"token\": \"id_token_here\"}`
    3. Server verifies the token with Google
    4. Server finds or creates the customer user
    5. Server returns a JWT token for API access

    **Auto-Registration:**
    - If user doesn't exist, they are automatically created
    - Email is marked as verified for Google OAuth users
    - User profile (name) is populated from Google account
    - Google OAuth users don't require a password

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
      \"user_id\": \"user_id_here\"
    }
    ```

    **Required Configuration:**
    - `GOOGLE_OAUTH_CLIENT_ID`: OAuth 2.0 Client ID from Google Cloud Console
    - This should be the same Client ID used by the client application

    **For Developers:**
    This endpoint can be used by external applications to implement Google Sign-In
    for their customers. The endpoint automatically handles user creation and
    returns a JWT token that can be used for authenticated API requests.

    **Example Usage:**
    ```javascript
    // After getting Google ID token from Google Sign-In
    const response = await fetch('https://api.example.com/api/v1/auth/google', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        token: googleIdToken
      })
    });
    const data = await response.json();
    // Use data.access_token for authenticated API requests
    ```

    Args:
        body (GoogleAuthRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | Token
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: GoogleAuthRequest,
) -> Response[HTTPValidationError | Token]:
    r"""Authenticate customer user with Google OAuth

     Authenticate a customer user using Google OAuth2 ID token.

    This endpoint is for customer/end-user authentication (not backend users).
    For backend user Google OAuth, use `/api/v1/backend/auth/google`.

    **How it works:**
    1. Client obtains Google ID token from Google Sign-In
    2. Client sends ID token to this endpoint in request body: `{\"token\": \"id_token_here\"}`
    3. Server verifies the token with Google
    4. Server finds or creates the customer user
    5. Server returns a JWT token for API access

    **Auto-Registration:**
    - If user doesn't exist, they are automatically created
    - Email is marked as verified for Google OAuth users
    - User profile (name) is populated from Google account
    - Google OAuth users don't require a password

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
      \"user_id\": \"user_id_here\"
    }
    ```

    **Required Configuration:**
    - `GOOGLE_OAUTH_CLIENT_ID`: OAuth 2.0 Client ID from Google Cloud Console
    - This should be the same Client ID used by the client application

    **For Developers:**
    This endpoint can be used by external applications to implement Google Sign-In
    for their customers. The endpoint automatically handles user creation and
    returns a JWT token that can be used for authenticated API requests.

    **Example Usage:**
    ```javascript
    // After getting Google ID token from Google Sign-In
    const response = await fetch('https://api.example.com/api/v1/auth/google', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        token: googleIdToken
      })
    });
    const data = await response.json();
    // Use data.access_token for authenticated API requests
    ```

    Args:
        body (GoogleAuthRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | Token]
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
) -> HTTPValidationError | Token | None:
    r"""Authenticate customer user with Google OAuth

     Authenticate a customer user using Google OAuth2 ID token.

    This endpoint is for customer/end-user authentication (not backend users).
    For backend user Google OAuth, use `/api/v1/backend/auth/google`.

    **How it works:**
    1. Client obtains Google ID token from Google Sign-In
    2. Client sends ID token to this endpoint in request body: `{\"token\": \"id_token_here\"}`
    3. Server verifies the token with Google
    4. Server finds or creates the customer user
    5. Server returns a JWT token for API access

    **Auto-Registration:**
    - If user doesn't exist, they are automatically created
    - Email is marked as verified for Google OAuth users
    - User profile (name) is populated from Google account
    - Google OAuth users don't require a password

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
      \"user_id\": \"user_id_here\"
    }
    ```

    **Required Configuration:**
    - `GOOGLE_OAUTH_CLIENT_ID`: OAuth 2.0 Client ID from Google Cloud Console
    - This should be the same Client ID used by the client application

    **For Developers:**
    This endpoint can be used by external applications to implement Google Sign-In
    for their customers. The endpoint automatically handles user creation and
    returns a JWT token that can be used for authenticated API requests.

    **Example Usage:**
    ```javascript
    // After getting Google ID token from Google Sign-In
    const response = await fetch('https://api.example.com/api/v1/auth/google', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        token: googleIdToken
      })
    });
    const data = await response.json();
    // Use data.access_token for authenticated API requests
    ```

    Args:
        body (GoogleAuthRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | Token
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
