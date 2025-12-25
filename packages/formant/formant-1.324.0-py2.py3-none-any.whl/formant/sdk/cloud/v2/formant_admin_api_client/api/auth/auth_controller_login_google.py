from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from ...client import Client
from ...models.google_login_request import GoogleLoginRequest
from ...models.login_result import LoginResult
from ...types import Response


def _get_kwargs(
    *,
    client: Client,
    json_body: GoogleLoginRequest,

) -> Dict[str, Any]:
    url = "{}/auth/login-google".format(
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


def _parse_response(*, response: httpx.Response) -> Optional[LoginResult]:
    if response.status_code == HTTPStatus.OK:
        response_200 = LoginResult.from_dict(response.json())



        return response_200
    return None


def _build_response(*, response: httpx.Response) -> Response[LoginResult]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(response=response),
    )


def sync_detailed(
    *,
    client: Client,
    json_body: GoogleLoginRequest,

) -> Response[LoginResult]:
    """Login google

     Log in with a Google token.

    Args:
        json_body (GoogleLoginRequest):

    Returns:
        Response[LoginResult]
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
    client: Client,
    json_body: GoogleLoginRequest,

) -> Optional[LoginResult]:
    """Login google

     Log in with a Google token.

    Args:
        json_body (GoogleLoginRequest):

    Returns:
        Response[LoginResult]
    """


    return sync_detailed(
        client=client,
json_body=json_body,

    ).parsed

async def asyncio_detailed(
    *,
    client: Client,
    json_body: GoogleLoginRequest,

) -> Response[LoginResult]:
    """Login google

     Log in with a Google token.

    Args:
        json_body (GoogleLoginRequest):

    Returns:
        Response[LoginResult]
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
    client: Client,
    json_body: GoogleLoginRequest,

) -> Optional[LoginResult]:
    """Login google

     Log in with a Google token.

    Args:
        json_body (GoogleLoginRequest):

    Returns:
        Response[LoginResult]
    """


    return (await asyncio_detailed(
        client=client,
json_body=json_body,

    )).parsed

