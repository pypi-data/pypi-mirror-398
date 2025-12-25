from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ...client import AuthenticatedClient
from ...models.stream_list_response import StreamListResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    client: AuthenticatedClient,
    active: Union[Unset, None, bool] = UNSET,

) -> Dict[str, Any]:
    url = "{}/streams/".format(
        client.base_url)

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    

    

    params: Dict[str, Any] = {}
    params["active"] = active



    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}


    

    

    return {
	    "method": "get",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
        "params": params,
    }


def _parse_response(*, response: httpx.Response) -> Optional[StreamListResponse]:
    if response.status_code == 200:
        response_200 = StreamListResponse.from_dict(response.json())



        return response_200
    return None


def _build_response(*, response: httpx.Response) -> Response[StreamListResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    active: Union[Unset, None, bool] = UNSET,

) -> Response[StreamListResponse]:
    """List

     List streams
    Resource: streams
    Authorized roles: viewer

    Args:
        active (Union[Unset, None, bool]):

    Returns:
        Response[StreamListResponse]
    """


    kwargs = _get_kwargs(
        client=client,
active=active,

    )

    response = httpx.request(
        verify=client.verify_ssl,
        **kwargs,
    )

    return _build_response(response=response)

def sync(
    *,
    client: AuthenticatedClient,
    active: Union[Unset, None, bool] = UNSET,

) -> Optional[StreamListResponse]:
    """List

     List streams
    Resource: streams
    Authorized roles: viewer

    Args:
        active (Union[Unset, None, bool]):

    Returns:
        Response[StreamListResponse]
    """


    return sync_detailed(
        client=client,
active=active,

    ).parsed

async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    active: Union[Unset, None, bool] = UNSET,

) -> Response[StreamListResponse]:
    """List

     List streams
    Resource: streams
    Authorized roles: viewer

    Args:
        active (Union[Unset, None, bool]):

    Returns:
        Response[StreamListResponse]
    """


    kwargs = _get_kwargs(
        client=client,
active=active,

    )

    async with httpx.AsyncClient(verify=client.verify_ssl) as _client:
        response = await _client.request(
            **kwargs
        )

    return _build_response(response=response)

async def asyncio(
    *,
    client: AuthenticatedClient,
    active: Union[Unset, None, bool] = UNSET,

) -> Optional[StreamListResponse]:
    """List

     List streams
    Resource: streams
    Authorized roles: viewer

    Args:
        active (Union[Unset, None, bool]):

    Returns:
        Response[StreamListResponse]
    """


    return (await asyncio_detailed(
        client=client,
active=active,

    )).parsed

