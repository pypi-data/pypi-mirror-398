from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from ...client import AuthenticatedClient
from ...models.get_features_response import GetFeaturesResponse
from ...types import Response


def _get_kwargs(
    *,
    client: AuthenticatedClient,

) -> Dict[str, Any]:
    url = "{}/auth/features".format(
        client.base_url)

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    

    

    

    

    

    return {
	    "method": "get",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
    }


def _parse_response(*, response: httpx.Response) -> Optional[GetFeaturesResponse]:
    if response.status_code == 200:
        response_200 = GetFeaturesResponse.from_dict(response.json())



        return response_200
    return None


def _build_response(*, response: httpx.Response) -> Response[GetFeaturesResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,

) -> Response[GetFeaturesResponse]:
    """Get features

     Get enabled features
    Resource: devices
    Authorized roles: viewer, device

    Returns:
        Response[GetFeaturesResponse]
    """


    kwargs = _get_kwargs(
        client=client,

    )

    response = httpx.request(
        verify=client.verify_ssl,
        **kwargs,
    )

    return _build_response(response=response)

def sync(
    *,
    client: AuthenticatedClient,

) -> Optional[GetFeaturesResponse]:
    """Get features

     Get enabled features
    Resource: devices
    Authorized roles: viewer, device

    Returns:
        Response[GetFeaturesResponse]
    """


    return sync_detailed(
        client=client,

    ).parsed

async def asyncio_detailed(
    *,
    client: AuthenticatedClient,

) -> Response[GetFeaturesResponse]:
    """Get features

     Get enabled features
    Resource: devices
    Authorized roles: viewer, device

    Returns:
        Response[GetFeaturesResponse]
    """


    kwargs = _get_kwargs(
        client=client,

    )

    async with httpx.AsyncClient(verify=client.verify_ssl) as _client:
        response = await _client.request(
            **kwargs
        )

    return _build_response(response=response)

async def asyncio(
    *,
    client: AuthenticatedClient,

) -> Optional[GetFeaturesResponse]:
    """Get features

     Get enabled features
    Resource: devices
    Authorized roles: viewer, device

    Returns:
        Response[GetFeaturesResponse]
    """


    return (await asyncio_detailed(
        client=client,

    )).parsed

