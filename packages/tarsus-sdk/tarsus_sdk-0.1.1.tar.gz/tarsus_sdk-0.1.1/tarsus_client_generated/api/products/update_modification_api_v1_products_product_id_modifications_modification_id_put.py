from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.modification_definition_model import ModificationDefinitionModel
from ...models.modification_update_model import ModificationUpdateModel
from ...types import UNSET, Response, Unset


def _get_kwargs(
    product_id: str,
    modification_id: str,
    *,
    body: ModificationUpdateModel,
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
        "method": "put",
        "url": "/api/v1/products/{product_id}/modifications/{modification_id}".format(
            product_id=quote(str(product_id), safe=""),
            modification_id=quote(str(modification_id), safe=""),
        ),
        "params": params,
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | HTTPValidationError | ModificationDefinitionModel | None:
    if response.status_code == 200:
        response_200 = ModificationDefinitionModel.from_dict(response.json())

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
) -> Response[Any | HTTPValidationError | ModificationDefinitionModel]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    product_id: str,
    modification_id: str,
    *,
    client: AuthenticatedClient,
    body: ModificationUpdateModel,
    project_id: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
    x_tenant_id: None | str | Unset = UNSET,
) -> Response[Any | HTTPValidationError | ModificationDefinitionModel]:
    """Update an existing modification

     Updates an existing modification with the provided data.
    Requires backend user authentication.

    Args:
        product_id (str):
        modification_id (str):
        project_id (None | str | Unset): Project/Tenant ID (optional, defaults to user's project)
        x_api_key (None | str | Unset):
        x_tenant_id (None | str | Unset): Tenant ID header
        body (ModificationUpdateModel): Model for updating modifications

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError | ModificationDefinitionModel]
    """

    kwargs = _get_kwargs(
        product_id=product_id,
        modification_id=modification_id,
        body=body,
        project_id=project_id,
        x_api_key=x_api_key,
        x_tenant_id=x_tenant_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    product_id: str,
    modification_id: str,
    *,
    client: AuthenticatedClient,
    body: ModificationUpdateModel,
    project_id: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
    x_tenant_id: None | str | Unset = UNSET,
) -> Any | HTTPValidationError | ModificationDefinitionModel | None:
    """Update an existing modification

     Updates an existing modification with the provided data.
    Requires backend user authentication.

    Args:
        product_id (str):
        modification_id (str):
        project_id (None | str | Unset): Project/Tenant ID (optional, defaults to user's project)
        x_api_key (None | str | Unset):
        x_tenant_id (None | str | Unset): Tenant ID header
        body (ModificationUpdateModel): Model for updating modifications

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError | ModificationDefinitionModel
    """

    return sync_detailed(
        product_id=product_id,
        modification_id=modification_id,
        client=client,
        body=body,
        project_id=project_id,
        x_api_key=x_api_key,
        x_tenant_id=x_tenant_id,
    ).parsed


async def asyncio_detailed(
    product_id: str,
    modification_id: str,
    *,
    client: AuthenticatedClient,
    body: ModificationUpdateModel,
    project_id: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
    x_tenant_id: None | str | Unset = UNSET,
) -> Response[Any | HTTPValidationError | ModificationDefinitionModel]:
    """Update an existing modification

     Updates an existing modification with the provided data.
    Requires backend user authentication.

    Args:
        product_id (str):
        modification_id (str):
        project_id (None | str | Unset): Project/Tenant ID (optional, defaults to user's project)
        x_api_key (None | str | Unset):
        x_tenant_id (None | str | Unset): Tenant ID header
        body (ModificationUpdateModel): Model for updating modifications

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError | ModificationDefinitionModel]
    """

    kwargs = _get_kwargs(
        product_id=product_id,
        modification_id=modification_id,
        body=body,
        project_id=project_id,
        x_api_key=x_api_key,
        x_tenant_id=x_tenant_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    product_id: str,
    modification_id: str,
    *,
    client: AuthenticatedClient,
    body: ModificationUpdateModel,
    project_id: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
    x_tenant_id: None | str | Unset = UNSET,
) -> Any | HTTPValidationError | ModificationDefinitionModel | None:
    """Update an existing modification

     Updates an existing modification with the provided data.
    Requires backend user authentication.

    Args:
        product_id (str):
        modification_id (str):
        project_id (None | str | Unset): Project/Tenant ID (optional, defaults to user's project)
        x_api_key (None | str | Unset):
        x_tenant_id (None | str | Unset): Tenant ID header
        body (ModificationUpdateModel): Model for updating modifications

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError | ModificationDefinitionModel
    """

    return (
        await asyncio_detailed(
            product_id=product_id,
            modification_id=modification_id,
            client=client,
            body=body,
            project_id=project_id,
            x_api_key=x_api_key,
            x_tenant_id=x_tenant_id,
        )
    ).parsed
