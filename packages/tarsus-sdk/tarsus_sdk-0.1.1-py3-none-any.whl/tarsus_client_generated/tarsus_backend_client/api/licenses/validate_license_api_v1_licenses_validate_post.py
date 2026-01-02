from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.license_validation_response import LicenseValidationResponse
from ...models.validate_license_request import ValidateLicenseRequest
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: ValidateLicenseRequest,
    project_id: None | str | Unset = UNSET,
    x_tenant_id: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_tenant_id, Unset):
        headers["X-Tenant-ID"] = x_tenant_id

    if not isinstance(x_api_key, Unset):
        headers["X-API-Key"] = x_api_key

    params: dict[str, Any] = {}

    json_project_id: None | str | Unset
    if isinstance(project_id, Unset):
        json_project_id = UNSET
    else:
        json_project_id = project_id
    params["project_id"] = json_project_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/licenses/validate",
        "params": params,
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | HTTPValidationError | LicenseValidationResponse | None:
    if response.status_code == 200:
        response_200 = LicenseValidationResponse.from_dict(response.json())

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
) -> Response[Any | HTTPValidationError | LicenseValidationResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    body: ValidateLicenseRequest,
    project_id: None | str | Unset = UNSET,
    x_tenant_id: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
) -> Response[Any | HTTPValidationError | LicenseValidationResponse]:
    """Validate a license key

     Validate a license key and check if it can be activated.
    Does not activate the license - use /activate endpoint for that.

    Args:
        project_id (None | str | Unset): Project/Tenant ID (optional, defaults to user's project)
        x_tenant_id (None | str | Unset): Tenant ID header
        x_api_key (None | str | Unset):
        body (ValidateLicenseRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError | LicenseValidationResponse]
    """

    kwargs = _get_kwargs(
        body=body,
        project_id=project_id,
        x_tenant_id=x_tenant_id,
        x_api_key=x_api_key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    body: ValidateLicenseRequest,
    project_id: None | str | Unset = UNSET,
    x_tenant_id: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
) -> Any | HTTPValidationError | LicenseValidationResponse | None:
    """Validate a license key

     Validate a license key and check if it can be activated.
    Does not activate the license - use /activate endpoint for that.

    Args:
        project_id (None | str | Unset): Project/Tenant ID (optional, defaults to user's project)
        x_tenant_id (None | str | Unset): Tenant ID header
        x_api_key (None | str | Unset):
        body (ValidateLicenseRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError | LicenseValidationResponse
    """

    return sync_detailed(
        client=client,
        body=body,
        project_id=project_id,
        x_tenant_id=x_tenant_id,
        x_api_key=x_api_key,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    body: ValidateLicenseRequest,
    project_id: None | str | Unset = UNSET,
    x_tenant_id: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
) -> Response[Any | HTTPValidationError | LicenseValidationResponse]:
    """Validate a license key

     Validate a license key and check if it can be activated.
    Does not activate the license - use /activate endpoint for that.

    Args:
        project_id (None | str | Unset): Project/Tenant ID (optional, defaults to user's project)
        x_tenant_id (None | str | Unset): Tenant ID header
        x_api_key (None | str | Unset):
        body (ValidateLicenseRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError | LicenseValidationResponse]
    """

    kwargs = _get_kwargs(
        body=body,
        project_id=project_id,
        x_tenant_id=x_tenant_id,
        x_api_key=x_api_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    body: ValidateLicenseRequest,
    project_id: None | str | Unset = UNSET,
    x_tenant_id: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
) -> Any | HTTPValidationError | LicenseValidationResponse | None:
    """Validate a license key

     Validate a license key and check if it can be activated.
    Does not activate the license - use /activate endpoint for that.

    Args:
        project_id (None | str | Unset): Project/Tenant ID (optional, defaults to user's project)
        x_tenant_id (None | str | Unset): Tenant ID header
        x_api_key (None | str | Unset):
        body (ValidateLicenseRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError | LicenseValidationResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            project_id=project_id,
            x_tenant_id=x_tenant_id,
            x_api_key=x_api_key,
        )
    ).parsed
