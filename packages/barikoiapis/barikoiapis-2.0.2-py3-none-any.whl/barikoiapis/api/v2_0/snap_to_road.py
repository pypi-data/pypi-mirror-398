from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.api_limit_exceeded import ApiLimitExceeded
from ...models.missing_parameter import MissingParameter
from ...models.no_registered_key import NoRegisteredKey
from ...models.payment_exception import PaymentException
from ...models.snap_to_road_success import SnapToRoadSuccess
from ...types import UNSET, Response


def _get_kwargs(
    *,
    api_key: str,
    point: str,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["api_key"] = api_key

    params["point"] = point

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v2/api/routing/nearest",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException | SnapToRoadSuccess | None:
    if response.status_code == 200:
        response_200 = SnapToRoadSuccess.from_dict(response.json())

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
) -> Response[ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException | SnapToRoadSuccess]:
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
    point: str,
) -> Response[ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException | SnapToRoadSuccess]:
    """Snap to Road

     Snap to Road API endpoint retrieves the nearest point on the road network to a specified
    geographical point (latitude and longitude). It returns the coordinates of the nearest point and the
    distance from the specified point to this nearest point. Snap to Road API is useful for finding the
    closest road location to a given geographic point, which can be used in various applications such as
    route planning, geofencing, and location-based services.

    Args:
        api_key (str):
        point (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException | SnapToRoadSuccess]
    """

    kwargs = _get_kwargs(
        api_key=api_key,
        point=point,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    api_key: str,
    point: str,
) -> ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException | SnapToRoadSuccess | None:
    """Snap to Road

     Snap to Road API endpoint retrieves the nearest point on the road network to a specified
    geographical point (latitude and longitude). It returns the coordinates of the nearest point and the
    distance from the specified point to this nearest point. Snap to Road API is useful for finding the
    closest road location to a given geographic point, which can be used in various applications such as
    route planning, geofencing, and location-based services.

    Args:
        api_key (str):
        point (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException | SnapToRoadSuccess
    """

    return sync_detailed(
        client=client,
        api_key=api_key,
        point=point,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    api_key: str,
    point: str,
) -> Response[ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException | SnapToRoadSuccess]:
    """Snap to Road

     Snap to Road API endpoint retrieves the nearest point on the road network to a specified
    geographical point (latitude and longitude). It returns the coordinates of the nearest point and the
    distance from the specified point to this nearest point. Snap to Road API is useful for finding the
    closest road location to a given geographic point, which can be used in various applications such as
    route planning, geofencing, and location-based services.

    Args:
        api_key (str):
        point (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException | SnapToRoadSuccess]
    """

    kwargs = _get_kwargs(
        api_key=api_key,
        point=point,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    api_key: str,
    point: str,
) -> ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException | SnapToRoadSuccess | None:
    """Snap to Road

     Snap to Road API endpoint retrieves the nearest point on the road network to a specified
    geographical point (latitude and longitude). It returns the coordinates of the nearest point and the
    distance from the specified point to this nearest point. Snap to Road API is useful for finding the
    closest road location to a given geographic point, which can be used in various applications such as
    route planning, geofencing, and location-based services.

    Args:
        api_key (str):
        point (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException | SnapToRoadSuccess
    """

    return (
        await asyncio_detailed(
            client=client,
            api_key=api_key,
            point=point,
        )
    ).parsed
