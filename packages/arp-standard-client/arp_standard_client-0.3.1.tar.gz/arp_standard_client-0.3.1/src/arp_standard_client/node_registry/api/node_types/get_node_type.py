from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from arp_standard_model import ErrorEnvelope
from arp_standard_model import NodeType
from ...types import UNSET, Unset
from typing import cast



def _get_kwargs(
    node_type_id: str,
    *,
    version: str | Unset = UNSET,

) -> dict[str, Any]:
    

    

    params: dict[str, Any] = {}

    params["version"] = version


    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}


    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/node-types/{node_type_id}".format(node_type_id=quote(str(node_type_id), safe=""),),
        "params": params,
    }


    return _kwargs



def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> ErrorEnvelope | NodeType:
    if response.status_code == 200:
        response_200 = NodeType.model_validate(response.json())



        return response_200

    if response.status_code == 401:
        response_401 = ErrorEnvelope.model_validate(response.json())



        return response_401

    if response.status_code == 403:
        response_403 = ErrorEnvelope.model_validate(response.json())



        return response_403

    response_default = ErrorEnvelope.model_validate(response.json())



    return response_default



def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[ErrorEnvelope | NodeType]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    node_type_id: str,
    *,
    client: AuthenticatedClient | Client,
    version: str | Unset = UNSET,

) -> Response[ErrorEnvelope | NodeType]:
    """ Get node type

    Args:
        node_type_id (str):
        version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorEnvelope | NodeType]
     """


    kwargs = _get_kwargs(
        node_type_id=node_type_id,
version=version,

    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)

def sync(
    node_type_id: str,
    *,
    client: AuthenticatedClient | Client,
    version: str | Unset = UNSET,

) -> ErrorEnvelope | NodeType | None:
    """ Get node type

    Args:
        node_type_id (str):
        version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorEnvelope | NodeType
     """


    return sync_detailed(
        node_type_id=node_type_id,
client=client,
version=version,

    ).parsed

async def asyncio_detailed(
    node_type_id: str,
    *,
    client: AuthenticatedClient | Client,
    version: str | Unset = UNSET,

) -> Response[ErrorEnvelope | NodeType]:
    """ Get node type

    Args:
        node_type_id (str):
        version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorEnvelope | NodeType]
     """


    kwargs = _get_kwargs(
        node_type_id=node_type_id,
version=version,

    )

    response = await client.get_async_httpx_client().request(
        **kwargs
    )

    return _build_response(client=client, response=response)

async def asyncio(
    node_type_id: str,
    *,
    client: AuthenticatedClient | Client,
    version: str | Unset = UNSET,

) -> ErrorEnvelope | NodeType | None:
    """ Get node type

    Args:
        node_type_id (str):
        version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorEnvelope | NodeType
     """


    return (await asyncio_detailed(
        node_type_id=node_type_id,
client=client,
version=version,

    )).parsed
