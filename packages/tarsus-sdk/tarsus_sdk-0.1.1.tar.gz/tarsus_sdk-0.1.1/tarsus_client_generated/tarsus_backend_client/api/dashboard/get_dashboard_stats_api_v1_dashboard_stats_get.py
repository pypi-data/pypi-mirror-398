from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_dashboard_stats_api_v1_dashboard_stats_get_response_get_dashboard_stats_api_v1_dashboard_stats_get import (
    GetDashboardStatsApiV1DashboardStatsGetResponseGetDashboardStatsApiV1DashboardStatsGet,
)
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    project_id: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
    x_tenant_id: None | str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_api_key, Unset):
        headers["X-API-Key"] = x_api_key

    if not isinstance(x_tenant_id, Unset):
        headers["X-Tenant-ID"] = x_tenant_id

    params: dict[str, Any] = {}

    json_project_id: None | str | Unset
    if isinstance(project_id, Unset):
        json_project_id = UNSET
    else:
        json_project_id = project_id
    params["project_id"] = json_project_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/dashboard/stats",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GetDashboardStatsApiV1DashboardStatsGetResponseGetDashboardStatsApiV1DashboardStatsGet | HTTPValidationError | None
):
    if response.status_code == 200:
        response_200 = GetDashboardStatsApiV1DashboardStatsGetResponseGetDashboardStatsApiV1DashboardStatsGet.from_dict(
            response.json()
        )

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
) -> Response[
    GetDashboardStatsApiV1DashboardStatsGetResponseGetDashboardStatsApiV1DashboardStatsGet | HTTPValidationError
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    project_id: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
    x_tenant_id: None | str | Unset = UNSET,
) -> Response[
    GetDashboardStatsApiV1DashboardStatsGetResponseGetDashboardStatsApiV1DashboardStatsGet | HTTPValidationError
]:
    """Get dashboard statistics

     Get comprehensive dashboard statistics for the current project/tenant.

    All statistics are scoped to the tenant_id determined by:
    1. project_id query parameter (if provided)
    2. X-Tenant-ID header (if provided)
    3. Backend user's first/active project (if backend user)

    Includes:
    - Product statistics (tenant-scoped): total, active, variants, stock levels
    - Order statistics (tenant-scoped): total, pending, revenue, status breakdown
    - User statistics (tenant-scoped via orders): users who have placed orders in this tenant
    - API usage statistics (scoped to backend_user_id): request counts, response times, etc.

    Returns:
    - tenant_id: The tenant/project ID these statistics are scoped to
    - scoped_to_tenant: Flag indicating all stats are tenant-scoped
    - All statistics sections with tenant_id included for verification

    Args:
        project_id (None | str | Unset): Project/Tenant ID (optional, defaults to user's project)
        x_api_key (None | str | Unset):
        x_tenant_id (None | str | Unset): Tenant ID header

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetDashboardStatsApiV1DashboardStatsGetResponseGetDashboardStatsApiV1DashboardStatsGet | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        x_api_key=x_api_key,
        x_tenant_id=x_tenant_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    project_id: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
    x_tenant_id: None | str | Unset = UNSET,
) -> (
    GetDashboardStatsApiV1DashboardStatsGetResponseGetDashboardStatsApiV1DashboardStatsGet | HTTPValidationError | None
):
    """Get dashboard statistics

     Get comprehensive dashboard statistics for the current project/tenant.

    All statistics are scoped to the tenant_id determined by:
    1. project_id query parameter (if provided)
    2. X-Tenant-ID header (if provided)
    3. Backend user's first/active project (if backend user)

    Includes:
    - Product statistics (tenant-scoped): total, active, variants, stock levels
    - Order statistics (tenant-scoped): total, pending, revenue, status breakdown
    - User statistics (tenant-scoped via orders): users who have placed orders in this tenant
    - API usage statistics (scoped to backend_user_id): request counts, response times, etc.

    Returns:
    - tenant_id: The tenant/project ID these statistics are scoped to
    - scoped_to_tenant: Flag indicating all stats are tenant-scoped
    - All statistics sections with tenant_id included for verification

    Args:
        project_id (None | str | Unset): Project/Tenant ID (optional, defaults to user's project)
        x_api_key (None | str | Unset):
        x_tenant_id (None | str | Unset): Tenant ID header

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetDashboardStatsApiV1DashboardStatsGetResponseGetDashboardStatsApiV1DashboardStatsGet | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        project_id=project_id,
        x_api_key=x_api_key,
        x_tenant_id=x_tenant_id,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    project_id: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
    x_tenant_id: None | str | Unset = UNSET,
) -> Response[
    GetDashboardStatsApiV1DashboardStatsGetResponseGetDashboardStatsApiV1DashboardStatsGet | HTTPValidationError
]:
    """Get dashboard statistics

     Get comprehensive dashboard statistics for the current project/tenant.

    All statistics are scoped to the tenant_id determined by:
    1. project_id query parameter (if provided)
    2. X-Tenant-ID header (if provided)
    3. Backend user's first/active project (if backend user)

    Includes:
    - Product statistics (tenant-scoped): total, active, variants, stock levels
    - Order statistics (tenant-scoped): total, pending, revenue, status breakdown
    - User statistics (tenant-scoped via orders): users who have placed orders in this tenant
    - API usage statistics (scoped to backend_user_id): request counts, response times, etc.

    Returns:
    - tenant_id: The tenant/project ID these statistics are scoped to
    - scoped_to_tenant: Flag indicating all stats are tenant-scoped
    - All statistics sections with tenant_id included for verification

    Args:
        project_id (None | str | Unset): Project/Tenant ID (optional, defaults to user's project)
        x_api_key (None | str | Unset):
        x_tenant_id (None | str | Unset): Tenant ID header

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetDashboardStatsApiV1DashboardStatsGetResponseGetDashboardStatsApiV1DashboardStatsGet | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        x_api_key=x_api_key,
        x_tenant_id=x_tenant_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    project_id: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
    x_tenant_id: None | str | Unset = UNSET,
) -> (
    GetDashboardStatsApiV1DashboardStatsGetResponseGetDashboardStatsApiV1DashboardStatsGet | HTTPValidationError | None
):
    """Get dashboard statistics

     Get comprehensive dashboard statistics for the current project/tenant.

    All statistics are scoped to the tenant_id determined by:
    1. project_id query parameter (if provided)
    2. X-Tenant-ID header (if provided)
    3. Backend user's first/active project (if backend user)

    Includes:
    - Product statistics (tenant-scoped): total, active, variants, stock levels
    - Order statistics (tenant-scoped): total, pending, revenue, status breakdown
    - User statistics (tenant-scoped via orders): users who have placed orders in this tenant
    - API usage statistics (scoped to backend_user_id): request counts, response times, etc.

    Returns:
    - tenant_id: The tenant/project ID these statistics are scoped to
    - scoped_to_tenant: Flag indicating all stats are tenant-scoped
    - All statistics sections with tenant_id included for verification

    Args:
        project_id (None | str | Unset): Project/Tenant ID (optional, defaults to user's project)
        x_api_key (None | str | Unset):
        x_tenant_id (None | str | Unset): Tenant ID header

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetDashboardStatsApiV1DashboardStatsGetResponseGetDashboardStatsApiV1DashboardStatsGet | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            project_id=project_id,
            x_api_key=x_api_key,
            x_tenant_id=x_tenant_id,
        )
    ).parsed
