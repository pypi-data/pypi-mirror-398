from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.application_dto_api_result import ApplicationDtoApiResult
from ...models.problem_details import ProblemDetails
from ...models.validation_problem_details import ValidationProblemDetails
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    application: Union[Unset, str] = UNSET,
    refresh_cache: Union[Unset, bool] = False,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["application"] = application

    params["refreshCache"] = refresh_cache

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1-q2/Config",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[ApplicationDtoApiResult, ProblemDetails, ValidationProblemDetails]]:
    if response.status_code == 400:
        response_400 = ValidationProblemDetails.from_dict(response.json())

        return response_400
    if response.status_code == 401:
        response_401 = ProblemDetails.from_dict(response.json())

        return response_401
    if response.status_code == 403:
        response_403 = ProblemDetails.from_dict(response.json())

        return response_403
    if response.status_code == 500:
        response_500 = ProblemDetails.from_dict(response.json())

        return response_500
    if response.status_code == 200:
        response_200 = ApplicationDtoApiResult.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[ApplicationDtoApiResult, ProblemDetails, ValidationProblemDetails]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    application: Union[Unset, str] = UNSET,
    refresh_cache: Union[Unset, bool] = False,
) -> Response[Union[ApplicationDtoApiResult, ProblemDetails, ValidationProblemDetails]]:
    """
    Args:
        application (Union[Unset, str]):
        refresh_cache (Union[Unset, bool]):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ApplicationDtoApiResult, ProblemDetails, ValidationProblemDetails]]
    """

    kwargs = _get_kwargs(
        application=application,
        refresh_cache=refresh_cache,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    application: Union[Unset, str] = UNSET,
    refresh_cache: Union[Unset, bool] = False,
) -> Optional[Union[ApplicationDtoApiResult, ProblemDetails, ValidationProblemDetails]]:
    """
    Args:
        application (Union[Unset, str]):
        refresh_cache (Union[Unset, bool]):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ApplicationDtoApiResult, ProblemDetails, ValidationProblemDetails]
    """

    return sync_detailed(
        client=client,
        application=application,
        refresh_cache=refresh_cache,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    application: Union[Unset, str] = UNSET,
    refresh_cache: Union[Unset, bool] = False,
) -> Response[Union[ApplicationDtoApiResult, ProblemDetails, ValidationProblemDetails]]:
    """
    Args:
        application (Union[Unset, str]):
        refresh_cache (Union[Unset, bool]):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ApplicationDtoApiResult, ProblemDetails, ValidationProblemDetails]]
    """

    kwargs = _get_kwargs(
        application=application,
        refresh_cache=refresh_cache,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    application: Union[Unset, str] = UNSET,
    refresh_cache: Union[Unset, bool] = False,
) -> Optional[Union[ApplicationDtoApiResult, ProblemDetails, ValidationProblemDetails]]:
    """
    Args:
        application (Union[Unset, str]):
        refresh_cache (Union[Unset, bool]):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ApplicationDtoApiResult, ProblemDetails, ValidationProblemDetails]
    """

    return (
        await asyncio_detailed(
            client=client,
            application=application,
            refresh_cache=refresh_cache,
        )
    ).parsed
