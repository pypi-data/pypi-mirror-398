from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from ...client import AuthenticatedClient
from ...models.partial_user import PartialUser
from ...models.user import User
from ...types import Response


def _get_kwargs(
    id: str,
    *,
    client: AuthenticatedClient,
    json_body: PartialUser,

) -> Dict[str, Any]:
    url = "{}/users/{id}".format(
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


def _parse_response(*, response: httpx.Response) -> Optional[User]:
    if response.status_code == 200:
        response_200 = User.from_dict(response.json())



        return response_200
    return None


def _build_response(*, response: httpx.Response) -> Response[User]:
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
    json_body: PartialUser,

) -> Response[User]:
    """Patch

     Update an existing user.
    Resource: users
    Authorized roles: viewer

    Args:
        id (str):
        json_body (PartialUser):

    Returns:
        Response[User]
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
    json_body: PartialUser,

) -> Optional[User]:
    """Patch

     Update an existing user.
    Resource: users
    Authorized roles: viewer

    Args:
        id (str):
        json_body (PartialUser):

    Returns:
        Response[User]
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
    json_body: PartialUser,

) -> Response[User]:
    """Patch

     Update an existing user.
    Resource: users
    Authorized roles: viewer

    Args:
        id (str):
        json_body (PartialUser):

    Returns:
        Response[User]
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
    json_body: PartialUser,

) -> Optional[User]:
    """Patch

     Update an existing user.
    Resource: users
    Authorized roles: viewer

    Args:
        id (str):
        json_body (PartialUser):

    Returns:
        Response[User]
    """


    return (await asyncio_detailed(
        id=id,
client=client,
json_body=json_body,

    )).parsed

