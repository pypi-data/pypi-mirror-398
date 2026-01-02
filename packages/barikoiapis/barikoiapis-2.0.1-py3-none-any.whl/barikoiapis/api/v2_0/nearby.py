from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.api_limit_exceeded import ApiLimitExceeded
from ...models.missing_parameter import MissingParameter
from ...models.nearby_success import NearbySuccess
from ...models.no_registered_key import NoRegisteredKey
from ...models.payment_exception import PaymentException
from ...types import UNSET, Response


def _get_kwargs(
    radius: float,
    limit: int,
    *,
    api_key: str,
    longitude: float,
    latitude: float,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["api_key"] = api_key

    params["longitude"] = longitude

    params["latitude"] = latitude

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v2/api/search/nearby/{radius}/{limit}".format(
            radius=quote(str(radius), safe=""),
            limit=quote(str(limit), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ApiLimitExceeded | MissingParameter | NearbySuccess | NoRegisteredKey | PaymentException | None:
    if response.status_code == 200:
        response_200 = NearbySuccess.from_dict(response.json())

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
) -> Response[ApiLimitExceeded | MissingParameter | NearbySuccess | NoRegisteredKey | PaymentException]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    radius: float,
    limit: int,
    *,
    client: AuthenticatedClient | Client,
    api_key: str,
    longitude: float,
    latitude: float,
) -> Response[ApiLimitExceeded | MissingParameter | NearbySuccess | NoRegisteredKey | PaymentException]:
    """Nearby Places

    Args:
        radius (float):
        limit (int):
        api_key (str):
        longitude (float):
        latitude (float):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiLimitExceeded | MissingParameter | NearbySuccess | NoRegisteredKey | PaymentException]
    """

    kwargs = _get_kwargs(
        radius=radius,
        limit=limit,
        api_key=api_key,
        longitude=longitude,
        latitude=latitude,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    radius: float,
    limit: int,
    *,
    client: AuthenticatedClient | Client,
    api_key: str,
    longitude: float,
    latitude: float,
) -> ApiLimitExceeded | MissingParameter | NearbySuccess | NoRegisteredKey | PaymentException | None:
    """Nearby Places

    Args:
        radius (float):
        limit (int):
        api_key (str):
        longitude (float):
        latitude (float):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiLimitExceeded | MissingParameter | NearbySuccess | NoRegisteredKey | PaymentException
    """

    return sync_detailed(
        radius=radius,
        limit=limit,
        client=client,
        api_key=api_key,
        longitude=longitude,
        latitude=latitude,
    ).parsed


async def asyncio_detailed(
    radius: float,
    limit: int,
    *,
    client: AuthenticatedClient | Client,
    api_key: str,
    longitude: float,
    latitude: float,
) -> Response[ApiLimitExceeded | MissingParameter | NearbySuccess | NoRegisteredKey | PaymentException]:
    """Nearby Places

    Args:
        radius (float):
        limit (int):
        api_key (str):
        longitude (float):
        latitude (float):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiLimitExceeded | MissingParameter | NearbySuccess | NoRegisteredKey | PaymentException]
    """

    kwargs = _get_kwargs(
        radius=radius,
        limit=limit,
        api_key=api_key,
        longitude=longitude,
        latitude=latitude,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    radius: float,
    limit: int,
    *,
    client: AuthenticatedClient | Client,
    api_key: str,
    longitude: float,
    latitude: float,
) -> ApiLimitExceeded | MissingParameter | NearbySuccess | NoRegisteredKey | PaymentException | None:
    """Nearby Places

    Args:
        radius (float):
        limit (int):
        api_key (str):
        longitude (float):
        latitude (float):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiLimitExceeded | MissingParameter | NearbySuccess | NoRegisteredKey | PaymentException
    """

    return (
        await asyncio_detailed(
            radius=radius,
            limit=limit,
            client=client,
            api_key=api_key,
            longitude=longitude,
            latitude=latitude,
        )
    ).parsed
