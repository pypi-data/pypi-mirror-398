from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ...client import AuthenticatedClient
from ...models.metadata_with_current_value import MetadataWithCurrentValue
from ...types import UNSET, Response, Unset


def _get_kwargs(
    id: str,
    *,
    client: AuthenticatedClient,
    range_days: Union[Unset, None, int] = UNSET,

) -> Dict[str, Any]:
    url = "{}/metadata/{id}/current-value".format(
        client.base_url,id=id)

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    

    

    params: Dict[str, Any] = {}
    params["rangeDays"] = range_days



    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}


    

    

    return {
	    "method": "get",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
        "params": params,
    }


def _parse_response(*, response: httpx.Response) -> Optional[MetadataWithCurrentValue]:
    if response.status_code == 200:
        response_200 = MetadataWithCurrentValue.from_dict(response.json())



        return response_200
    return None


def _build_response(*, response: httpx.Response) -> Response[MetadataWithCurrentValue]:
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
    range_days: Union[Unset, None, int] = UNSET,

) -> Response[MetadataWithCurrentValue]:
    """Lastest value for metadata id

     Resource: streams
    Authorized roles: viewer

    Args:
        id (str):
        range_days (Union[Unset, None, int]):

    Returns:
        Response[MetadataWithCurrentValue]
    """


    kwargs = _get_kwargs(
        id=id,
client=client,
range_days=range_days,

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
    range_days: Union[Unset, None, int] = UNSET,

) -> Optional[MetadataWithCurrentValue]:
    """Lastest value for metadata id

     Resource: streams
    Authorized roles: viewer

    Args:
        id (str):
        range_days (Union[Unset, None, int]):

    Returns:
        Response[MetadataWithCurrentValue]
    """


    return sync_detailed(
        id=id,
client=client,
range_days=range_days,

    ).parsed

async def asyncio_detailed(
    id: str,
    *,
    client: AuthenticatedClient,
    range_days: Union[Unset, None, int] = UNSET,

) -> Response[MetadataWithCurrentValue]:
    """Lastest value for metadata id

     Resource: streams
    Authorized roles: viewer

    Args:
        id (str):
        range_days (Union[Unset, None, int]):

    Returns:
        Response[MetadataWithCurrentValue]
    """


    kwargs = _get_kwargs(
        id=id,
client=client,
range_days=range_days,

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
    range_days: Union[Unset, None, int] = UNSET,

) -> Optional[MetadataWithCurrentValue]:
    """Lastest value for metadata id

     Resource: streams
    Authorized roles: viewer

    Args:
        id (str):
        range_days (Union[Unset, None, int]):

    Returns:
        Response[MetadataWithCurrentValue]
    """


    return (await asyncio_detailed(
        id=id,
client=client,
range_days=range_days,

    )).parsed

