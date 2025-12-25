from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from ...client import AuthenticatedClient
from ...models.device_configuration import DeviceConfiguration
from ...types import Response


def _get_kwargs(
    id: str,
    version: str,
    *,
    client: AuthenticatedClient,

) -> Dict[str, Any]:
    url = "{}/devices/{id}/configurations/{version}".format(
        client.base_url,id=id,version=version)

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    

    

    

    

    

    return {
	    "method": "get",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
    }


def _parse_response(*, response: httpx.Response) -> Optional[Optional[DeviceConfiguration]]:
    if response.status_code == 200:
        _response_200 = response.json()
        response_200: Optional[DeviceConfiguration]
        if _response_200 is None:
            response_200 = None
        else:
            response_200 = DeviceConfiguration.from_dict(_response_200)



        return response_200
    return None


def _build_response(*, response: httpx.Response) -> Response[Optional[DeviceConfiguration]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(response=response),
    )


def sync_detailed(
    id: str,
    version: str,
    *,
    client: AuthenticatedClient,

) -> Response[Optional[DeviceConfiguration]]:
    """Get configuration

     Get a device configuration
    Resource: devices
    Authorized roles: viewer

    Args:
        id (str):
        version (str):

    Returns:
        Response[Optional[DeviceConfiguration]]
    """


    kwargs = _get_kwargs(
        id=id,
version=version,
client=client,

    )

    response = httpx.request(
        verify=client.verify_ssl,
        **kwargs,
    )

    return _build_response(response=response)

def sync(
    id: str,
    version: str,
    *,
    client: AuthenticatedClient,

) -> Optional[Optional[DeviceConfiguration]]:
    """Get configuration

     Get a device configuration
    Resource: devices
    Authorized roles: viewer

    Args:
        id (str):
        version (str):

    Returns:
        Response[Optional[DeviceConfiguration]]
    """


    return sync_detailed(
        id=id,
version=version,
client=client,

    ).parsed

async def asyncio_detailed(
    id: str,
    version: str,
    *,
    client: AuthenticatedClient,

) -> Response[Optional[DeviceConfiguration]]:
    """Get configuration

     Get a device configuration
    Resource: devices
    Authorized roles: viewer

    Args:
        id (str):
        version (str):

    Returns:
        Response[Optional[DeviceConfiguration]]
    """


    kwargs = _get_kwargs(
        id=id,
version=version,
client=client,

    )

    async with httpx.AsyncClient(verify=client.verify_ssl) as _client:
        response = await _client.request(
            **kwargs
        )

    return _build_response(response=response)

async def asyncio(
    id: str,
    version: str,
    *,
    client: AuthenticatedClient,

) -> Optional[Optional[DeviceConfiguration]]:
    """Get configuration

     Get a device configuration
    Resource: devices
    Authorized roles: viewer

    Args:
        id (str):
        version (str):

    Returns:
        Response[Optional[DeviceConfiguration]]
    """


    return (await asyncio_detailed(
        id=id,
version=version,
client=client,

    )).parsed

