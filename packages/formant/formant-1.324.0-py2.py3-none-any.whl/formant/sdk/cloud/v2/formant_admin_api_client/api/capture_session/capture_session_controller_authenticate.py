from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ...client import Client
from ...models.authenticate_capture_code_response import \
    AuthenticateCaptureCodeResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    code: str,
    *,
    client: Client,
    include_capture_session: Union[Unset, None, bool] = UNSET,
    include_scope: Union[Unset, None, bool] = UNSET,

) -> Dict[str, Any]:
    url = "{}/capture-sessions/{code}/authenticate".format(
        client.base_url,code=code)

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    

    

    params: Dict[str, Any] = {}
    params["includeCaptureSession"] = include_capture_session


    params["includeScope"] = include_scope



    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}


    

    

    return {
	    "method": "post",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
        "params": params,
    }


def _parse_response(*, response: httpx.Response) -> Optional[AuthenticateCaptureCodeResponse]:
    if response.status_code == HTTPStatus.OK:
        response_200 = AuthenticateCaptureCodeResponse.from_dict(response.json())



        return response_200
    return None


def _build_response(*, response: httpx.Response) -> Response[AuthenticateCaptureCodeResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(response=response),
    )


def sync_detailed(
    code: str,
    *,
    client: Client,
    include_capture_session: Union[Unset, None, bool] = UNSET,
    include_scope: Union[Unset, None, bool] = UNSET,

) -> Response[AuthenticateCaptureCodeResponse]:
    """Authenticate

    Args:
        code (str):
        include_capture_session (Union[Unset, None, bool]):
        include_scope (Union[Unset, None, bool]):

    Returns:
        Response[AuthenticateCaptureCodeResponse]
    """


    kwargs = _get_kwargs(
        code=code,
client=client,
include_capture_session=include_capture_session,
include_scope=include_scope,

    )

    response = httpx.request(
        verify=client.verify_ssl,
        **kwargs,
    )

    return _build_response(response=response)

def sync(
    code: str,
    *,
    client: Client,
    include_capture_session: Union[Unset, None, bool] = UNSET,
    include_scope: Union[Unset, None, bool] = UNSET,

) -> Optional[AuthenticateCaptureCodeResponse]:
    """Authenticate

    Args:
        code (str):
        include_capture_session (Union[Unset, None, bool]):
        include_scope (Union[Unset, None, bool]):

    Returns:
        Response[AuthenticateCaptureCodeResponse]
    """


    return sync_detailed(
        code=code,
client=client,
include_capture_session=include_capture_session,
include_scope=include_scope,

    ).parsed

async def asyncio_detailed(
    code: str,
    *,
    client: Client,
    include_capture_session: Union[Unset, None, bool] = UNSET,
    include_scope: Union[Unset, None, bool] = UNSET,

) -> Response[AuthenticateCaptureCodeResponse]:
    """Authenticate

    Args:
        code (str):
        include_capture_session (Union[Unset, None, bool]):
        include_scope (Union[Unset, None, bool]):

    Returns:
        Response[AuthenticateCaptureCodeResponse]
    """


    kwargs = _get_kwargs(
        code=code,
client=client,
include_capture_session=include_capture_session,
include_scope=include_scope,

    )

    async with httpx.AsyncClient(verify=client.verify_ssl) as _client:
        response = await _client.request(
            **kwargs
        )

    return _build_response(response=response)

async def asyncio(
    code: str,
    *,
    client: Client,
    include_capture_session: Union[Unset, None, bool] = UNSET,
    include_scope: Union[Unset, None, bool] = UNSET,

) -> Optional[AuthenticateCaptureCodeResponse]:
    """Authenticate

    Args:
        code (str):
        include_capture_session (Union[Unset, None, bool]):
        include_scope (Union[Unset, None, bool]):

    Returns:
        Response[AuthenticateCaptureCodeResponse]
    """


    return (await asyncio_detailed(
        code=code,
client=client,
include_capture_session=include_capture_session,
include_scope=include_scope,

    )).parsed

