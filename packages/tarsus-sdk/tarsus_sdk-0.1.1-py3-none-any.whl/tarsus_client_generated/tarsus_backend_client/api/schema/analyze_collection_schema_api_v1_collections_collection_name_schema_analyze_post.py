from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.schema_proposal import SchemaProposal
from ...types import UNSET, Response, Unset


def _get_kwargs(
    collection_name: str,
    *,
    sample_size: int | Unset = 50,
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

    params["sample_size"] = sample_size

    json_project_id: None | str | Unset
    if isinstance(project_id, Unset):
        json_project_id = UNSET
    else:
        json_project_id = project_id
    params["project_id"] = json_project_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/collections/{collection_name}/schema/analyze".format(
            collection_name=quote(str(collection_name), safe=""),
        ),
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | HTTPValidationError | SchemaProposal | None:
    if response.status_code == 200:
        response_200 = SchemaProposal.from_dict(response.json())

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
) -> Response[Any | HTTPValidationError | SchemaProposal]:
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
    sample_size: int | Unset = 50,
    project_id: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
    x_tenant_id: None | str | Unset = UNSET,
) -> Response[Any | HTTPValidationError | SchemaProposal]:
    """Analyze collection and generate schema proposal

     Analyze a collection and generate a JSON Schema proposal.

    This endpoint:
    1. Samples records from the collection
    2. Uses LLM to infer a JSON Schema
    3. Detects conflicts and breaking changes
    4. Saves the proposal for later enforcement

    - **collection_name**: Collection to analyze
    - **sample_size**: Number of records to sample (default: 50, max: 100)

    Args:
        collection_name (str):
        sample_size (int | Unset):  Default: 50.
        project_id (None | str | Unset): Project/Tenant ID (optional, defaults to user's project)
        x_api_key (None | str | Unset):
        x_tenant_id (None | str | Unset): Tenant ID header

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError | SchemaProposal]
    """

    kwargs = _get_kwargs(
        collection_name=collection_name,
        sample_size=sample_size,
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
    sample_size: int | Unset = 50,
    project_id: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
    x_tenant_id: None | str | Unset = UNSET,
) -> Any | HTTPValidationError | SchemaProposal | None:
    """Analyze collection and generate schema proposal

     Analyze a collection and generate a JSON Schema proposal.

    This endpoint:
    1. Samples records from the collection
    2. Uses LLM to infer a JSON Schema
    3. Detects conflicts and breaking changes
    4. Saves the proposal for later enforcement

    - **collection_name**: Collection to analyze
    - **sample_size**: Number of records to sample (default: 50, max: 100)

    Args:
        collection_name (str):
        sample_size (int | Unset):  Default: 50.
        project_id (None | str | Unset): Project/Tenant ID (optional, defaults to user's project)
        x_api_key (None | str | Unset):
        x_tenant_id (None | str | Unset): Tenant ID header

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError | SchemaProposal
    """

    return sync_detailed(
        collection_name=collection_name,
        client=client,
        sample_size=sample_size,
        project_id=project_id,
        x_api_key=x_api_key,
        x_tenant_id=x_tenant_id,
    ).parsed


async def asyncio_detailed(
    collection_name: str,
    *,
    client: AuthenticatedClient,
    sample_size: int | Unset = 50,
    project_id: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
    x_tenant_id: None | str | Unset = UNSET,
) -> Response[Any | HTTPValidationError | SchemaProposal]:
    """Analyze collection and generate schema proposal

     Analyze a collection and generate a JSON Schema proposal.

    This endpoint:
    1. Samples records from the collection
    2. Uses LLM to infer a JSON Schema
    3. Detects conflicts and breaking changes
    4. Saves the proposal for later enforcement

    - **collection_name**: Collection to analyze
    - **sample_size**: Number of records to sample (default: 50, max: 100)

    Args:
        collection_name (str):
        sample_size (int | Unset):  Default: 50.
        project_id (None | str | Unset): Project/Tenant ID (optional, defaults to user's project)
        x_api_key (None | str | Unset):
        x_tenant_id (None | str | Unset): Tenant ID header

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError | SchemaProposal]
    """

    kwargs = _get_kwargs(
        collection_name=collection_name,
        sample_size=sample_size,
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
    sample_size: int | Unset = 50,
    project_id: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
    x_tenant_id: None | str | Unset = UNSET,
) -> Any | HTTPValidationError | SchemaProposal | None:
    """Analyze collection and generate schema proposal

     Analyze a collection and generate a JSON Schema proposal.

    This endpoint:
    1. Samples records from the collection
    2. Uses LLM to infer a JSON Schema
    3. Detects conflicts and breaking changes
    4. Saves the proposal for later enforcement

    - **collection_name**: Collection to analyze
    - **sample_size**: Number of records to sample (default: 50, max: 100)

    Args:
        collection_name (str):
        sample_size (int | Unset):  Default: 50.
        project_id (None | str | Unset): Project/Tenant ID (optional, defaults to user's project)
        x_api_key (None | str | Unset):
        x_tenant_id (None | str | Unset): Tenant ID header

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError | SchemaProposal
    """

    return (
        await asyncio_detailed(
            collection_name=collection_name,
            client=client,
            sample_size=sample_size,
            project_id=project_id,
            x_api_key=x_api_key,
            x_tenant_id=x_tenant_id,
        )
    ).parsed
