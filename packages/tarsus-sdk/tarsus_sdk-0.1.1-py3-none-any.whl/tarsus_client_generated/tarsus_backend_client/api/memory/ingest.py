from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.ingest_body_type_0 import IngestBodyType0
from ...models.knowledge_chunk_model import KnowledgeChunkModel
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: IngestBodyType0 | None | Unset = UNSET,
    text: str,
    source: None | str | Unset = UNSET,
    source_type: None | str | Unset = UNSET,
    chunk_size: int | Unset = 500,
    chunk_overlap: int | Unset = 50,
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

    params["text"] = text

    json_source: None | str | Unset
    if isinstance(source, Unset):
        json_source = UNSET
    else:
        json_source = source
    params["source"] = json_source

    json_source_type: None | str | Unset
    if isinstance(source_type, Unset):
        json_source_type = UNSET
    else:
        json_source_type = source_type
    params["source_type"] = json_source_type

    params["chunk_size"] = chunk_size

    params["chunk_overlap"] = chunk_overlap

    json_project_id: None | str | Unset
    if isinstance(project_id, Unset):
        json_project_id = UNSET
    else:
        json_project_id = project_id
    params["project_id"] = json_project_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/memory/knowledge",
        "params": params,
    }

    if isinstance(body, IngestBodyType0):
        _kwargs["json"] = body.to_dict()
    else:
        _kwargs["json"] = body

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | HTTPValidationError | list[KnowledgeChunkModel] | None:
    if response.status_code == 201:
        response_201 = []
        _response_201 = response.json()
        for response_201_item_data in _response_201:
            response_201_item = KnowledgeChunkModel.from_dict(response_201_item_data)

            response_201.append(response_201_item)

        return response_201

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
) -> Response[Any | HTTPValidationError | list[KnowledgeChunkModel]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    body: IngestBodyType0 | None | Unset = UNSET,
    text: str,
    source: None | str | Unset = UNSET,
    source_type: None | str | Unset = UNSET,
    chunk_size: int | Unset = 500,
    chunk_overlap: int | Unset = 50,
    project_id: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
    x_tenant_id: None | str | Unset = UNSET,
) -> Response[Any | HTTPValidationError | list[KnowledgeChunkModel]]:
    """Ingest knowledge (text with automatic chunking)

     Ingest text knowledge with automatic chunking and embedding generation.

    The text will be split into overlapping chunks, each chunk will be embedded,
    and stored in Firestore for vector search.

    - **text**: The text content to store
    - **source**: Optional source identifier (e.g., filename, URL)
    - **source_type**: Type of source (e.g., 'pdf', 'markdown', 'text')
    - **chunk_size**: Target size for each chunk in tokens (default: 500)
    - **chunk_overlap**: Overlap between chunks in tokens (default: 50)
    - **metadata**: Additional metadata to store with chunks

    Args:
        text (str):
        source (None | str | Unset):
        source_type (None | str | Unset): Type of source (e.g., 'pdf', 'markdown', 'text')
        chunk_size (int | Unset): Target chunk size in tokens Default: 500.
        chunk_overlap (int | Unset): Overlap between chunks in tokens Default: 50.
        project_id (None | str | Unset): Project/Tenant ID (optional, defaults to user's project)
        x_api_key (None | str | Unset):
        x_tenant_id (None | str | Unset): Tenant ID header
        body (IngestBodyType0 | None | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError | list[KnowledgeChunkModel]]
    """

    kwargs = _get_kwargs(
        body=body,
        text=text,
        source=source,
        source_type=source_type,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
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
    body: IngestBodyType0 | None | Unset = UNSET,
    text: str,
    source: None | str | Unset = UNSET,
    source_type: None | str | Unset = UNSET,
    chunk_size: int | Unset = 500,
    chunk_overlap: int | Unset = 50,
    project_id: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
    x_tenant_id: None | str | Unset = UNSET,
) -> Any | HTTPValidationError | list[KnowledgeChunkModel] | None:
    """Ingest knowledge (text with automatic chunking)

     Ingest text knowledge with automatic chunking and embedding generation.

    The text will be split into overlapping chunks, each chunk will be embedded,
    and stored in Firestore for vector search.

    - **text**: The text content to store
    - **source**: Optional source identifier (e.g., filename, URL)
    - **source_type**: Type of source (e.g., 'pdf', 'markdown', 'text')
    - **chunk_size**: Target size for each chunk in tokens (default: 500)
    - **chunk_overlap**: Overlap between chunks in tokens (default: 50)
    - **metadata**: Additional metadata to store with chunks

    Args:
        text (str):
        source (None | str | Unset):
        source_type (None | str | Unset): Type of source (e.g., 'pdf', 'markdown', 'text')
        chunk_size (int | Unset): Target chunk size in tokens Default: 500.
        chunk_overlap (int | Unset): Overlap between chunks in tokens Default: 50.
        project_id (None | str | Unset): Project/Tenant ID (optional, defaults to user's project)
        x_api_key (None | str | Unset):
        x_tenant_id (None | str | Unset): Tenant ID header
        body (IngestBodyType0 | None | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError | list[KnowledgeChunkModel]
    """

    return sync_detailed(
        client=client,
        body=body,
        text=text,
        source=source,
        source_type=source_type,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        project_id=project_id,
        x_api_key=x_api_key,
        x_tenant_id=x_tenant_id,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    body: IngestBodyType0 | None | Unset = UNSET,
    text: str,
    source: None | str | Unset = UNSET,
    source_type: None | str | Unset = UNSET,
    chunk_size: int | Unset = 500,
    chunk_overlap: int | Unset = 50,
    project_id: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
    x_tenant_id: None | str | Unset = UNSET,
) -> Response[Any | HTTPValidationError | list[KnowledgeChunkModel]]:
    """Ingest knowledge (text with automatic chunking)

     Ingest text knowledge with automatic chunking and embedding generation.

    The text will be split into overlapping chunks, each chunk will be embedded,
    and stored in Firestore for vector search.

    - **text**: The text content to store
    - **source**: Optional source identifier (e.g., filename, URL)
    - **source_type**: Type of source (e.g., 'pdf', 'markdown', 'text')
    - **chunk_size**: Target size for each chunk in tokens (default: 500)
    - **chunk_overlap**: Overlap between chunks in tokens (default: 50)
    - **metadata**: Additional metadata to store with chunks

    Args:
        text (str):
        source (None | str | Unset):
        source_type (None | str | Unset): Type of source (e.g., 'pdf', 'markdown', 'text')
        chunk_size (int | Unset): Target chunk size in tokens Default: 500.
        chunk_overlap (int | Unset): Overlap between chunks in tokens Default: 50.
        project_id (None | str | Unset): Project/Tenant ID (optional, defaults to user's project)
        x_api_key (None | str | Unset):
        x_tenant_id (None | str | Unset): Tenant ID header
        body (IngestBodyType0 | None | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError | list[KnowledgeChunkModel]]
    """

    kwargs = _get_kwargs(
        body=body,
        text=text,
        source=source,
        source_type=source_type,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        project_id=project_id,
        x_api_key=x_api_key,
        x_tenant_id=x_tenant_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    body: IngestBodyType0 | None | Unset = UNSET,
    text: str,
    source: None | str | Unset = UNSET,
    source_type: None | str | Unset = UNSET,
    chunk_size: int | Unset = 500,
    chunk_overlap: int | Unset = 50,
    project_id: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
    x_tenant_id: None | str | Unset = UNSET,
) -> Any | HTTPValidationError | list[KnowledgeChunkModel] | None:
    """Ingest knowledge (text with automatic chunking)

     Ingest text knowledge with automatic chunking and embedding generation.

    The text will be split into overlapping chunks, each chunk will be embedded,
    and stored in Firestore for vector search.

    - **text**: The text content to store
    - **source**: Optional source identifier (e.g., filename, URL)
    - **source_type**: Type of source (e.g., 'pdf', 'markdown', 'text')
    - **chunk_size**: Target size for each chunk in tokens (default: 500)
    - **chunk_overlap**: Overlap between chunks in tokens (default: 50)
    - **metadata**: Additional metadata to store with chunks

    Args:
        text (str):
        source (None | str | Unset):
        source_type (None | str | Unset): Type of source (e.g., 'pdf', 'markdown', 'text')
        chunk_size (int | Unset): Target chunk size in tokens Default: 500.
        chunk_overlap (int | Unset): Overlap between chunks in tokens Default: 50.
        project_id (None | str | Unset): Project/Tenant ID (optional, defaults to user's project)
        x_api_key (None | str | Unset):
        x_tenant_id (None | str | Unset): Tenant ID header
        body (IngestBodyType0 | None | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError | list[KnowledgeChunkModel]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            text=text,
            source=source,
            source_type=source_type,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            project_id=project_id,
            x_api_key=x_api_key,
            x_tenant_id=x_tenant_id,
        )
    ).parsed
