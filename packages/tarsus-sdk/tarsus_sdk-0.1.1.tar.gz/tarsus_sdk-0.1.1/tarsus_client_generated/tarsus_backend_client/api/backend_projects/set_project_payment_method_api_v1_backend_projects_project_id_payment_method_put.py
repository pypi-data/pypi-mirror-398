from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.project_public import ProjectPublic
from ...models.set_project_payment_method_api_v1_backend_projects_project_id_payment_method_put_payment_method_data import (
    SetProjectPaymentMethodApiV1BackendProjectsProjectIdPaymentMethodPutPaymentMethodData,
)
from ...types import Response


def _get_kwargs(
    project_id: str,
    *,
    body: SetProjectPaymentMethodApiV1BackendProjectsProjectIdPaymentMethodPutPaymentMethodData,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": "/api/v1/backend/projects/{project_id}/payment-method".format(
            project_id=quote(str(project_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | ProjectPublic | None:
    if response.status_code == 200:
        response_200 = ProjectPublic.from_dict(response.json())

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
) -> Response[HTTPValidationError | ProjectPublic]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    project_id: str,
    *,
    client: AuthenticatedClient,
    body: SetProjectPaymentMethodApiV1BackendProjectsProjectIdPaymentMethodPutPaymentMethodData,
) -> Response[HTTPValidationError | ProjectPublic]:
    """Set Project Payment Method

     Set or update payment method for a project.
    Payment method can be project-specific or None (to use tenant default).

    Args:
        project_id (str):
        body
            (SetProjectPaymentMethodApiV1BackendProjectsProjectIdPaymentMethodPutPaymentMethodData):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ProjectPublic]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    project_id: str,
    *,
    client: AuthenticatedClient,
    body: SetProjectPaymentMethodApiV1BackendProjectsProjectIdPaymentMethodPutPaymentMethodData,
) -> HTTPValidationError | ProjectPublic | None:
    """Set Project Payment Method

     Set or update payment method for a project.
    Payment method can be project-specific or None (to use tenant default).

    Args:
        project_id (str):
        body
            (SetProjectPaymentMethodApiV1BackendProjectsProjectIdPaymentMethodPutPaymentMethodData):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ProjectPublic
    """

    return sync_detailed(
        project_id=project_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    project_id: str,
    *,
    client: AuthenticatedClient,
    body: SetProjectPaymentMethodApiV1BackendProjectsProjectIdPaymentMethodPutPaymentMethodData,
) -> Response[HTTPValidationError | ProjectPublic]:
    """Set Project Payment Method

     Set or update payment method for a project.
    Payment method can be project-specific or None (to use tenant default).

    Args:
        project_id (str):
        body
            (SetProjectPaymentMethodApiV1BackendProjectsProjectIdPaymentMethodPutPaymentMethodData):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ProjectPublic]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    project_id: str,
    *,
    client: AuthenticatedClient,
    body: SetProjectPaymentMethodApiV1BackendProjectsProjectIdPaymentMethodPutPaymentMethodData,
) -> HTTPValidationError | ProjectPublic | None:
    """Set Project Payment Method

     Set or update payment method for a project.
    Payment method can be project-specific or None (to use tenant default).

    Args:
        project_id (str):
        body
            (SetProjectPaymentMethodApiV1BackendProjectsProjectIdPaymentMethodPutPaymentMethodData):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ProjectPublic
    """

    return (
        await asyncio_detailed(
            project_id=project_id,
            client=client,
            body=body,
        )
    ).parsed
