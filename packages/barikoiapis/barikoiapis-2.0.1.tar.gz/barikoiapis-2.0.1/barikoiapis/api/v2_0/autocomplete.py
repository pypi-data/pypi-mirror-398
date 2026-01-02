from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.api_limit_exceeded import ApiLimitExceeded
from ...models.autocomplete_success import AutocompleteSuccess
from ...models.missing_parameter import MissingParameter
from ...models.no_registered_key import NoRegisteredKey
from ...models.payment_exception import PaymentException
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    api_key: str,
    q: str,
    bangla: bool | Unset = True,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["api_key"] = api_key

    params["q"] = q

    params["bangla"] = bangla

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v2/api/search/autocomplete/place",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ApiLimitExceeded | AutocompleteSuccess | MissingParameter | NoRegisteredKey | PaymentException | None:
    if response.status_code == 200:
        response_200 = AutocompleteSuccess.from_dict(response.json())

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
) -> Response[ApiLimitExceeded | AutocompleteSuccess | MissingParameter | NoRegisteredKey | PaymentException]:
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
    bangla: bool | Unset = True,
) -> Response[ApiLimitExceeded | AutocompleteSuccess | MissingParameter | NoRegisteredKey | PaymentException]:
    """Autocomplete

     Barikoi Autocomplete API endpoint provides autocomplete suggestions for place names based on a query
    string. It returns a list of matching places with detailed information including addresses in both
    English and Bangla, as well as geographic coordinates. Barikoi Autocomplete API is useful for
    providing real-time, location-based search suggestions to users as they type, enhancing the user
    experience by quickly narrowing down potential matches based on partial input.

    Args:
        api_key (str):
        q (str):
        bangla (bool | Unset):  Default: True.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiLimitExceeded | AutocompleteSuccess | MissingParameter | NoRegisteredKey | PaymentException]
    """

    kwargs = _get_kwargs(
        api_key=api_key,
        q=q,
        bangla=bangla,
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
    bangla: bool | Unset = True,
) -> ApiLimitExceeded | AutocompleteSuccess | MissingParameter | NoRegisteredKey | PaymentException | None:
    """Autocomplete

     Barikoi Autocomplete API endpoint provides autocomplete suggestions for place names based on a query
    string. It returns a list of matching places with detailed information including addresses in both
    English and Bangla, as well as geographic coordinates. Barikoi Autocomplete API is useful for
    providing real-time, location-based search suggestions to users as they type, enhancing the user
    experience by quickly narrowing down potential matches based on partial input.

    Args:
        api_key (str):
        q (str):
        bangla (bool | Unset):  Default: True.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiLimitExceeded | AutocompleteSuccess | MissingParameter | NoRegisteredKey | PaymentException
    """

    return sync_detailed(
        client=client,
        api_key=api_key,
        q=q,
        bangla=bangla,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    api_key: str,
    q: str,
    bangla: bool | Unset = True,
) -> Response[ApiLimitExceeded | AutocompleteSuccess | MissingParameter | NoRegisteredKey | PaymentException]:
    """Autocomplete

     Barikoi Autocomplete API endpoint provides autocomplete suggestions for place names based on a query
    string. It returns a list of matching places with detailed information including addresses in both
    English and Bangla, as well as geographic coordinates. Barikoi Autocomplete API is useful for
    providing real-time, location-based search suggestions to users as they type, enhancing the user
    experience by quickly narrowing down potential matches based on partial input.

    Args:
        api_key (str):
        q (str):
        bangla (bool | Unset):  Default: True.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiLimitExceeded | AutocompleteSuccess | MissingParameter | NoRegisteredKey | PaymentException]
    """

    kwargs = _get_kwargs(
        api_key=api_key,
        q=q,
        bangla=bangla,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    api_key: str,
    q: str,
    bangla: bool | Unset = True,
) -> ApiLimitExceeded | AutocompleteSuccess | MissingParameter | NoRegisteredKey | PaymentException | None:
    """Autocomplete

     Barikoi Autocomplete API endpoint provides autocomplete suggestions for place names based on a query
    string. It returns a list of matching places with detailed information including addresses in both
    English and Bangla, as well as geographic coordinates. Barikoi Autocomplete API is useful for
    providing real-time, location-based search suggestions to users as they type, enhancing the user
    experience by quickly narrowing down potential matches based on partial input.

    Args:
        api_key (str):
        q (str):
        bangla (bool | Unset):  Default: True.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiLimitExceeded | AutocompleteSuccess | MissingParameter | NoRegisteredKey | PaymentException
    """

    return (
        await asyncio_detailed(
            client=client,
            api_key=api_key,
            q=q,
            bangla=bangla,
        )
    ).parsed
