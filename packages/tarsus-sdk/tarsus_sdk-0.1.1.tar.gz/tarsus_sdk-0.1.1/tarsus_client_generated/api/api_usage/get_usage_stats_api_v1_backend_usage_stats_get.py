from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.api_usage_stats import APIUsageStats
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    api_key_id: None | str | Unset = UNSET,
    start_date: None | str | Unset = UNSET,
    end_date: None | str | Unset = UNSET,
    days: int | Unset = 30,
    x_api_key: None | str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_api_key, Unset):
        headers["X-API-Key"] = x_api_key

    params: dict[str, Any] = {}

    json_api_key_id: None | str | Unset
    if isinstance(api_key_id, Unset):
        json_api_key_id = UNSET
    else:
        json_api_key_id = api_key_id
    params["api_key_id"] = json_api_key_id

    json_start_date: None | str | Unset
    if isinstance(start_date, Unset):
        json_start_date = UNSET
    else:
        json_start_date = start_date
    params["start_date"] = json_start_date

    json_end_date: None | str | Unset
    if isinstance(end_date, Unset):
        json_end_date = UNSET
    else:
        json_end_date = end_date
    params["end_date"] = json_end_date

    params["days"] = days

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/backend/usage/stats",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> APIUsageStats | Any | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = APIUsageStats.from_dict(response.json())

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
) -> Response[APIUsageStats | Any | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    api_key_id: None | str | Unset = UNSET,
    start_date: None | str | Unset = UNSET,
    end_date: None | str | Unset = UNSET,
    days: int | Unset = 30,
    x_api_key: None | str | Unset = UNSET,
) -> Response[APIUsageStats | Any | HTTPValidationError]:
    """Get API usage statistics

     Get aggregated API usage statistics.

    - **super_admin** and **admin**: Can see stats for all users/keys
    - **developer**: Can only see stats for their own API keys

    Args:
        api_key_id (None | str | Unset): Filter by API key ID
        start_date (None | str | Unset): Start date (ISO format)
        end_date (None | str | Unset): End date (ISO format)
        days (int | Unset): Number of days to look back (if dates not provided) Default: 30.
        x_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[APIUsageStats | Any | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        api_key_id=api_key_id,
        start_date=start_date,
        end_date=end_date,
        days=days,
        x_api_key=x_api_key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    api_key_id: None | str | Unset = UNSET,
    start_date: None | str | Unset = UNSET,
    end_date: None | str | Unset = UNSET,
    days: int | Unset = 30,
    x_api_key: None | str | Unset = UNSET,
) -> APIUsageStats | Any | HTTPValidationError | None:
    """Get API usage statistics

     Get aggregated API usage statistics.

    - **super_admin** and **admin**: Can see stats for all users/keys
    - **developer**: Can only see stats for their own API keys

    Args:
        api_key_id (None | str | Unset): Filter by API key ID
        start_date (None | str | Unset): Start date (ISO format)
        end_date (None | str | Unset): End date (ISO format)
        days (int | Unset): Number of days to look back (if dates not provided) Default: 30.
        x_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        APIUsageStats | Any | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        api_key_id=api_key_id,
        start_date=start_date,
        end_date=end_date,
        days=days,
        x_api_key=x_api_key,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    api_key_id: None | str | Unset = UNSET,
    start_date: None | str | Unset = UNSET,
    end_date: None | str | Unset = UNSET,
    days: int | Unset = 30,
    x_api_key: None | str | Unset = UNSET,
) -> Response[APIUsageStats | Any | HTTPValidationError]:
    """Get API usage statistics

     Get aggregated API usage statistics.

    - **super_admin** and **admin**: Can see stats for all users/keys
    - **developer**: Can only see stats for their own API keys

    Args:
        api_key_id (None | str | Unset): Filter by API key ID
        start_date (None | str | Unset): Start date (ISO format)
        end_date (None | str | Unset): End date (ISO format)
        days (int | Unset): Number of days to look back (if dates not provided) Default: 30.
        x_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[APIUsageStats | Any | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        api_key_id=api_key_id,
        start_date=start_date,
        end_date=end_date,
        days=days,
        x_api_key=x_api_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    api_key_id: None | str | Unset = UNSET,
    start_date: None | str | Unset = UNSET,
    end_date: None | str | Unset = UNSET,
    days: int | Unset = 30,
    x_api_key: None | str | Unset = UNSET,
) -> APIUsageStats | Any | HTTPValidationError | None:
    """Get API usage statistics

     Get aggregated API usage statistics.

    - **super_admin** and **admin**: Can see stats for all users/keys
    - **developer**: Can only see stats for their own API keys

    Args:
        api_key_id (None | str | Unset): Filter by API key ID
        start_date (None | str | Unset): Start date (ISO format)
        end_date (None | str | Unset): End date (ISO format)
        days (int | Unset): Number of days to look back (if dates not provided) Default: 30.
        x_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        APIUsageStats | Any | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            api_key_id=api_key_id,
            start_date=start_date,
            end_date=end_date,
            days=days,
            x_api_key=x_api_key,
        )
    ).parsed
