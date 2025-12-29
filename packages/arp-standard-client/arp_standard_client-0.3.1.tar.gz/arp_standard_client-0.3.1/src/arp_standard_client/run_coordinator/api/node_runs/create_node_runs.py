from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from arp_standard_model import ErrorEnvelope
from arp_standard_model import NodeRunsCreateRequest
from arp_standard_model import NodeRunsCreateResponse
from typing import cast



def _get_kwargs(
    *,
    body: NodeRunsCreateRequest,

) -> dict[str, Any]:
    headers: dict[str, Any] = {}


    

    

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/node-runs",
    }

    _kwargs["json"] = body.model_dump(exclude_none=True)


    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs



def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> ErrorEnvelope | NodeRunsCreateResponse:
    if response.status_code == 200:
        response_200 = NodeRunsCreateResponse.model_validate(response.json())



        return response_200

    if response.status_code == 401:
        response_401 = ErrorEnvelope.model_validate(response.json())



        return response_401

    if response.status_code == 403:
        response_403 = ErrorEnvelope.model_validate(response.json())



        return response_403

    response_default = ErrorEnvelope.model_validate(response.json())



    return response_default



def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[ErrorEnvelope | NodeRunsCreateResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: NodeRunsCreateRequest,

) -> Response[ErrorEnvelope | NodeRunsCreateResponse]:
    """ Create NodeRuns (subtasks)

    Args:
        body (NodeRunsCreateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorEnvelope | NodeRunsCreateResponse]
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
    client: AuthenticatedClient | Client,
    body: NodeRunsCreateRequest,

) -> ErrorEnvelope | NodeRunsCreateResponse | None:
    """ Create NodeRuns (subtasks)

    Args:
        body (NodeRunsCreateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorEnvelope | NodeRunsCreateResponse
     """


    return sync_detailed(
        client=client,
body=body,

    ).parsed

async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: NodeRunsCreateRequest,

) -> Response[ErrorEnvelope | NodeRunsCreateResponse]:
    """ Create NodeRuns (subtasks)

    Args:
        body (NodeRunsCreateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorEnvelope | NodeRunsCreateResponse]
     """


    kwargs = _get_kwargs(
        body=body,

    )

    response = await client.get_async_httpx_client().request(
        **kwargs
    )

    return _build_response(client=client, response=response)

async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: NodeRunsCreateRequest,

) -> ErrorEnvelope | NodeRunsCreateResponse | None:
    """ Create NodeRuns (subtasks)

    Args:
        body (NodeRunsCreateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorEnvelope | NodeRunsCreateResponse
     """


    return (await asyncio_detailed(
        client=client,
body=body,

    )).parsed
