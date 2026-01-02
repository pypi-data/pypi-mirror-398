from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    report_type: str,
    tenant_id: None | str | Unset = UNSET,
    format_: str | Unset = "json",
    start_date: None | str | Unset = UNSET,
    end_date: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_api_key, Unset):
        headers["X-API-Key"] = x_api_key

    params: dict[str, Any] = {}

    params["report_type"] = report_type

    json_tenant_id: None | str | Unset
    if isinstance(tenant_id, Unset):
        json_tenant_id = UNSET
    else:
        json_tenant_id = tenant_id
    params["tenant_id"] = json_tenant_id

    params["format"] = format_

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

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/backend/admin/reports/export",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = response.json()
        return response_200

    if response.status_code == 403:
        response_403 = cast(Any, None)
        return response_403

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Any | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    report_type: str,
    tenant_id: None | str | Unset = UNSET,
    format_: str | Unset = "json",
    start_date: None | str | Unset = UNSET,
    end_date: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
) -> Response[Any | HTTPValidationError]:
    """Export Report

     Export usage report as CSV or JSON.
    Requires super_admin role.

    Args:
        report_type (str): Report type: 'tenant' or 'system'
        tenant_id (None | str | Unset): Tenant ID (required for tenant reports)
        format_ (str | Unset): Export format: 'json' or 'csv' Default: 'json'.
        start_date (None | str | Unset): Start date (ISO format)
        end_date (None | str | Unset): End date (ISO format)
        x_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        report_type=report_type,
        tenant_id=tenant_id,
        format_=format_,
        start_date=start_date,
        end_date=end_date,
        x_api_key=x_api_key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    report_type: str,
    tenant_id: None | str | Unset = UNSET,
    format_: str | Unset = "json",
    start_date: None | str | Unset = UNSET,
    end_date: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
) -> Any | HTTPValidationError | None:
    """Export Report

     Export usage report as CSV or JSON.
    Requires super_admin role.

    Args:
        report_type (str): Report type: 'tenant' or 'system'
        tenant_id (None | str | Unset): Tenant ID (required for tenant reports)
        format_ (str | Unset): Export format: 'json' or 'csv' Default: 'json'.
        start_date (None | str | Unset): Start date (ISO format)
        end_date (None | str | Unset): End date (ISO format)
        x_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        report_type=report_type,
        tenant_id=tenant_id,
        format_=format_,
        start_date=start_date,
        end_date=end_date,
        x_api_key=x_api_key,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    report_type: str,
    tenant_id: None | str | Unset = UNSET,
    format_: str | Unset = "json",
    start_date: None | str | Unset = UNSET,
    end_date: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
) -> Response[Any | HTTPValidationError]:
    """Export Report

     Export usage report as CSV or JSON.
    Requires super_admin role.

    Args:
        report_type (str): Report type: 'tenant' or 'system'
        tenant_id (None | str | Unset): Tenant ID (required for tenant reports)
        format_ (str | Unset): Export format: 'json' or 'csv' Default: 'json'.
        start_date (None | str | Unset): Start date (ISO format)
        end_date (None | str | Unset): End date (ISO format)
        x_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        report_type=report_type,
        tenant_id=tenant_id,
        format_=format_,
        start_date=start_date,
        end_date=end_date,
        x_api_key=x_api_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    report_type: str,
    tenant_id: None | str | Unset = UNSET,
    format_: str | Unset = "json",
    start_date: None | str | Unset = UNSET,
    end_date: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
) -> Any | HTTPValidationError | None:
    """Export Report

     Export usage report as CSV or JSON.
    Requires super_admin role.

    Args:
        report_type (str): Report type: 'tenant' or 'system'
        tenant_id (None | str | Unset): Tenant ID (required for tenant reports)
        format_ (str | Unset): Export format: 'json' or 'csv' Default: 'json'.
        start_date (None | str | Unset): Start date (ISO format)
        end_date (None | str | Unset): End date (ISO format)
        x_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            report_type=report_type,
            tenant_id=tenant_id,
            format_=format_,
            start_date=start_date,
            end_date=end_date,
            x_api_key=x_api_key,
        )
    ).parsed
