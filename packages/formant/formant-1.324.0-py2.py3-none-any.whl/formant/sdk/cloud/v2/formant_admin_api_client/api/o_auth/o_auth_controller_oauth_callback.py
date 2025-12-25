from http import HTTPStatus
from typing import Any, Dict, Union

import httpx

from ...client import Client
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    client: Client,
    state: Union[Unset, None, str] = UNSET,
    code: Union[Unset, None, str] = UNSET,
    error: Union[Unset, None, str] = UNSET,
    scope: Union[Unset, None, str] = UNSET,
    error_description: Union[Unset, None, str] = UNSET,
    code_challenge_method: Union[Unset, None, str] = UNSET,

) -> Dict[str, Any]:
    url = "{}/oauth/callback".format(
        client.base_url)

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    

    

    params: Dict[str, Any] = {}
    params["state"] = state


    params["code"] = code


    params["error"] = error


    params["scope"] = scope


    params["error_description"] = error_description


    params["code_challenge_method"] = code_challenge_method



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
    client: Client,
    state: Union[Unset, None, str] = UNSET,
    code: Union[Unset, None, str] = UNSET,
    error: Union[Unset, None, str] = UNSET,
    scope: Union[Unset, None, str] = UNSET,
    error_description: Union[Unset, None, str] = UNSET,
    code_challenge_method: Union[Unset, None, str] = UNSET,

) -> Response[Any]:
    """Oauth callback

     Callback for OAuth authentication.

    Args:
        state (Union[Unset, None, str]):
        code (Union[Unset, None, str]):
        error (Union[Unset, None, str]):
        scope (Union[Unset, None, str]):
        error_description (Union[Unset, None, str]):
        code_challenge_method (Union[Unset, None, str]):

    Returns:
        Response[Any]
    """


    kwargs = _get_kwargs(
        client=client,
state=state,
code=code,
error=error,
scope=scope,
error_description=error_description,
code_challenge_method=code_challenge_method,

    )

    response = httpx.request(
        verify=client.verify_ssl,
        **kwargs,
    )

    return _build_response(response=response)


async def asyncio_detailed(
    *,
    client: Client,
    state: Union[Unset, None, str] = UNSET,
    code: Union[Unset, None, str] = UNSET,
    error: Union[Unset, None, str] = UNSET,
    scope: Union[Unset, None, str] = UNSET,
    error_description: Union[Unset, None, str] = UNSET,
    code_challenge_method: Union[Unset, None, str] = UNSET,

) -> Response[Any]:
    """Oauth callback

     Callback for OAuth authentication.

    Args:
        state (Union[Unset, None, str]):
        code (Union[Unset, None, str]):
        error (Union[Unset, None, str]):
        scope (Union[Unset, None, str]):
        error_description (Union[Unset, None, str]):
        code_challenge_method (Union[Unset, None, str]):

    Returns:
        Response[Any]
    """


    kwargs = _get_kwargs(
        client=client,
state=state,
code=code,
error=error,
scope=scope,
error_description=error_description,
code_challenge_method=code_challenge_method,

    )

    async with httpx.AsyncClient(verify=client.verify_ssl) as _client:
        response = await _client.request(
            **kwargs
        )

    return _build_response(response=response)


