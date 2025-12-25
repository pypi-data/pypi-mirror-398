from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from ...client import AuthenticatedClient
from ...models.google_auth_request import GoogleAuthRequest
from ...models.google_info import GoogleInfo
from ...types import Response


def _get_kwargs(
    *,
    client: AuthenticatedClient,
    json_body: GoogleAuthRequest,

) -> Dict[str, Any]:
    url = "{}/integrations/google/auth".format(
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


def _parse_response(*, response: httpx.Response) -> Optional[GoogleInfo]:
    if response.status_code == HTTPStatus.OK:
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
    *,
    client: AuthenticatedClient,
    json_body: GoogleAuthRequest,

) -> Response[GoogleInfo]:
    """Google

     Create a Google integration
    Resource: integrations
    Authorized roles: administrator

    Args:
        json_body (GoogleAuthRequest):

    Returns:
        Response[GoogleInfo]
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
    json_body: GoogleAuthRequest,

) -> Optional[GoogleInfo]:
    """Google

     Create a Google integration
    Resource: integrations
    Authorized roles: administrator

    Args:
        json_body (GoogleAuthRequest):

    Returns:
        Response[GoogleInfo]
    """


    return sync_detailed(
        client=client,
json_body=json_body,

    ).parsed

async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    json_body: GoogleAuthRequest,

) -> Response[GoogleInfo]:
    """Google

     Create a Google integration
    Resource: integrations
    Authorized roles: administrator

    Args:
        json_body (GoogleAuthRequest):

    Returns:
        Response[GoogleInfo]
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
    json_body: GoogleAuthRequest,

) -> Optional[GoogleInfo]:
    """Google

     Create a Google integration
    Resource: integrations
    Authorized roles: administrator

    Args:
        json_body (GoogleAuthRequest):

    Returns:
        Response[GoogleInfo]
    """


    return (await asyncio_detailed(
        client=client,
json_body=json_body,

    )).parsed

