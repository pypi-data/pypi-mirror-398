from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.api_limit_exceeded import ApiLimitExceeded
from ...models.missing_parameter import MissingParameter
from ...models.no_registered_key import NoRegisteredKey
from ...models.payment_exception import PaymentException
from ...models.reverse_geocode_success import ReverseGeocodeSuccess
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    api_key: str,
    longitude: float,
    latitude: float,
    country_code: str | Unset = UNSET,
    country: bool | Unset = UNSET,
    district: bool | Unset = UNSET,
    post_code: bool | Unset = UNSET,
    sub_district: bool | Unset = UNSET,
    union: bool | Unset = UNSET,
    pauroshova: bool | Unset = UNSET,
    location_type: bool | Unset = UNSET,
    division: bool | Unset = UNSET,
    address: bool | Unset = UNSET,
    area: bool | Unset = UNSET,
    bangla: bool | Unset = UNSET,
    thana: bool | Unset = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["api_key"] = api_key

    params["longitude"] = longitude

    params["latitude"] = latitude

    params["country_code"] = country_code

    params["country"] = country

    params["district"] = district

    params["post_code"] = post_code

    params["sub_district"] = sub_district

    params["union"] = union

    params["pauroshova"] = pauroshova

    params["location_type"] = location_type

    params["division"] = division

    params["address"] = address

    params["area"] = area

    params["bangla"] = bangla

    params["thana"] = thana

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v2/api/search/reverse/geocode",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException | ReverseGeocodeSuccess | None:
    if response.status_code == 200:
        response_200 = ReverseGeocodeSuccess.from_dict(response.json())

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
) -> Response[ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException | ReverseGeocodeSuccess]:
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
    longitude: float,
    latitude: float,
    country_code: str | Unset = UNSET,
    country: bool | Unset = UNSET,
    district: bool | Unset = UNSET,
    post_code: bool | Unset = UNSET,
    sub_district: bool | Unset = UNSET,
    union: bool | Unset = UNSET,
    pauroshova: bool | Unset = UNSET,
    location_type: bool | Unset = UNSET,
    division: bool | Unset = UNSET,
    address: bool | Unset = UNSET,
    area: bool | Unset = UNSET,
    bangla: bool | Unset = UNSET,
    thana: bool | Unset = UNSET,
) -> Response[ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException | ReverseGeocodeSuccess]:
    """Reverse Geocoding

     This API endpoint performs reverse geocoding to convert geographical coordinates (longitude and
    latitude) into a human-readable address. It provides detailed location information including the
    address in both English and Bangla, along with other administrative details such as district,
    division, and more.

    **IMPORTANT:** ⚠️ Enabling **all** optional parameters will trigger multiple internal API calls,
    which will consume more of your API credits. To optimize performance and reduce credit usage, only
    request the parameters that are essential for your use case.

    Args:
        api_key (str):
        longitude (float):
        latitude (float):
        country_code (str | Unset):
        country (bool | Unset):
        district (bool | Unset):
        post_code (bool | Unset):
        sub_district (bool | Unset):
        union (bool | Unset):
        pauroshova (bool | Unset):
        location_type (bool | Unset):
        division (bool | Unset):
        address (bool | Unset):
        area (bool | Unset):
        bangla (bool | Unset):
        thana (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException | ReverseGeocodeSuccess]
    """

    kwargs = _get_kwargs(
        api_key=api_key,
        longitude=longitude,
        latitude=latitude,
        country_code=country_code,
        country=country,
        district=district,
        post_code=post_code,
        sub_district=sub_district,
        union=union,
        pauroshova=pauroshova,
        location_type=location_type,
        division=division,
        address=address,
        area=area,
        bangla=bangla,
        thana=thana,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    api_key: str,
    longitude: float,
    latitude: float,
    country_code: str | Unset = UNSET,
    country: bool | Unset = UNSET,
    district: bool | Unset = UNSET,
    post_code: bool | Unset = UNSET,
    sub_district: bool | Unset = UNSET,
    union: bool | Unset = UNSET,
    pauroshova: bool | Unset = UNSET,
    location_type: bool | Unset = UNSET,
    division: bool | Unset = UNSET,
    address: bool | Unset = UNSET,
    area: bool | Unset = UNSET,
    bangla: bool | Unset = UNSET,
    thana: bool | Unset = UNSET,
) -> ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException | ReverseGeocodeSuccess | None:
    """Reverse Geocoding

     This API endpoint performs reverse geocoding to convert geographical coordinates (longitude and
    latitude) into a human-readable address. It provides detailed location information including the
    address in both English and Bangla, along with other administrative details such as district,
    division, and more.

    **IMPORTANT:** ⚠️ Enabling **all** optional parameters will trigger multiple internal API calls,
    which will consume more of your API credits. To optimize performance and reduce credit usage, only
    request the parameters that are essential for your use case.

    Args:
        api_key (str):
        longitude (float):
        latitude (float):
        country_code (str | Unset):
        country (bool | Unset):
        district (bool | Unset):
        post_code (bool | Unset):
        sub_district (bool | Unset):
        union (bool | Unset):
        pauroshova (bool | Unset):
        location_type (bool | Unset):
        division (bool | Unset):
        address (bool | Unset):
        area (bool | Unset):
        bangla (bool | Unset):
        thana (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException | ReverseGeocodeSuccess
    """

    return sync_detailed(
        client=client,
        api_key=api_key,
        longitude=longitude,
        latitude=latitude,
        country_code=country_code,
        country=country,
        district=district,
        post_code=post_code,
        sub_district=sub_district,
        union=union,
        pauroshova=pauroshova,
        location_type=location_type,
        division=division,
        address=address,
        area=area,
        bangla=bangla,
        thana=thana,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    api_key: str,
    longitude: float,
    latitude: float,
    country_code: str | Unset = UNSET,
    country: bool | Unset = UNSET,
    district: bool | Unset = UNSET,
    post_code: bool | Unset = UNSET,
    sub_district: bool | Unset = UNSET,
    union: bool | Unset = UNSET,
    pauroshova: bool | Unset = UNSET,
    location_type: bool | Unset = UNSET,
    division: bool | Unset = UNSET,
    address: bool | Unset = UNSET,
    area: bool | Unset = UNSET,
    bangla: bool | Unset = UNSET,
    thana: bool | Unset = UNSET,
) -> Response[ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException | ReverseGeocodeSuccess]:
    """Reverse Geocoding

     This API endpoint performs reverse geocoding to convert geographical coordinates (longitude and
    latitude) into a human-readable address. It provides detailed location information including the
    address in both English and Bangla, along with other administrative details such as district,
    division, and more.

    **IMPORTANT:** ⚠️ Enabling **all** optional parameters will trigger multiple internal API calls,
    which will consume more of your API credits. To optimize performance and reduce credit usage, only
    request the parameters that are essential for your use case.

    Args:
        api_key (str):
        longitude (float):
        latitude (float):
        country_code (str | Unset):
        country (bool | Unset):
        district (bool | Unset):
        post_code (bool | Unset):
        sub_district (bool | Unset):
        union (bool | Unset):
        pauroshova (bool | Unset):
        location_type (bool | Unset):
        division (bool | Unset):
        address (bool | Unset):
        area (bool | Unset):
        bangla (bool | Unset):
        thana (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException | ReverseGeocodeSuccess]
    """

    kwargs = _get_kwargs(
        api_key=api_key,
        longitude=longitude,
        latitude=latitude,
        country_code=country_code,
        country=country,
        district=district,
        post_code=post_code,
        sub_district=sub_district,
        union=union,
        pauroshova=pauroshova,
        location_type=location_type,
        division=division,
        address=address,
        area=area,
        bangla=bangla,
        thana=thana,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    api_key: str,
    longitude: float,
    latitude: float,
    country_code: str | Unset = UNSET,
    country: bool | Unset = UNSET,
    district: bool | Unset = UNSET,
    post_code: bool | Unset = UNSET,
    sub_district: bool | Unset = UNSET,
    union: bool | Unset = UNSET,
    pauroshova: bool | Unset = UNSET,
    location_type: bool | Unset = UNSET,
    division: bool | Unset = UNSET,
    address: bool | Unset = UNSET,
    area: bool | Unset = UNSET,
    bangla: bool | Unset = UNSET,
    thana: bool | Unset = UNSET,
) -> ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException | ReverseGeocodeSuccess | None:
    """Reverse Geocoding

     This API endpoint performs reverse geocoding to convert geographical coordinates (longitude and
    latitude) into a human-readable address. It provides detailed location information including the
    address in both English and Bangla, along with other administrative details such as district,
    division, and more.

    **IMPORTANT:** ⚠️ Enabling **all** optional parameters will trigger multiple internal API calls,
    which will consume more of your API credits. To optimize performance and reduce credit usage, only
    request the parameters that are essential for your use case.

    Args:
        api_key (str):
        longitude (float):
        latitude (float):
        country_code (str | Unset):
        country (bool | Unset):
        district (bool | Unset):
        post_code (bool | Unset):
        sub_district (bool | Unset):
        union (bool | Unset):
        pauroshova (bool | Unset):
        location_type (bool | Unset):
        division (bool | Unset):
        address (bool | Unset):
        area (bool | Unset):
        bangla (bool | Unset):
        thana (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException | ReverseGeocodeSuccess
    """

    return (
        await asyncio_detailed(
            client=client,
            api_key=api_key,
            longitude=longitude,
            latitude=latitude,
            country_code=country_code,
            country=country,
            district=district,
            post_code=post_code,
            sub_district=sub_district,
            union=union,
            pauroshova=pauroshova,
            location_type=location_type,
            division=division,
            address=address,
            area=area,
            bangla=bangla,
            thana=thana,
        )
    ).parsed
