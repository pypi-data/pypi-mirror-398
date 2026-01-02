from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.api_limit_exceeded import ApiLimitExceeded
from ...models.calculate_route_body import CalculateRouteBody
from ...models.calculate_route_profile import CalculateRouteProfile
from ...models.calculate_route_type import CalculateRouteType
from ...models.missing_parameter import MissingParameter
from ...models.no_registered_key import NoRegisteredKey
from ...models.payment_exception import PaymentException
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: CalculateRouteBody,
    api_key: str,
    type_: CalculateRouteType,
    profile: CalculateRouteProfile | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    params: dict[str, Any] = {}

    params["api_key"] = api_key

    json_type_ = type_.value
    params["type"] = json_type_

    json_profile: str | Unset = UNSET
    if not isinstance(profile, Unset):
        json_profile = profile.value

    params["profile"] = json_profile

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v2/api/routing",
        "params": params,
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
    body: CalculateRouteBody,
    api_key: str,
    type_: CalculateRouteType,
    profile: CalculateRouteProfile | Unset = UNSET,
) -> Response[ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException]:
    """Calculate Route

     This API response is intended for use in applications requiring detailed route information and
    navigation instructions. Such applications might include: GPS navigation systems, Mapping services,
    Route optimization tools for logistics and delivery, Travel planning apps.These can guide users from
    their starting point to their destination, providing clear, step-by-step directions, estimated
    travel times, and costs associated with the journey.

    Args:
        api_key (str):
        type_ (CalculateRouteType):
        profile (CalculateRouteProfile | Unset):
        body (CalculateRouteBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException]
    """

    kwargs = _get_kwargs(
        body=body,
        api_key=api_key,
        type_=type_,
        profile=profile,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: CalculateRouteBody,
    api_key: str,
    type_: CalculateRouteType,
    profile: CalculateRouteProfile | Unset = UNSET,
) -> ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException | None:
    """Calculate Route

     This API response is intended for use in applications requiring detailed route information and
    navigation instructions. Such applications might include: GPS navigation systems, Mapping services,
    Route optimization tools for logistics and delivery, Travel planning apps.These can guide users from
    their starting point to their destination, providing clear, step-by-step directions, estimated
    travel times, and costs associated with the journey.

    Args:
        api_key (str):
        type_ (CalculateRouteType):
        profile (CalculateRouteProfile | Unset):
        body (CalculateRouteBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException
    """

    return sync_detailed(
        client=client,
        body=body,
        api_key=api_key,
        type_=type_,
        profile=profile,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CalculateRouteBody,
    api_key: str,
    type_: CalculateRouteType,
    profile: CalculateRouteProfile | Unset = UNSET,
) -> Response[ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException]:
    """Calculate Route

     This API response is intended for use in applications requiring detailed route information and
    navigation instructions. Such applications might include: GPS navigation systems, Mapping services,
    Route optimization tools for logistics and delivery, Travel planning apps.These can guide users from
    their starting point to their destination, providing clear, step-by-step directions, estimated
    travel times, and costs associated with the journey.

    Args:
        api_key (str):
        type_ (CalculateRouteType):
        profile (CalculateRouteProfile | Unset):
        body (CalculateRouteBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException]
    """

    kwargs = _get_kwargs(
        body=body,
        api_key=api_key,
        type_=type_,
        profile=profile,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CalculateRouteBody,
    api_key: str,
    type_: CalculateRouteType,
    profile: CalculateRouteProfile | Unset = UNSET,
) -> ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException | None:
    """Calculate Route

     This API response is intended for use in applications requiring detailed route information and
    navigation instructions. Such applications might include: GPS navigation systems, Mapping services,
    Route optimization tools for logistics and delivery, Travel planning apps.These can guide users from
    their starting point to their destination, providing clear, step-by-step directions, estimated
    travel times, and costs associated with the journey.

    Args:
        api_key (str):
        type_ (CalculateRouteType):
        profile (CalculateRouteProfile | Unset):
        body (CalculateRouteBody):

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
            api_key=api_key,
            type_=type_,
            profile=profile,
        )
    ).parsed
