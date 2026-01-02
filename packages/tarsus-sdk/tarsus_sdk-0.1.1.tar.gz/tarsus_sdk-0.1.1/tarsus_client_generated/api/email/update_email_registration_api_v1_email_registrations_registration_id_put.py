from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.update_email_registration_api_v1_email_registrations_registration_id_put_response_update_email_registration_api_v1_email_registrations_registration_id_put import (
    UpdateEmailRegistrationApiV1EmailRegistrationsRegistrationIdPutResponseUpdateEmailRegistrationApiV1EmailRegistrationsRegistrationIdPut,
)
from ...models.update_email_registration_api_v1_email_registrations_registration_id_put_updates import (
    UpdateEmailRegistrationApiV1EmailRegistrationsRegistrationIdPutUpdates,
)
from ...types import Response


def _get_kwargs(
    registration_id: str,
    *,
    body: UpdateEmailRegistrationApiV1EmailRegistrationsRegistrationIdPutUpdates,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": "/api/v1/email/registrations/{registration_id}".format(
            registration_id=quote(str(registration_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    HTTPValidationError
    | UpdateEmailRegistrationApiV1EmailRegistrationsRegistrationIdPutResponseUpdateEmailRegistrationApiV1EmailRegistrationsRegistrationIdPut
    | None
):
    if response.status_code == 200:
        response_200 = UpdateEmailRegistrationApiV1EmailRegistrationsRegistrationIdPutResponseUpdateEmailRegistrationApiV1EmailRegistrationsRegistrationIdPut.from_dict(
            response.json()
        )

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
) -> Response[
    HTTPValidationError
    | UpdateEmailRegistrationApiV1EmailRegistrationsRegistrationIdPutResponseUpdateEmailRegistrationApiV1EmailRegistrationsRegistrationIdPut
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    registration_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateEmailRegistrationApiV1EmailRegistrationsRegistrationIdPutUpdates,
) -> Response[
    HTTPValidationError
    | UpdateEmailRegistrationApiV1EmailRegistrationsRegistrationIdPutResponseUpdateEmailRegistrationApiV1EmailRegistrationsRegistrationIdPut
]:
    """Update Email Registration

     Update an email registration (e.g., toggle is_active, update source).

    Args:
        registration_id (str):
        body (UpdateEmailRegistrationApiV1EmailRegistrationsRegistrationIdPutUpdates):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | UpdateEmailRegistrationApiV1EmailRegistrationsRegistrationIdPutResponseUpdateEmailRegistrationApiV1EmailRegistrationsRegistrationIdPut]
    """

    kwargs = _get_kwargs(
        registration_id=registration_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    registration_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateEmailRegistrationApiV1EmailRegistrationsRegistrationIdPutUpdates,
) -> (
    HTTPValidationError
    | UpdateEmailRegistrationApiV1EmailRegistrationsRegistrationIdPutResponseUpdateEmailRegistrationApiV1EmailRegistrationsRegistrationIdPut
    | None
):
    """Update Email Registration

     Update an email registration (e.g., toggle is_active, update source).

    Args:
        registration_id (str):
        body (UpdateEmailRegistrationApiV1EmailRegistrationsRegistrationIdPutUpdates):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | UpdateEmailRegistrationApiV1EmailRegistrationsRegistrationIdPutResponseUpdateEmailRegistrationApiV1EmailRegistrationsRegistrationIdPut
    """

    return sync_detailed(
        registration_id=registration_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    registration_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateEmailRegistrationApiV1EmailRegistrationsRegistrationIdPutUpdates,
) -> Response[
    HTTPValidationError
    | UpdateEmailRegistrationApiV1EmailRegistrationsRegistrationIdPutResponseUpdateEmailRegistrationApiV1EmailRegistrationsRegistrationIdPut
]:
    """Update Email Registration

     Update an email registration (e.g., toggle is_active, update source).

    Args:
        registration_id (str):
        body (UpdateEmailRegistrationApiV1EmailRegistrationsRegistrationIdPutUpdates):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | UpdateEmailRegistrationApiV1EmailRegistrationsRegistrationIdPutResponseUpdateEmailRegistrationApiV1EmailRegistrationsRegistrationIdPut]
    """

    kwargs = _get_kwargs(
        registration_id=registration_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    registration_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateEmailRegistrationApiV1EmailRegistrationsRegistrationIdPutUpdates,
) -> (
    HTTPValidationError
    | UpdateEmailRegistrationApiV1EmailRegistrationsRegistrationIdPutResponseUpdateEmailRegistrationApiV1EmailRegistrationsRegistrationIdPut
    | None
):
    """Update Email Registration

     Update an email registration (e.g., toggle is_active, update source).

    Args:
        registration_id (str):
        body (UpdateEmailRegistrationApiV1EmailRegistrationsRegistrationIdPutUpdates):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | UpdateEmailRegistrationApiV1EmailRegistrationsRegistrationIdPutResponseUpdateEmailRegistrationApiV1EmailRegistrationsRegistrationIdPut
    """

    return (
        await asyncio_detailed(
            registration_id=registration_id,
            client=client,
            body=body,
        )
    ).parsed
