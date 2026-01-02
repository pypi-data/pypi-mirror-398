from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.api_limit_exceeded import ApiLimitExceeded
from ...models.missing_parameter import MissingParameter
from ...models.no_registered_key import NoRegisteredKey
from ...models.payment_exception import PaymentException
from ...models.route_optimization_body import RouteOptimizationBody
from ...types import Response


def _get_kwargs(
    *,
    body: RouteOptimizationBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v2/api/route/optimized",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException | None:
    if response.status_code == 400:
        response_400 = MissingParameter.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = NoRegisteredKey.from_dict(response.json())

        return response_401

    if response.status_code == 402:
        response_402 = PaymentException.from_dict(response.json())

        return response_402

    if response.status_code == 429:
        response_429 = ApiLimitExceeded.from_dict(response.json())

        return response_429

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: RouteOptimizationBody,
) -> Response[ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException]:
    """Route Optimization

     This api provides routing details from source to destination points. Additional waypoints can also
    be included in order to get more precise routing experience. Maximum 50 waypoints can be included as
    additional points. Content-Types:application/json should be attached to the request header in order
    to match the correct request format.

    Note: Waypoints will be sorted based on given id in ascending order.

    Args:
        body (RouteOptimizationBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException]
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
    body: RouteOptimizationBody,
) -> ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException | None:
    """Route Optimization

     This api provides routing details from source to destination points. Additional waypoints can also
    be included in order to get more precise routing experience. Maximum 50 waypoints can be included as
    additional points. Content-Types:application/json should be attached to the request header in order
    to match the correct request format.

    Note: Waypoints will be sorted based on given id in ascending order.

    Args:
        body (RouteOptimizationBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: RouteOptimizationBody,
) -> Response[ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException]:
    """Route Optimization

     This api provides routing details from source to destination points. Additional waypoints can also
    be included in order to get more precise routing experience. Maximum 50 waypoints can be included as
    additional points. Content-Types:application/json should be attached to the request header in order
    to match the correct request format.

    Note: Waypoints will be sorted based on given id in ascending order.

    Args:
        body (RouteOptimizationBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: RouteOptimizationBody,
) -> ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException | None:
    """Route Optimization

     This api provides routing details from source to destination points. Additional waypoints can also
    be included in order to get more precise routing experience. Maximum 50 waypoints can be included as
    additional points. Content-Types:application/json should be attached to the request header in order
    to match the correct request format.

    Note: Waypoints will be sorted based on given id in ascending order.

    Args:
        body (RouteOptimizationBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
