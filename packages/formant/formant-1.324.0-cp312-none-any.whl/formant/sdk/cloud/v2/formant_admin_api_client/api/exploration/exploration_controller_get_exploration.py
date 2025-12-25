from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from ...client import AuthenticatedClient
from ...models.exploration import Exploration
from ...types import Response


def _get_kwargs(
    id: str,
    *,
    client: AuthenticatedClient,

) -> Dict[str, Any]:
    url = "{}/exploration/{id}".format(
        client.base_url,id=id)

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    

    

    

    

    

    return {
	    "method": "get",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
    }


def _parse_response(*, response: httpx.Response) -> Optional[Exploration]:
    if response.status_code == 200:
        response_200 = Exploration.from_dict(response.json())



        return response_200
    return None


def _build_response(*, response: httpx.Response) -> Response[Exploration]:
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

) -> Response[Exploration]:
    """Get exploration

     Get an exploration
    Resource: commands
    Authorized roles: viewer

    Args:
        id (str):

    Returns:
        Response[Exploration]
    """


    kwargs = _get_kwargs(
        id=id,
client=client,

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

) -> Optional[Exploration]:
    """Get exploration

     Get an exploration
    Resource: commands
    Authorized roles: viewer

    Args:
        id (str):

    Returns:
        Response[Exploration]
    """


    return sync_detailed(
        id=id,
client=client,

    ).parsed

async def asyncio_detailed(
    id: str,
    *,
    client: AuthenticatedClient,

) -> Response[Exploration]:
    """Get exploration

     Get an exploration
    Resource: commands
    Authorized roles: viewer

    Args:
        id (str):

    Returns:
        Response[Exploration]
    """


    kwargs = _get_kwargs(
        id=id,
client=client,

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

) -> Optional[Exploration]:
    """Get exploration

     Get an exploration
    Resource: commands
    Authorized roles: viewer

    Args:
        id (str):

    Returns:
        Response[Exploration]
    """


    return (await asyncio_detailed(
        id=id,
client=client,

    )).parsed

