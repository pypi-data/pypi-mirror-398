from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.email_response import EmailResponse
from ...models.http_validation_error import HTTPValidationError
from ...models.submit_support_ticket_api_v1_email_support_post_request import (
    SubmitSupportTicketApiV1EmailSupportPostRequest,
)
from ...types import Response


def _get_kwargs(
    *,
    body: SubmitSupportTicketApiV1EmailSupportPostRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/email/support",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> EmailResponse | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = EmailResponse.from_dict(response.json())

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
) -> Response[EmailResponse | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: SubmitSupportTicketApiV1EmailSupportPostRequest,
) -> Response[EmailResponse | HTTPValidationError]:
    r"""Submit Support Ticket

     Submit a support ticket that sends an email to info@buteossystems.com.
    Uses platform email service (does not require project SMTP credentials).

    Request Body:
        {
            \"name\": \"User Name\",
            \"email\": \"user@example.com\",
            \"subject\": \"Support Request Subject\",
            \"message\": \"Support ticket message\"
        }

    Returns:
        EmailResponse with success status

    Args:
        body (SubmitSupportTicketApiV1EmailSupportPostRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[EmailResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: SubmitSupportTicketApiV1EmailSupportPostRequest,
) -> EmailResponse | HTTPValidationError | None:
    r"""Submit Support Ticket

     Submit a support ticket that sends an email to info@buteossystems.com.
    Uses platform email service (does not require project SMTP credentials).

    Request Body:
        {
            \"name\": \"User Name\",
            \"email\": \"user@example.com\",
            \"subject\": \"Support Request Subject\",
            \"message\": \"Support ticket message\"
        }

    Returns:
        EmailResponse with success status

    Args:
        body (SubmitSupportTicketApiV1EmailSupportPostRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        EmailResponse | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: SubmitSupportTicketApiV1EmailSupportPostRequest,
) -> Response[EmailResponse | HTTPValidationError]:
    r"""Submit Support Ticket

     Submit a support ticket that sends an email to info@buteossystems.com.
    Uses platform email service (does not require project SMTP credentials).

    Request Body:
        {
            \"name\": \"User Name\",
            \"email\": \"user@example.com\",
            \"subject\": \"Support Request Subject\",
            \"message\": \"Support ticket message\"
        }

    Returns:
        EmailResponse with success status

    Args:
        body (SubmitSupportTicketApiV1EmailSupportPostRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[EmailResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: SubmitSupportTicketApiV1EmailSupportPostRequest,
) -> EmailResponse | HTTPValidationError | None:
    r"""Submit Support Ticket

     Submit a support ticket that sends an email to info@buteossystems.com.
    Uses platform email service (does not require project SMTP credentials).

    Request Body:
        {
            \"name\": \"User Name\",
            \"email\": \"user@example.com\",
            \"subject\": \"Support Request Subject\",
            \"message\": \"Support ticket message\"
        }

    Returns:
        EmailResponse with success status

    Args:
        body (SubmitSupportTicketApiV1EmailSupportPostRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        EmailResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
