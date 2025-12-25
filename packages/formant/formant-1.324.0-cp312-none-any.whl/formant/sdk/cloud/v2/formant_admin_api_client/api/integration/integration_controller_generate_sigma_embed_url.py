from http import HTTPStatus
from typing import Any, Dict

import httpx

from ...client import AuthenticatedClient
from ...types import UNSET, Response


def _get_kwargs(
    *,
    client: AuthenticatedClient,
    external_user_team: str,
    mode: str,
    session_length: int,
    menu_position: str,
    tag: str,

) -> Dict[str, Any]:
    url = "{}/integrations/generate-sigma-embed-url".format(
        client.base_url)

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    

    

    params: Dict[str, Any] = {}
    params["external_user_team"] = external_user_team


    params["mode"] = mode


    params["session_length"] = session_length


    params["menu_position"] = menu_position


    params["tag"] = tag



    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}


    

    

    return {
	    "method": "get",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
        "params": params,
    }




def _build_response(*, response: httpx.Response) -> Response[Any]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=None,
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    external_user_team: str,
    mode: str,
    session_length: int,
    menu_position: str,
    tag: str,

) -> Response[Any]:
    """Generate sigma embed url

     Generate Sigma embed URL
    Resource: integrations
    Authorized roles: viewer

    Args:
        external_user_team (str):
        mode (str):
        session_length (int):
        menu_position (str):
        tag (str):

    Returns:
        Response[Any]
    """


    kwargs = _get_kwargs(
        client=client,
external_user_team=external_user_team,
mode=mode,
session_length=session_length,
menu_position=menu_position,
tag=tag,

    )

    response = httpx.request(
        verify=client.verify_ssl,
        **kwargs,
    )

    return _build_response(response=response)


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    external_user_team: str,
    mode: str,
    session_length: int,
    menu_position: str,
    tag: str,

) -> Response[Any]:
    """Generate sigma embed url

     Generate Sigma embed URL
    Resource: integrations
    Authorized roles: viewer

    Args:
        external_user_team (str):
        mode (str):
        session_length (int):
        menu_position (str):
        tag (str):

    Returns:
        Response[Any]
    """


    kwargs = _get_kwargs(
        client=client,
external_user_team=external_user_team,
mode=mode,
session_length=session_length,
menu_position=menu_position,
tag=tag,

    )

    async with httpx.AsyncClient(verify=client.verify_ssl) as _client:
        response = await _client.request(
            **kwargs
        )

    return _build_response(response=response)


