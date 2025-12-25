from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from ...client import AuthenticatedClient
from ...models.device import Device
from ...models.partial_device import PartialDevice
from ...types import Response


def _get_kwargs(
    id: str,
    *,
    client: AuthenticatedClient,
    json_body: PartialDevice,

) -> Dict[str, Any]:
    url = "{}/devices/{id}".format(
        client.base_url,id=id)

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    

    

    

    json_json_body = json_body.to_dict()



    

    return {
	    "method": "patch",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
        "json": json_json_body,
    }


def _parse_response(*, response: httpx.Response) -> Optional[Device]:
    if response.status_code == 200:
        response_200 = Device.from_dict(response.json())



        return response_200
    return None


def _build_response(*, response: httpx.Response) -> Response[Device]:
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
    json_body: PartialDevice,

) -> Response[Device]:
    """Patch

     Update an existing device.
    Resource: devices
    Authorized roles: administrator, device

    Args:
        id (str):
        json_body (PartialDevice):

    Returns:
        Response[Device]
    """


    kwargs = _get_kwargs(
        id=id,
client=client,
json_body=json_body,

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
    json_body: PartialDevice,

) -> Optional[Device]:
    """Patch

     Update an existing device.
    Resource: devices
    Authorized roles: administrator, device

    Args:
        id (str):
        json_body (PartialDevice):

    Returns:
        Response[Device]
    """


    return sync_detailed(
        id=id,
client=client,
json_body=json_body,

    ).parsed

async def asyncio_detailed(
    id: str,
    *,
    client: AuthenticatedClient,
    json_body: PartialDevice,

) -> Response[Device]:
    """Patch

     Update an existing device.
    Resource: devices
    Authorized roles: administrator, device

    Args:
        id (str):
        json_body (PartialDevice):

    Returns:
        Response[Device]
    """


    kwargs = _get_kwargs(
        id=id,
client=client,
json_body=json_body,

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
    json_body: PartialDevice,

) -> Optional[Device]:
    """Patch

     Update an existing device.
    Resource: devices
    Authorized roles: administrator, device

    Args:
        id (str):
        json_body (PartialDevice):

    Returns:
        Response[Device]
    """


    return (await asyncio_detailed(
        id=id,
client=client,
json_body=json_body,

    )).parsed

