from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    payment_method_id: str,
    *,
    x_api_key: None | str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_api_key, Unset):
        headers["X-API-Key"] = x_api_key

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/api/v1/backend/payment-methods/{payment_method_id}".format(
            payment_method_id=quote(str(payment_method_id), safe=""),
        ),
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = response.json()
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
) -> Response[Any | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    payment_method_id: str,
    *,
    client: AuthenticatedClient,
    x_api_key: None | str | Unset = UNSET,
) -> Response[Any | HTTPValidationError]:
    """Delete Payment Method

     Delete a payment method.

    Args:
        payment_method_id (str):
        x_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        payment_method_id=payment_method_id,
        x_api_key=x_api_key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    payment_method_id: str,
    *,
    client: AuthenticatedClient,
    x_api_key: None | str | Unset = UNSET,
) -> Any | HTTPValidationError | None:
    """Delete Payment Method

     Delete a payment method.

    Args:
        payment_method_id (str):
        x_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError
    """

    return sync_detailed(
        payment_method_id=payment_method_id,
        client=client,
        x_api_key=x_api_key,
    ).parsed


async def asyncio_detailed(
    payment_method_id: str,
    *,
    client: AuthenticatedClient,
    x_api_key: None | str | Unset = UNSET,
) -> Response[Any | HTTPValidationError]:
    """Delete Payment Method

     Delete a payment method.

    Args:
        payment_method_id (str):
        x_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        payment_method_id=payment_method_id,
        x_api_key=x_api_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    payment_method_id: str,
    *,
    client: AuthenticatedClient,
    x_api_key: None | str | Unset = UNSET,
) -> Any | HTTPValidationError | None:
    """Delete Payment Method

     Delete a payment method.

    Args:
        payment_method_id (str):
        x_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            payment_method_id=payment_method_id,
            client=client,
            x_api_key=x_api_key,
        )
    ).parsed
