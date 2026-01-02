from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_email_registrations_api_v1_email_registrations_get_response_200_item import (
    GetEmailRegistrationsApiV1EmailRegistrationsGetResponse200Item,
)
from ...types import Response


def _get_kwargs() -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/email/registrations",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> list[GetEmailRegistrationsApiV1EmailRegistrationsGetResponse200Item] | None:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = GetEmailRegistrationsApiV1EmailRegistrationsGetResponse200Item.from_dict(
                response_200_item_data
            )

            response_200.append(response_200_item)

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[list[GetEmailRegistrationsApiV1EmailRegistrationsGetResponse200Item]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
) -> Response[list[GetEmailRegistrationsApiV1EmailRegistrationsGetResponse200Item]]:
    """Get Email Registrations

     Get all email registrations from both email_registrations collection and users collection.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list[GetEmailRegistrationsApiV1EmailRegistrationsGetResponse200Item]]
    """

    kwargs = _get_kwargs()

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
) -> list[GetEmailRegistrationsApiV1EmailRegistrationsGetResponse200Item] | None:
    """Get Email Registrations

     Get all email registrations from both email_registrations collection and users collection.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list[GetEmailRegistrationsApiV1EmailRegistrationsGetResponse200Item]
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
) -> Response[list[GetEmailRegistrationsApiV1EmailRegistrationsGetResponse200Item]]:
    """Get Email Registrations

     Get all email registrations from both email_registrations collection and users collection.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list[GetEmailRegistrationsApiV1EmailRegistrationsGetResponse200Item]]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
) -> list[GetEmailRegistrationsApiV1EmailRegistrationsGetResponse200Item] | None:
    """Get Email Registrations

     Get all email registrations from both email_registrations collection and users collection.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list[GetEmailRegistrationsApiV1EmailRegistrationsGetResponse200Item]
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
