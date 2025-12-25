from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from ...client import AuthenticatedClient
from ...models.command import Command
from ...types import Response


def _get_kwargs(
    *,
    client: AuthenticatedClient,
    json_body: Command,

) -> Dict[str, Any]:
    url = "{}/commands".format(
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


def _parse_response(*, response: httpx.Response) -> Optional[Command]:
    if response.status_code == 201:
        response_201 = Command.from_dict(response.json())



        return response_201
    return None


def _build_response(*, response: httpx.Response) -> Response[Command]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    json_body: Command,

) -> Response[Command]:
    """Post

     Create a new command instance.
    Resource: commands
    Authorized roles: operator

    Args:
        json_body (Command):

    Returns:
        Response[Command]
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
    json_body: Command,

) -> Optional[Command]:
    """Post

     Create a new command instance.
    Resource: commands
    Authorized roles: operator

    Args:
        json_body (Command):

    Returns:
        Response[Command]
    """


    return sync_detailed(
        client=client,
json_body=json_body,

    ).parsed

async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    json_body: Command,

) -> Response[Command]:
    """Post

     Create a new command instance.
    Resource: commands
    Authorized roles: operator

    Args:
        json_body (Command):

    Returns:
        Response[Command]
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
    json_body: Command,

) -> Optional[Command]:
    """Post

     Create a new command instance.
    Resource: commands
    Authorized roles: operator

    Args:
        json_body (Command):

    Returns:
        Response[Command]
    """


    return (await asyncio_detailed(
        client=client,
json_body=json_body,

    )).parsed

