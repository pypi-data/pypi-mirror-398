from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from ...client import AuthenticatedClient
from ...models.cloud_file import CloudFile
from ...types import Response


def _get_kwargs(
    id: str,
    *,
    client: AuthenticatedClient,

) -> Dict[str, Any]:
    url = "{}/files/{id}".format(
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


def _parse_response(*, response: httpx.Response) -> Optional[CloudFile]:
    if response.status_code == 200:
        response_200 = CloudFile.from_dict(response.json())



        return response_200
    return None


def _build_response(*, response: httpx.Response) -> Response[CloudFile]:
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

) -> Response[CloudFile]:
    """Get

     Get a file by file ID.
    Resource: fileStorage
    Authorized roles: administrator

    Args:
        id (str):

    Returns:
        Response[CloudFile]
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

) -> Optional[CloudFile]:
    """Get

     Get a file by file ID.
    Resource: fileStorage
    Authorized roles: administrator

    Args:
        id (str):

    Returns:
        Response[CloudFile]
    """


    return sync_detailed(
        id=id,
client=client,

    ).parsed

async def asyncio_detailed(
    id: str,
    *,
    client: AuthenticatedClient,

) -> Response[CloudFile]:
    """Get

     Get a file by file ID.
    Resource: fileStorage
    Authorized roles: administrator

    Args:
        id (str):

    Returns:
        Response[CloudFile]
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

) -> Optional[CloudFile]:
    """Get

     Get a file by file ID.
    Resource: fileStorage
    Authorized roles: administrator

    Args:
        id (str):

    Returns:
        Response[CloudFile]
    """


    return (await asyncio_detailed(
        id=id,
client=client,

    )).parsed

