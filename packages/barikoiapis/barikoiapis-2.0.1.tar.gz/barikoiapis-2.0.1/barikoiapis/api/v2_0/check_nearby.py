from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.api_limit_exceeded import ApiLimitExceeded
from ...models.check_nearby_success import CheckNearbySuccess
from ...models.missing_parameter import MissingParameter
from ...models.no_registered_key import NoRegisteredKey
from ...models.payment_exception import PaymentException
from ...types import UNSET, Response


def _get_kwargs(
    *,
    api_key: str,
    destination_latitude: float,
    destination_longitude: float,
    radius: int,
    current_latitude: float,
    current_longitude: float,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["api_key"] = api_key

    params["destination_latitude"] = destination_latitude

    params["destination_longitude"] = destination_longitude

    params["radius"] = radius

    params["current_latitude"] = current_latitude

    params["current_longitude"] = current_longitude

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v2/api/check/nearby",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ApiLimitExceeded | CheckNearbySuccess | MissingParameter | NoRegisteredKey | PaymentException | None:
    if response.status_code == 200:
        response_200 = CheckNearbySuccess.from_dict(response.json())

        return response_200

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
) -> Response[ApiLimitExceeded | CheckNearbySuccess | MissingParameter | NoRegisteredKey | PaymentException]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    api_key: str,
    destination_latitude: float,
    destination_longitude: float,
    radius: int,
    current_latitude: float,
    current_longitude: float,
) -> Response[ApiLimitExceeded | CheckNearbySuccess | MissingParameter | NoRegisteredKey | PaymentException]:
    """Check Nearby

    Args:
        api_key (str):
        destination_latitude (float):
        destination_longitude (float):
        radius (int):
        current_latitude (float):
        current_longitude (float):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiLimitExceeded | CheckNearbySuccess | MissingParameter | NoRegisteredKey | PaymentException]
    """

    kwargs = _get_kwargs(
        api_key=api_key,
        destination_latitude=destination_latitude,
        destination_longitude=destination_longitude,
        radius=radius,
        current_latitude=current_latitude,
        current_longitude=current_longitude,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    api_key: str,
    destination_latitude: float,
    destination_longitude: float,
    radius: int,
    current_latitude: float,
    current_longitude: float,
) -> ApiLimitExceeded | CheckNearbySuccess | MissingParameter | NoRegisteredKey | PaymentException | None:
    """Check Nearby

    Args:
        api_key (str):
        destination_latitude (float):
        destination_longitude (float):
        radius (int):
        current_latitude (float):
        current_longitude (float):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiLimitExceeded | CheckNearbySuccess | MissingParameter | NoRegisteredKey | PaymentException
    """

    return sync_detailed(
        client=client,
        api_key=api_key,
        destination_latitude=destination_latitude,
        destination_longitude=destination_longitude,
        radius=radius,
        current_latitude=current_latitude,
        current_longitude=current_longitude,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    api_key: str,
    destination_latitude: float,
    destination_longitude: float,
    radius: int,
    current_latitude: float,
    current_longitude: float,
) -> Response[ApiLimitExceeded | CheckNearbySuccess | MissingParameter | NoRegisteredKey | PaymentException]:
    """Check Nearby

    Args:
        api_key (str):
        destination_latitude (float):
        destination_longitude (float):
        radius (int):
        current_latitude (float):
        current_longitude (float):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiLimitExceeded | CheckNearbySuccess | MissingParameter | NoRegisteredKey | PaymentException]
    """

    kwargs = _get_kwargs(
        api_key=api_key,
        destination_latitude=destination_latitude,
        destination_longitude=destination_longitude,
        radius=radius,
        current_latitude=current_latitude,
        current_longitude=current_longitude,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    api_key: str,
    destination_latitude: float,
    destination_longitude: float,
    radius: int,
    current_latitude: float,
    current_longitude: float,
) -> ApiLimitExceeded | CheckNearbySuccess | MissingParameter | NoRegisteredKey | PaymentException | None:
    """Check Nearby

    Args:
        api_key (str):
        destination_latitude (float):
        destination_longitude (float):
        radius (int):
        current_latitude (float):
        current_longitude (float):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiLimitExceeded | CheckNearbySuccess | MissingParameter | NoRegisteredKey | PaymentException
    """

    return (
        await asyncio_detailed(
            client=client,
            api_key=api_key,
            destination_latitude=destination_latitude,
            destination_longitude=destination_longitude,
            radius=radius,
            current_latitude=current_latitude,
            current_longitude=current_longitude,
        )
    ).parsed
