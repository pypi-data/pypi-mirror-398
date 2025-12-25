from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from ...client import AuthenticatedClient
from ...models.group import Group
from ...models.partial_group import PartialGroup
from ...types import Response


def _get_kwargs(
    id: str,
    *,
    client: AuthenticatedClient,
    json_body: PartialGroup,

) -> Dict[str, Any]:
    url = "{}/groups/{id}".format(
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


def _parse_response(*, response: httpx.Response) -> Optional[Group]:
    if response.status_code == 200:
        response_200 = Group.from_dict(response.json())



        return response_200
    return None


def _build_response(*, response: httpx.Response) -> Response[Group]:
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
    json_body: PartialGroup,

) -> Response[Group]:
    """Patch

     Update a group
    Resource: devices
    Authorized roles: administrator

    Args:
        id (str):
        json_body (PartialGroup):

    Returns:
        Response[Group]
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
    json_body: PartialGroup,

) -> Optional[Group]:
    """Patch

     Update a group
    Resource: devices
    Authorized roles: administrator

    Args:
        id (str):
        json_body (PartialGroup):

    Returns:
        Response[Group]
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
    json_body: PartialGroup,

) -> Response[Group]:
    """Patch

     Update a group
    Resource: devices
    Authorized roles: administrator

    Args:
        id (str):
        json_body (PartialGroup):

    Returns:
        Response[Group]
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
    json_body: PartialGroup,

) -> Optional[Group]:
    """Patch

     Update a group
    Resource: devices
    Authorized roles: administrator

    Args:
        id (str):
        json_body (PartialGroup):

    Returns:
        Response[Group]
    """


    return (await asyncio_detailed(
        id=id,
client=client,
json_body=json_body,

    )).parsed

