from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.product_model import ProductModel
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    id: None | str | Unset = UNSET,
    skip: int | Unset = 0,
    limit: int | Unset = 100,
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

    json_id: None | str | Unset
    if isinstance(id, Unset):
        json_id = UNSET
    else:
        json_id = id
    params["id"] = json_id

    params["skip"] = skip

    params["limit"] = limit

    json_project_id: None | str | Unset
    if isinstance(project_id, Unset):
        json_project_id = UNSET
    else:
        json_project_id = project_id
    params["project_id"] = json_project_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/products",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | HTTPValidationError | list[ProductModel] | None:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = ProductModel.from_dict(response_200_item_data)

            response_200.append(response_200_item)

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
) -> Response[Any | HTTPValidationError | list[ProductModel]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    id: None | str | Unset = UNSET,
    skip: int | Unset = 0,
    limit: int | Unset = 100,
    project_id: None | str | Unset = UNSET,
    x_tenant_id: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
) -> Response[Any | HTTPValidationError | list[ProductModel]]:
    """List all products or get single product by query param

     Retrieves a list of all products or single product by ID query param.
    Public endpoint - no authentication required for browsing.
    - **id**: Optional product ID to get single product.
    - **skip**: Number of products to skip.
    - **limit**: Maximum number of products to return.

    Args:
        id (None | str | Unset):
        skip (int | Unset):  Default: 0.
        limit (int | Unset):  Default: 100.
        project_id (None | str | Unset): Project/Tenant ID (optional, defaults to user's project)
        x_tenant_id (None | str | Unset): Tenant ID header
        x_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError | list[ProductModel]]
    """

    kwargs = _get_kwargs(
        id=id,
        skip=skip,
        limit=limit,
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
    id: None | str | Unset = UNSET,
    skip: int | Unset = 0,
    limit: int | Unset = 100,
    project_id: None | str | Unset = UNSET,
    x_tenant_id: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
) -> Any | HTTPValidationError | list[ProductModel] | None:
    """List all products or get single product by query param

     Retrieves a list of all products or single product by ID query param.
    Public endpoint - no authentication required for browsing.
    - **id**: Optional product ID to get single product.
    - **skip**: Number of products to skip.
    - **limit**: Maximum number of products to return.

    Args:
        id (None | str | Unset):
        skip (int | Unset):  Default: 0.
        limit (int | Unset):  Default: 100.
        project_id (None | str | Unset): Project/Tenant ID (optional, defaults to user's project)
        x_tenant_id (None | str | Unset): Tenant ID header
        x_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError | list[ProductModel]
    """

    return sync_detailed(
        client=client,
        id=id,
        skip=skip,
        limit=limit,
        project_id=project_id,
        x_tenant_id=x_tenant_id,
        x_api_key=x_api_key,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    id: None | str | Unset = UNSET,
    skip: int | Unset = 0,
    limit: int | Unset = 100,
    project_id: None | str | Unset = UNSET,
    x_tenant_id: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
) -> Response[Any | HTTPValidationError | list[ProductModel]]:
    """List all products or get single product by query param

     Retrieves a list of all products or single product by ID query param.
    Public endpoint - no authentication required for browsing.
    - **id**: Optional product ID to get single product.
    - **skip**: Number of products to skip.
    - **limit**: Maximum number of products to return.

    Args:
        id (None | str | Unset):
        skip (int | Unset):  Default: 0.
        limit (int | Unset):  Default: 100.
        project_id (None | str | Unset): Project/Tenant ID (optional, defaults to user's project)
        x_tenant_id (None | str | Unset): Tenant ID header
        x_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError | list[ProductModel]]
    """

    kwargs = _get_kwargs(
        id=id,
        skip=skip,
        limit=limit,
        project_id=project_id,
        x_tenant_id=x_tenant_id,
        x_api_key=x_api_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    id: None | str | Unset = UNSET,
    skip: int | Unset = 0,
    limit: int | Unset = 100,
    project_id: None | str | Unset = UNSET,
    x_tenant_id: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
) -> Any | HTTPValidationError | list[ProductModel] | None:
    """List all products or get single product by query param

     Retrieves a list of all products or single product by ID query param.
    Public endpoint - no authentication required for browsing.
    - **id**: Optional product ID to get single product.
    - **skip**: Number of products to skip.
    - **limit**: Maximum number of products to return.

    Args:
        id (None | str | Unset):
        skip (int | Unset):  Default: 0.
        limit (int | Unset):  Default: 100.
        project_id (None | str | Unset): Project/Tenant ID (optional, defaults to user's project)
        x_tenant_id (None | str | Unset): Tenant ID header
        x_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError | list[ProductModel]
    """

    return (
        await asyncio_detailed(
            client=client,
            id=id,
            skip=skip,
            limit=limit,
            project_id=project_id,
            x_tenant_id=x_tenant_id,
            x_api_key=x_api_key,
        )
    ).parsed
