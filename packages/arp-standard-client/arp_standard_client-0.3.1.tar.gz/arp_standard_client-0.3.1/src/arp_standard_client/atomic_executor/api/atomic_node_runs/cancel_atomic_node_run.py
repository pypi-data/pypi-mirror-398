from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from arp_standard_model import ErrorEnvelope
from typing import cast



def _get_kwargs(
    node_run_id: str,

) -> dict[str, Any]:
    

    

    

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/atomic-node-runs/{node_run_id}:cancel".format(node_run_id=quote(str(node_run_id), safe=""),),
    }


    return _kwargs



def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Any | ErrorEnvelope:
    if response.status_code == 204:
        response_204 = cast(Any, None)
        return response_204

    if response.status_code == 401:
        response_401 = ErrorEnvelope.model_validate(response.json())



        return response_401

    if response.status_code == 403:
        response_403 = ErrorEnvelope.model_validate(response.json())



        return response_403

    response_default = ErrorEnvelope.model_validate(response.json())



    return response_default



def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[Any | ErrorEnvelope]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    node_run_id: str,
    *,
    client: AuthenticatedClient | Client,

) -> Response[Any | ErrorEnvelope]:
    """ Cancel atomic NodeRun (optional)

    Args:
        node_run_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | ErrorEnvelope]
     """


    kwargs = _get_kwargs(
        node_run_id=node_run_id,

    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)

def sync(
    node_run_id: str,
    *,
    client: AuthenticatedClient | Client,

) -> Any | ErrorEnvelope | None:
    """ Cancel atomic NodeRun (optional)

    Args:
        node_run_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | ErrorEnvelope
     """


    return sync_detailed(
        node_run_id=node_run_id,
client=client,

    ).parsed

async def asyncio_detailed(
    node_run_id: str,
    *,
    client: AuthenticatedClient | Client,

) -> Response[Any | ErrorEnvelope]:
    """ Cancel atomic NodeRun (optional)

    Args:
        node_run_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | ErrorEnvelope]
     """


    kwargs = _get_kwargs(
        node_run_id=node_run_id,

    )

    response = await client.get_async_httpx_client().request(
        **kwargs
    )

    return _build_response(client=client, response=response)

async def asyncio(
    node_run_id: str,
    *,
    client: AuthenticatedClient | Client,

) -> Any | ErrorEnvelope | None:
    """ Cancel atomic NodeRun (optional)

    Args:
        node_run_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | ErrorEnvelope
     """


    return (await asyncio_detailed(
        node_run_id=node_run_id,
client=client,

    )).parsed
