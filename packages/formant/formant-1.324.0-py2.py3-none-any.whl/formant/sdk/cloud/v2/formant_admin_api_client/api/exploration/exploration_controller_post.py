from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from ...client import AuthenticatedClient
from ...models.exploration import Exploration
from ...types import Response


def _get_kwargs(
    *,
    client: AuthenticatedClient,
    json_body: Exploration,

) -> Dict[str, Any]:
    url = "{}/exploration/".format(
        client.base_url)

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    

    

    

    json_json_body = json_body.to_dict()



    

    return {
	    "method": "post",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
        "json": json_json_body,
    }


def _parse_response(*, response: httpx.Response) -> Optional[Exploration]:
    if response.status_code == HTTPStatus.CREATED:
        response_201 = Exploration.from_dict(response.json())



        return response_201
    return None


def _build_response(*, response: httpx.Response) -> Response[Exploration]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    json_body: Exploration,

) -> Response[Exploration]:
    """Post

     Create an exploration
    Resource: commands
    Authorized roles: viewer

    Args:
        json_body (Exploration):

    Returns:
        Response[Exploration]
    """


    kwargs = _get_kwargs(
        client=client,
json_body=json_body,

    )

    response = httpx.request(
        verify=client.verify_ssl,
        **kwargs,
    )

    return _build_response(response=response)

def sync(
    *,
    client: AuthenticatedClient,
    json_body: Exploration,

) -> Optional[Exploration]:
    """Post

     Create an exploration
    Resource: commands
    Authorized roles: viewer

    Args:
        json_body (Exploration):

    Returns:
        Response[Exploration]
    """


    return sync_detailed(
        client=client,
json_body=json_body,

    ).parsed

async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    json_body: Exploration,

) -> Response[Exploration]:
    """Post

     Create an exploration
    Resource: commands
    Authorized roles: viewer

    Args:
        json_body (Exploration):

    Returns:
        Response[Exploration]
    """


    kwargs = _get_kwargs(
        client=client,
json_body=json_body,

    )

    async with httpx.AsyncClient(verify=client.verify_ssl) as _client:
        response = await _client.request(
            **kwargs
        )

    return _build_response(response=response)

async def asyncio(
    *,
    client: AuthenticatedClient,
    json_body: Exploration,

) -> Optional[Exploration]:
    """Post

     Create an exploration
    Resource: commands
    Authorized roles: viewer

    Args:
        json_body (Exploration):

    Returns:
        Response[Exploration]
    """


    return (await asyncio_detailed(
        client=client,
json_body=json_body,

    )).parsed

