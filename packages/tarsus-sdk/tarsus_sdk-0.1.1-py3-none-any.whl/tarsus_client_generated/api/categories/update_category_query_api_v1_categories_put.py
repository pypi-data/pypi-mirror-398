from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.category_model import CategoryModel
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: CategoryModel,
    id: str,
    x_api_key: None | str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_api_key, Unset):
        headers["X-API-Key"] = x_api_key

    params: dict[str, Any] = {}

    params["id"] = id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": "/api/v1/categories/",
        "params": params,
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | CategoryModel | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = CategoryModel.from_dict(response.json())

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
) -> Response[Any | CategoryModel | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    body: CategoryModel,
    id: str,
    x_api_key: None | str | Unset = UNSET,
) -> Response[Any | CategoryModel | HTTPValidationError]:
    """Update Category Query

     Update category by query param.
    Requires admin or super_admin role.

    Args:
        id (str):
        x_api_key (None | str | Unset):
        body (CategoryModel): Pydantic model for a product category.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | CategoryModel | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
        id=id,
        x_api_key=x_api_key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    body: CategoryModel,
    id: str,
    x_api_key: None | str | Unset = UNSET,
) -> Any | CategoryModel | HTTPValidationError | None:
    """Update Category Query

     Update category by query param.
    Requires admin or super_admin role.

    Args:
        id (str):
        x_api_key (None | str | Unset):
        body (CategoryModel): Pydantic model for a product category.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | CategoryModel | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        body=body,
        id=id,
        x_api_key=x_api_key,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    body: CategoryModel,
    id: str,
    x_api_key: None | str | Unset = UNSET,
) -> Response[Any | CategoryModel | HTTPValidationError]:
    """Update Category Query

     Update category by query param.
    Requires admin or super_admin role.

    Args:
        id (str):
        x_api_key (None | str | Unset):
        body (CategoryModel): Pydantic model for a product category.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | CategoryModel | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
        id=id,
        x_api_key=x_api_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    body: CategoryModel,
    id: str,
    x_api_key: None | str | Unset = UNSET,
) -> Any | CategoryModel | HTTPValidationError | None:
    """Update Category Query

     Update category by query param.
    Requires admin or super_admin role.

    Args:
        id (str):
        x_api_key (None | str | Unset):
        body (CategoryModel): Pydantic model for a product category.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | CategoryModel | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            id=id,
            x_api_key=x_api_key,
        )
    ).parsed
