from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    tenant_id: str,
    project_id: str,
    *,
    prefix: None | str | Unset = "",
    x_api_key: None | str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_api_key, Unset):
        headers["X-API-Key"] = x_api_key

    params: dict[str, Any] = {}

    json_prefix: None | str | Unset
    if isinstance(prefix, Unset):
        json_prefix = UNSET
    else:
        json_prefix = prefix
    params["prefix"] = json_prefix

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/backend/admin/tenants/{tenant_id}/projects/{project_id}/storage/files".format(
            tenant_id=quote(str(tenant_id), safe=""),
            project_id=quote(str(project_id), safe=""),
        ),
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
    tenant_id: str,
    project_id: str,
    *,
    client: AuthenticatedClient,
    prefix: None | str | Unset = "",
    x_api_key: None | str | Unset = UNSET,
) -> Response[Any | HTTPValidationError]:
    """List Project Files

     List files in a project's bucket.

    Args:
        tenant_id (str):
        project_id (str):
        prefix (None | str | Unset):  Default: ''.
        x_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        tenant_id=tenant_id,
        project_id=project_id,
        prefix=prefix,
        x_api_key=x_api_key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    tenant_id: str,
    project_id: str,
    *,
    client: AuthenticatedClient,
    prefix: None | str | Unset = "",
    x_api_key: None | str | Unset = UNSET,
) -> Any | HTTPValidationError | None:
    """List Project Files

     List files in a project's bucket.

    Args:
        tenant_id (str):
        project_id (str):
        prefix (None | str | Unset):  Default: ''.
        x_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError
    """

    return sync_detailed(
        tenant_id=tenant_id,
        project_id=project_id,
        client=client,
        prefix=prefix,
        x_api_key=x_api_key,
    ).parsed


async def asyncio_detailed(
    tenant_id: str,
    project_id: str,
    *,
    client: AuthenticatedClient,
    prefix: None | str | Unset = "",
    x_api_key: None | str | Unset = UNSET,
) -> Response[Any | HTTPValidationError]:
    """List Project Files

     List files in a project's bucket.

    Args:
        tenant_id (str):
        project_id (str):
        prefix (None | str | Unset):  Default: ''.
        x_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        tenant_id=tenant_id,
        project_id=project_id,
        prefix=prefix,
        x_api_key=x_api_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    tenant_id: str,
    project_id: str,
    *,
    client: AuthenticatedClient,
    prefix: None | str | Unset = "",
    x_api_key: None | str | Unset = UNSET,
) -> Any | HTTPValidationError | None:
    """List Project Files

     List files in a project's bucket.

    Args:
        tenant_id (str):
        project_id (str):
        prefix (None | str | Unset):  Default: ''.
        x_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            tenant_id=tenant_id,
            project_id=project_id,
            client=client,
            prefix=prefix,
            x_api_key=x_api_key,
        )
    ).parsed
