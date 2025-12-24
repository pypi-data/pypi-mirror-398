from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.enrollment_view_request import EnrollmentViewRequest
from ...models.problem_details import ProblemDetails
from ...models.soa_enrollment_customer_account_i_read_only_list_api_result import (
    SOAEnrollmentCustomerAccountIReadOnlyListApiResult,
)
from ...models.validation_problem_details import ValidationProblemDetails
from ...types import Response


def _get_kwargs(
    *,
    body: EnrollmentViewRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1-q2/Enrollment/view/enrollment",
    }

    _body = body.to_dict()

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[ProblemDetails, SOAEnrollmentCustomerAccountIReadOnlyListApiResult, ValidationProblemDetails]]:
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
        response_200 = SOAEnrollmentCustomerAccountIReadOnlyListApiResult.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[ProblemDetails, SOAEnrollmentCustomerAccountIReadOnlyListApiResult, ValidationProblemDetails]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: EnrollmentViewRequest,
) -> Response[Union[ProblemDetails, SOAEnrollmentCustomerAccountIReadOnlyListApiResult, ValidationProblemDetails]]:
    """Get Account and Customer information.

    Args:
        body (EnrollmentViewRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ProblemDetails, SOAEnrollmentCustomerAccountIReadOnlyListApiResult, ValidationProblemDetails]]
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
    client: Union[AuthenticatedClient, Client],
    body: EnrollmentViewRequest,
) -> Optional[Union[ProblemDetails, SOAEnrollmentCustomerAccountIReadOnlyListApiResult, ValidationProblemDetails]]:
    """Get Account and Customer information.

    Args:
        body (EnrollmentViewRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ProblemDetails, SOAEnrollmentCustomerAccountIReadOnlyListApiResult, ValidationProblemDetails]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: EnrollmentViewRequest,
) -> Response[Union[ProblemDetails, SOAEnrollmentCustomerAccountIReadOnlyListApiResult, ValidationProblemDetails]]:
    """Get Account and Customer information.

    Args:
        body (EnrollmentViewRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ProblemDetails, SOAEnrollmentCustomerAccountIReadOnlyListApiResult, ValidationProblemDetails]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: EnrollmentViewRequest,
) -> Optional[Union[ProblemDetails, SOAEnrollmentCustomerAccountIReadOnlyListApiResult, ValidationProblemDetails]]:
    """Get Account and Customer information.

    Args:
        body (EnrollmentViewRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ProblemDetails, SOAEnrollmentCustomerAccountIReadOnlyListApiResult, ValidationProblemDetails]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
