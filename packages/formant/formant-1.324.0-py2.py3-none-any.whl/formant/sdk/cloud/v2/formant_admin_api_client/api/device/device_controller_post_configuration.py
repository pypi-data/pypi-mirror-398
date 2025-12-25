from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from ...client import AuthenticatedClient
from ...models.device_configuration import DeviceConfiguration
from ...types import Response


def _get_kwargs(
    id: str,
    *,
    client: AuthenticatedClient,
    json_body: Optional[DeviceConfiguration],

) -> Dict[str, Any]:
    url = "{}/devices/{id}/configurations".format(
        client.base_url,id=id)

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    

    

    

    json_json_body = json_body.to_dict() if json_body else None



    

    return {
	    "method": "post",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
        "json": json_json_body,
    }


def _parse_response(*, response: httpx.Response) -> Optional[Optional[DeviceConfiguration]]:
    if response.status_code == HTTPStatus.CREATED:
        _response_201 = response.json()
        response_201: Optional[DeviceConfiguration]
        if _response_201 is None:
            response_201 = None
        else:
            response_201 = DeviceConfiguration.from_dict(_response_201)



        return response_201
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
    *,
    client: AuthenticatedClient,
    json_body: Optional[DeviceConfiguration],

) -> Response[Optional[DeviceConfiguration]]:
    """Post configuration

     Create a device configuration
    Resource: devices
    Authorized roles: administrator

    Args:
        id (str):
        json_body (Optional[DeviceConfiguration]):

    Returns:
        Response[Optional[DeviceConfiguration]]
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
    json_body: Optional[DeviceConfiguration],

) -> Optional[Optional[DeviceConfiguration]]:
    """Post configuration

     Create a device configuration
    Resource: devices
    Authorized roles: administrator

    Args:
        id (str):
        json_body (Optional[DeviceConfiguration]):

    Returns:
        Response[Optional[DeviceConfiguration]]
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
    json_body: Optional[DeviceConfiguration],

) -> Response[Optional[DeviceConfiguration]]:
    """Post configuration

     Create a device configuration
    Resource: devices
    Authorized roles: administrator

    Args:
        id (str):
        json_body (Optional[DeviceConfiguration]):

    Returns:
        Response[Optional[DeviceConfiguration]]
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
    json_body: Optional[DeviceConfiguration],

) -> Optional[Optional[DeviceConfiguration]]:
    """Post configuration

     Create a device configuration
    Resource: devices
    Authorized roles: administrator

    Args:
        id (str):
        json_body (Optional[DeviceConfiguration]):

    Returns:
        Response[Optional[DeviceConfiguration]]
    """


    return (await asyncio_detailed(
        id=id,
client=client,
json_body=json_body,

    )).parsed

