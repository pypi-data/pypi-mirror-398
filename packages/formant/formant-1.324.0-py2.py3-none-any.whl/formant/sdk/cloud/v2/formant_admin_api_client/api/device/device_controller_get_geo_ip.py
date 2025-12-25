from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ...client import AuthenticatedClient
from ...models.geo_ip import GeoIp
from ...types import UNSET, Response, Unset


def _get_kwargs(
    id: str,
    *,
    client: AuthenticatedClient,
    x_forwarded_for: Union[Unset, str] = UNSET,

) -> Dict[str, Any]:
    url = "{}/devices/{id}/geoip".format(
        client.base_url,id=id)

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    if not isinstance(x_forwarded_for, Unset):
        headers["x-forwarded-for"] = x_forwarded_for



    

    

    

    

    return {
	    "method": "get",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
    }


def _parse_response(*, response: httpx.Response) -> Optional[GeoIp]:
    if response.status_code == HTTPStatus.OK:
        response_200 = GeoIp.from_dict(response.json())



        return response_200
    return None


def _build_response(*, response: httpx.Response) -> Response[GeoIp]:
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
    x_forwarded_for: Union[Unset, str] = UNSET,

) -> Response[GeoIp]:
    """Get geo ip

     Get GeoIP for device
    Resource: devices
    Authorized roles: device

    Args:
        id (str):
        x_forwarded_for (Union[Unset, str]):

    Returns:
        Response[GeoIp]
    """


    kwargs = _get_kwargs(
        id=id,
client=client,
x_forwarded_for=x_forwarded_for,

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
    x_forwarded_for: Union[Unset, str] = UNSET,

) -> Optional[GeoIp]:
    """Get geo ip

     Get GeoIP for device
    Resource: devices
    Authorized roles: device

    Args:
        id (str):
        x_forwarded_for (Union[Unset, str]):

    Returns:
        Response[GeoIp]
    """


    return sync_detailed(
        id=id,
client=client,
x_forwarded_for=x_forwarded_for,

    ).parsed

async def asyncio_detailed(
    id: str,
    *,
    client: AuthenticatedClient,
    x_forwarded_for: Union[Unset, str] = UNSET,

) -> Response[GeoIp]:
    """Get geo ip

     Get GeoIP for device
    Resource: devices
    Authorized roles: device

    Args:
        id (str):
        x_forwarded_for (Union[Unset, str]):

    Returns:
        Response[GeoIp]
    """


    kwargs = _get_kwargs(
        id=id,
client=client,
x_forwarded_for=x_forwarded_for,

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
    x_forwarded_for: Union[Unset, str] = UNSET,

) -> Optional[GeoIp]:
    """Get geo ip

     Get GeoIP for device
    Resource: devices
    Authorized roles: device

    Args:
        id (str):
        x_forwarded_for (Union[Unset, str]):

    Returns:
        Response[GeoIp]
    """


    return (await asyncio_detailed(
        id=id,
client=client,
x_forwarded_for=x_forwarded_for,

    )).parsed

