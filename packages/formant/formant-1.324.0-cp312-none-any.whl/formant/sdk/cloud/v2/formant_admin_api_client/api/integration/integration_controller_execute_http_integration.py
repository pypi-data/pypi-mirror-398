from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from ...client import AuthenticatedClient
from ...models.google_info import GoogleInfo
from ...types import Response


def _get_kwargs(
    id: str,
    *,
    client: AuthenticatedClient,
    json_body: Any,

) -> Dict[str, Any]:
    url = "{}/integrations/http/execute/{id}".format(
        client.base_url,id=id)

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    

    

    

    json_json_body = json_body


    

    return {
	    "method": "post",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
        "json": json_json_body,
    }


def _parse_response(*, response: httpx.Response) -> Optional[GoogleInfo]:
    if response.status_code == 200:
        response_200 = GoogleInfo.from_dict(response.json())



        return response_200
    return None


def _build_response(*, response: httpx.Response) -> Response[GoogleInfo]:
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
    json_body: Any,

) -> Response[GoogleInfo]:
    """Execute http integration

     Execute POST HTTP integration
    Resource: streams
    Authorized roles: viewer

    Args:
        id (str):
        json_body (Any):

    Returns:
        Response[GoogleInfo]
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
    json_body: Any,

) -> Optional[GoogleInfo]:
    """Execute http integration

     Execute POST HTTP integration
    Resource: streams
    Authorized roles: viewer

    Args:
        id (str):
        json_body (Any):

    Returns:
        Response[GoogleInfo]
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
    json_body: Any,

) -> Response[GoogleInfo]:
    """Execute http integration

     Execute POST HTTP integration
    Resource: streams
    Authorized roles: viewer

    Args:
        id (str):
        json_body (Any):

    Returns:
        Response[GoogleInfo]
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
    json_body: Any,

) -> Optional[GoogleInfo]:
    """Execute http integration

     Execute POST HTTP integration
    Resource: streams
    Authorized roles: viewer

    Args:
        id (str):
        json_body (Any):

    Returns:
        Response[GoogleInfo]
    """


    return (await asyncio_detailed(
        id=id,
client=client,
json_body=json_body,

    )).parsed

