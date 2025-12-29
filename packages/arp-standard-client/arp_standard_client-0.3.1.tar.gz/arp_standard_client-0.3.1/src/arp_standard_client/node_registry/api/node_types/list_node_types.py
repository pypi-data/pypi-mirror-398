from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from arp_standard_model import ErrorEnvelope
from arp_standard_model import NodeKind
from arp_standard_model import NodeType
from ...types import UNSET, Unset
from typing import cast



def _get_kwargs(
    *,
    q: str | Unset = UNSET,
    kind: NodeKind | Unset = UNSET,

) -> dict[str, Any]:
    

    

    params: dict[str, Any] = {}

    params["q"] = q

    json_kind: str | Unset = UNSET
    if not isinstance(kind, Unset):
        json_kind = kind.value

    params["kind"] = json_kind


    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}


    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/node-types",
        "params": params,
    }


    return _kwargs



def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> ErrorEnvelope | list[NodeType]:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in (_response_200):
            response_200_item = NodeType.model_validate(response_200_item_data)



            response_200.append(response_200_item)

        return response_200

    if response.status_code == 401:
        response_401 = ErrorEnvelope.model_validate(response.json())



        return response_401

    if response.status_code == 403:
        response_403 = ErrorEnvelope.model_validate(response.json())



        return response_403

    response_default = ErrorEnvelope.model_validate(response.json())



    return response_default



def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[ErrorEnvelope | list[NodeType]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    q: str | Unset = UNSET,
    kind: NodeKind | Unset = UNSET,

) -> Response[ErrorEnvelope | list[NodeType]]:
    """ List node types

    Args:
        q (str | Unset):
        kind (NodeKind | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorEnvelope | list[NodeType]]
     """


    kwargs = _get_kwargs(
        q=q,
kind=kind,

    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)

def sync(
    *,
    client: AuthenticatedClient | Client,
    q: str | Unset = UNSET,
    kind: NodeKind | Unset = UNSET,

) -> ErrorEnvelope | list[NodeType] | None:
    """ List node types

    Args:
        q (str | Unset):
        kind (NodeKind | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorEnvelope | list[NodeType]
     """


    return sync_detailed(
        client=client,
q=q,
kind=kind,

    ).parsed

async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    q: str | Unset = UNSET,
    kind: NodeKind | Unset = UNSET,

) -> Response[ErrorEnvelope | list[NodeType]]:
    """ List node types

    Args:
        q (str | Unset):
        kind (NodeKind | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorEnvelope | list[NodeType]]
     """


    kwargs = _get_kwargs(
        q=q,
kind=kind,

    )

    response = await client.get_async_httpx_client().request(
        **kwargs
    )

    return _build_response(client=client, response=response)

async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    q: str | Unset = UNSET,
    kind: NodeKind | Unset = UNSET,

) -> ErrorEnvelope | list[NodeType] | None:
    """ List node types

    Args:
        q (str | Unset):
        kind (NodeKind | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorEnvelope | list[NodeType]
     """


    return (await asyncio_detailed(
        client=client,
q=q,
kind=kind,

    )).parsed
