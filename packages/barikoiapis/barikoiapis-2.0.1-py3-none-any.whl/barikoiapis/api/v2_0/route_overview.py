from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.api_limit_exceeded import ApiLimitExceeded
from ...models.missing_parameter import MissingParameter
from ...models.no_registered_key import NoRegisteredKey
from ...models.payment_exception import PaymentException
from ...models.route_overview_geometries import RouteOverviewGeometries
from ...models.route_overview_profile import RouteOverviewProfile
from ...types import UNSET, Response, Unset


def _get_kwargs(
    coordinates: str,
    *,
    api_key: str,
    geometries: RouteOverviewGeometries | Unset = RouteOverviewGeometries.POLYLINE,
    profile: RouteOverviewProfile | Unset = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["api_key"] = api_key

    json_geometries: str | Unset = UNSET
    if not isinstance(geometries, Unset):
        json_geometries = geometries.value

    params["geometries"] = json_geometries

    json_profile: str | Unset = UNSET
    if not isinstance(profile, Unset):
        json_profile = profile.value

    params["profile"] = json_profile

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v2/api/route/{coordinates}".format(
            coordinates=quote(str(coordinates), safe=""),
        ),
        "params": params,
    }

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
    coordinates: str,
    *,
    client: AuthenticatedClient | Client,
    api_key: str,
    geometries: RouteOverviewGeometries | Unset = RouteOverviewGeometries.POLYLINE,
    profile: RouteOverviewProfile | Unset = UNSET,
) -> Response[ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException]:
    """Route Overview

     This API endpoint retrieves route information between two geographical points specified by their
    longitude and latitude coordinates. The response includes details such as the geometry of the route,
    distance, duration, and waypoints.

    Args:
        coordinates (str):
        api_key (str):
        geometries (RouteOverviewGeometries | Unset):  Default: RouteOverviewGeometries.POLYLINE.
        profile (RouteOverviewProfile | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException]
    """

    kwargs = _get_kwargs(
        coordinates=coordinates,
        api_key=api_key,
        geometries=geometries,
        profile=profile,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    coordinates: str,
    *,
    client: AuthenticatedClient | Client,
    api_key: str,
    geometries: RouteOverviewGeometries | Unset = RouteOverviewGeometries.POLYLINE,
    profile: RouteOverviewProfile | Unset = UNSET,
) -> ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException | None:
    """Route Overview

     This API endpoint retrieves route information between two geographical points specified by their
    longitude and latitude coordinates. The response includes details such as the geometry of the route,
    distance, duration, and waypoints.

    Args:
        coordinates (str):
        api_key (str):
        geometries (RouteOverviewGeometries | Unset):  Default: RouteOverviewGeometries.POLYLINE.
        profile (RouteOverviewProfile | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException
    """

    return sync_detailed(
        coordinates=coordinates,
        client=client,
        api_key=api_key,
        geometries=geometries,
        profile=profile,
    ).parsed


async def asyncio_detailed(
    coordinates: str,
    *,
    client: AuthenticatedClient | Client,
    api_key: str,
    geometries: RouteOverviewGeometries | Unset = RouteOverviewGeometries.POLYLINE,
    profile: RouteOverviewProfile | Unset = UNSET,
) -> Response[ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException]:
    """Route Overview

     This API endpoint retrieves route information between two geographical points specified by their
    longitude and latitude coordinates. The response includes details such as the geometry of the route,
    distance, duration, and waypoints.

    Args:
        coordinates (str):
        api_key (str):
        geometries (RouteOverviewGeometries | Unset):  Default: RouteOverviewGeometries.POLYLINE.
        profile (RouteOverviewProfile | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException]
    """

    kwargs = _get_kwargs(
        coordinates=coordinates,
        api_key=api_key,
        geometries=geometries,
        profile=profile,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    coordinates: str,
    *,
    client: AuthenticatedClient | Client,
    api_key: str,
    geometries: RouteOverviewGeometries | Unset = RouteOverviewGeometries.POLYLINE,
    profile: RouteOverviewProfile | Unset = UNSET,
) -> ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException | None:
    """Route Overview

     This API endpoint retrieves route information between two geographical points specified by their
    longitude and latitude coordinates. The response includes details such as the geometry of the route,
    distance, duration, and waypoints.

    Args:
        coordinates (str):
        api_key (str):
        geometries (RouteOverviewGeometries | Unset):  Default: RouteOverviewGeometries.POLYLINE.
        profile (RouteOverviewProfile | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException
    """

    return (
        await asyncio_detailed(
            coordinates=coordinates,
            client=client,
            api_key=api_key,
            geometries=geometries,
            profile=profile,
        )
    ).parsed
