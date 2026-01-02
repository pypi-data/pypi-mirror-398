from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.enforce_collection_schema_api_v1_collections_collection_name_schema_enforce_post_body_type_0 import (
    EnforceCollectionSchemaApiV1CollectionsCollectionNameSchemaEnforcePostBodyType0,
)
from ...models.enforced_schema import EnforcedSchema
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    collection_name: str,
    *,
    body: EnforceCollectionSchemaApiV1CollectionsCollectionNameSchemaEnforcePostBodyType0 | None | Unset = UNSET,
    validate_existing: bool | Unset = True,
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

    params["validate_existing"] = validate_existing

    json_project_id: None | str | Unset
    if isinstance(project_id, Unset):
        json_project_id = UNSET
    else:
        json_project_id = project_id
    params["project_id"] = json_project_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/collections/{collection_name}/schema/enforce".format(
            collection_name=quote(str(collection_name), safe=""),
        ),
        "params": params,
    }

    if isinstance(
        body,
        EnforceCollectionSchemaApiV1CollectionsCollectionNameSchemaEnforcePostBodyType0,
    ):
        _kwargs["json"] = body.to_dict()
    else:
        _kwargs["json"] = body

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | EnforcedSchema | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = EnforcedSchema.from_dict(response.json())

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
) -> Response[Any | EnforcedSchema | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    collection_name: str,
    *,
    client: AuthenticatedClient,
    body: EnforceCollectionSchemaApiV1CollectionsCollectionNameSchemaEnforcePostBodyType0 | None | Unset = UNSET,
    validate_existing: bool | Unset = True,
    project_id: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
    x_tenant_id: None | str | Unset = UNSET,
) -> Response[Any | EnforcedSchema | HTTPValidationError]:
    """Enforce a schema on a collection

     Enforce a schema on a collection.

    If schema_definition is not provided, uses the latest proposal.
    Validates all existing data if validate_existing is true.

    Args:
        collection_name (str):
        validate_existing (bool | Unset):  Default: True.
        project_id (None | str | Unset): Project/Tenant ID (optional, defaults to user's project)
        x_api_key (None | str | Unset):
        x_tenant_id (None | str | Unset): Tenant ID header
        body (EnforceCollectionSchemaApiV1CollectionsCollectionNameSchemaEnforcePostBodyType0 |
            None | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | EnforcedSchema | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        collection_name=collection_name,
        body=body,
        validate_existing=validate_existing,
        project_id=project_id,
        x_api_key=x_api_key,
        x_tenant_id=x_tenant_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    collection_name: str,
    *,
    client: AuthenticatedClient,
    body: EnforceCollectionSchemaApiV1CollectionsCollectionNameSchemaEnforcePostBodyType0 | None | Unset = UNSET,
    validate_existing: bool | Unset = True,
    project_id: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
    x_tenant_id: None | str | Unset = UNSET,
) -> Any | EnforcedSchema | HTTPValidationError | None:
    """Enforce a schema on a collection

     Enforce a schema on a collection.

    If schema_definition is not provided, uses the latest proposal.
    Validates all existing data if validate_existing is true.

    Args:
        collection_name (str):
        validate_existing (bool | Unset):  Default: True.
        project_id (None | str | Unset): Project/Tenant ID (optional, defaults to user's project)
        x_api_key (None | str | Unset):
        x_tenant_id (None | str | Unset): Tenant ID header
        body (EnforceCollectionSchemaApiV1CollectionsCollectionNameSchemaEnforcePostBodyType0 |
            None | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | EnforcedSchema | HTTPValidationError
    """

    return sync_detailed(
        collection_name=collection_name,
        client=client,
        body=body,
        validate_existing=validate_existing,
        project_id=project_id,
        x_api_key=x_api_key,
        x_tenant_id=x_tenant_id,
    ).parsed


async def asyncio_detailed(
    collection_name: str,
    *,
    client: AuthenticatedClient,
    body: EnforceCollectionSchemaApiV1CollectionsCollectionNameSchemaEnforcePostBodyType0 | None | Unset = UNSET,
    validate_existing: bool | Unset = True,
    project_id: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
    x_tenant_id: None | str | Unset = UNSET,
) -> Response[Any | EnforcedSchema | HTTPValidationError]:
    """Enforce a schema on a collection

     Enforce a schema on a collection.

    If schema_definition is not provided, uses the latest proposal.
    Validates all existing data if validate_existing is true.

    Args:
        collection_name (str):
        validate_existing (bool | Unset):  Default: True.
        project_id (None | str | Unset): Project/Tenant ID (optional, defaults to user's project)
        x_api_key (None | str | Unset):
        x_tenant_id (None | str | Unset): Tenant ID header
        body (EnforceCollectionSchemaApiV1CollectionsCollectionNameSchemaEnforcePostBodyType0 |
            None | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | EnforcedSchema | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        collection_name=collection_name,
        body=body,
        validate_existing=validate_existing,
        project_id=project_id,
        x_api_key=x_api_key,
        x_tenant_id=x_tenant_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    collection_name: str,
    *,
    client: AuthenticatedClient,
    body: EnforceCollectionSchemaApiV1CollectionsCollectionNameSchemaEnforcePostBodyType0 | None | Unset = UNSET,
    validate_existing: bool | Unset = True,
    project_id: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
    x_tenant_id: None | str | Unset = UNSET,
) -> Any | EnforcedSchema | HTTPValidationError | None:
    """Enforce a schema on a collection

     Enforce a schema on a collection.

    If schema_definition is not provided, uses the latest proposal.
    Validates all existing data if validate_existing is true.

    Args:
        collection_name (str):
        validate_existing (bool | Unset):  Default: True.
        project_id (None | str | Unset): Project/Tenant ID (optional, defaults to user's project)
        x_api_key (None | str | Unset):
        x_tenant_id (None | str | Unset): Tenant ID header
        body (EnforceCollectionSchemaApiV1CollectionsCollectionNameSchemaEnforcePostBodyType0 |
            None | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | EnforcedSchema | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            collection_name=collection_name,
            client=client,
            body=body,
            validate_existing=validate_existing,
            project_id=project_id,
            x_api_key=x_api_key,
            x_tenant_id=x_tenant_id,
        )
    ).parsed
