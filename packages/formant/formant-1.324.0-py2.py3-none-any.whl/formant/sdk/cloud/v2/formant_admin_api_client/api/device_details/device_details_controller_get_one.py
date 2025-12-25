from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ...client import AuthenticatedClient
from ...models.device_details import DeviceDetails
from ...types import UNSET, Response, Unset


def _get_kwargs(
    id: str,
    *,
    client: AuthenticatedClient,
    fill_online_status: Union[Unset, None, bool] = UNSET,
    fill_last_seen: Union[Unset, None, bool] = UNSET,

) -> Dict[str, Any]:
    url = "{}/device-details/{id}".format(
        client.base_url,id=id)

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    

    

    params: Dict[str, Any] = {}
    params["fillOnlineStatus"] = fill_online_status


    params["fillLastSeen"] = fill_last_seen



    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}


    

    

    return {
	    "method": "get",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
        "params": params,
    }


def _parse_response(*, response: httpx.Response) -> Optional[DeviceDetails]:
    if response.status_code == HTTPStatus.OK:
        response_200 = DeviceDetails.from_dict(response.json())



        return response_200
    return None


def _build_response(*, response: httpx.Response) -> Response[DeviceDetails]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(response=response),
    )


def sync_detailed(
    id: str,
    *,
    client: AuthenticatedClient,
    fill_online_status: Union[Unset, None, bool] = UNSET,
    fill_last_seen: Union[Unset, None, bool] = UNSET,

) -> Response[DeviceDetails]:
    """Get one

     Get device details by device ID.
    Resource: devices
    Authorized roles: viewer

    Args:
        id (str):
        fill_online_status (Union[Unset, None, bool]):
        fill_last_seen (Union[Unset, None, bool]):

    Returns:
        Response[DeviceDetails]
    """


    kwargs = _get_kwargs(
        id=id,
client=client,
fill_online_status=fill_online_status,
fill_last_seen=fill_last_seen,

    )

    response = httpx.request(
        verify=client.verify_ssl,
        **kwargs,
    )

    return _build_response(response=response)

def sync(
    id: str,
    *,
    client: AuthenticatedClient,
    fill_online_status: Union[Unset, None, bool] = UNSET,
    fill_last_seen: Union[Unset, None, bool] = UNSET,

) -> Optional[DeviceDetails]:
    """Get one

     Get device details by device ID.
    Resource: devices
    Authorized roles: viewer

    Args:
        id (str):
        fill_online_status (Union[Unset, None, bool]):
        fill_last_seen (Union[Unset, None, bool]):

    Returns:
        Response[DeviceDetails]
    """


    return sync_detailed(
        id=id,
client=client,
fill_online_status=fill_online_status,
fill_last_seen=fill_last_seen,

    ).parsed

async def asyncio_detailed(
    id: str,
    *,
    client: AuthenticatedClient,
    fill_online_status: Union[Unset, None, bool] = UNSET,
    fill_last_seen: Union[Unset, None, bool] = UNSET,

) -> Response[DeviceDetails]:
    """Get one

     Get device details by device ID.
    Resource: devices
    Authorized roles: viewer

    Args:
        id (str):
        fill_online_status (Union[Unset, None, bool]):
        fill_last_seen (Union[Unset, None, bool]):

    Returns:
        Response[DeviceDetails]
    """


    kwargs = _get_kwargs(
        id=id,
client=client,
fill_online_status=fill_online_status,
fill_last_seen=fill_last_seen,

    )

    async with httpx.AsyncClient(verify=client.verify_ssl) as _client:
        response = await _client.request(
            **kwargs
        )

    return _build_response(response=response)

async def asyncio(
    id: str,
    *,
    client: AuthenticatedClient,
    fill_online_status: Union[Unset, None, bool] = UNSET,
    fill_last_seen: Union[Unset, None, bool] = UNSET,

) -> Optional[DeviceDetails]:
    """Get one

     Get device details by device ID.
    Resource: devices
    Authorized roles: viewer

    Args:
        id (str):
        fill_online_status (Union[Unset, None, bool]):
        fill_last_seen (Union[Unset, None, bool]):

    Returns:
        Response[DeviceDetails]
    """


    return (await asyncio_detailed(
        id=id,
client=client,
fill_online_status=fill_online_status,
fill_last_seen=fill_last_seen,

    )).parsed

