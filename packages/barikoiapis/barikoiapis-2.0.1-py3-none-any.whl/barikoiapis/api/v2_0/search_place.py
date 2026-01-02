from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.api_limit_exceeded import ApiLimitExceeded
from ...models.missing_parameter import MissingParameter
from ...models.no_registered_key import NoRegisteredKey
from ...models.payment_exception import PaymentException
from ...models.search_place_success import SearchPlaceSuccess
from ...types import UNSET, Response


def _get_kwargs(
    *,
    api_key: str,
    q: str,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["api_key"] = api_key

    params["q"] = q

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v2/search-place",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException | SearchPlaceSuccess | None:
    if response.status_code == 200:
        response_200 = SearchPlaceSuccess.from_dict(response.json())

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
) -> Response[ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException | SearchPlaceSuccess]:
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
    q: str,
) -> Response[ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException | SearchPlaceSuccess]:
    """Search Place

     This API endpoint searches for places that match a given query string. It returns a list of matching
    places, including their addresses and unique place codes. This API is useful for searching and
    retrieving detailed information about places based on a given query string, which can be helpful for
    location-based services, mapping, and navigation applications.

    **Note: Each request to this API generates a new session ID. The session ID is crucial for testing
    and tracking API interactions. Make sure to include the session ID in** [<b>Get Place
    Details</b>](https://docs.barikoi.com/api#tag/v2.0/operation/Search_PlGet_Place_Detailsace) **API
    request to ensure proper functionality.**

    Args:
        api_key (str):
        q (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException | SearchPlaceSuccess]
    """

    kwargs = _get_kwargs(
        api_key=api_key,
        q=q,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    api_key: str,
    q: str,
) -> ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException | SearchPlaceSuccess | None:
    """Search Place

     This API endpoint searches for places that match a given query string. It returns a list of matching
    places, including their addresses and unique place codes. This API is useful for searching and
    retrieving detailed information about places based on a given query string, which can be helpful for
    location-based services, mapping, and navigation applications.

    **Note: Each request to this API generates a new session ID. The session ID is crucial for testing
    and tracking API interactions. Make sure to include the session ID in** [<b>Get Place
    Details</b>](https://docs.barikoi.com/api#tag/v2.0/operation/Search_PlGet_Place_Detailsace) **API
    request to ensure proper functionality.**

    Args:
        api_key (str):
        q (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException | SearchPlaceSuccess
    """

    return sync_detailed(
        client=client,
        api_key=api_key,
        q=q,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    api_key: str,
    q: str,
) -> Response[ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException | SearchPlaceSuccess]:
    """Search Place

     This API endpoint searches for places that match a given query string. It returns a list of matching
    places, including their addresses and unique place codes. This API is useful for searching and
    retrieving detailed information about places based on a given query string, which can be helpful for
    location-based services, mapping, and navigation applications.

    **Note: Each request to this API generates a new session ID. The session ID is crucial for testing
    and tracking API interactions. Make sure to include the session ID in** [<b>Get Place
    Details</b>](https://docs.barikoi.com/api#tag/v2.0/operation/Search_PlGet_Place_Detailsace) **API
    request to ensure proper functionality.**

    Args:
        api_key (str):
        q (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException | SearchPlaceSuccess]
    """

    kwargs = _get_kwargs(
        api_key=api_key,
        q=q,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    api_key: str,
    q: str,
) -> ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException | SearchPlaceSuccess | None:
    """Search Place

     This API endpoint searches for places that match a given query string. It returns a list of matching
    places, including their addresses and unique place codes. This API is useful for searching and
    retrieving detailed information about places based on a given query string, which can be helpful for
    location-based services, mapping, and navigation applications.

    **Note: Each request to this API generates a new session ID. The session ID is crucial for testing
    and tracking API interactions. Make sure to include the session ID in** [<b>Get Place
    Details</b>](https://docs.barikoi.com/api#tag/v2.0/operation/Search_PlGet_Place_Detailsace) **API
    request to ensure proper functionality.**

    Args:
        api_key (str):
        q (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiLimitExceeded | MissingParameter | NoRegisteredKey | PaymentException | SearchPlaceSuccess
    """

    return (
        await asyncio_detailed(
            client=client,
            api_key=api_key,
            q=q,
        )
    ).parsed
