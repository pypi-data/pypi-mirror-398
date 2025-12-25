from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from ...client import AuthenticatedClient
from ...models.sso_configuration_list_response import \
    SsoConfigurationListResponse
from ...types import Response


def _get_kwargs(
    *,
    client: AuthenticatedClient,

) -> Dict[str, Any]:
    url = "{}/sso-configuration".format(
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


def _parse_response(*, response: httpx.Response) -> Optional[SsoConfigurationListResponse]:
    if response.status_code == HTTPStatus.OK:
        response_200 = SsoConfigurationListResponse.from_dict(response.json())



        return response_200
    return None


def _build_response(*, response: httpx.Response) -> Response[SsoConfigurationListResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,

) -> Response[SsoConfigurationListResponse]:
    """List

     List all SSO configurations for the organization
    Resource: organization
    Authorized roles: administrator

    Returns:
        Response[SsoConfigurationListResponse]
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

) -> Optional[SsoConfigurationListResponse]:
    """List

     List all SSO configurations for the organization
    Resource: organization
    Authorized roles: administrator

    Returns:
        Response[SsoConfigurationListResponse]
    """


    return sync_detailed(
        client=client,

    ).parsed

async def asyncio_detailed(
    *,
    client: AuthenticatedClient,

) -> Response[SsoConfigurationListResponse]:
    """List

     List all SSO configurations for the organization
    Resource: organization
    Authorized roles: administrator

    Returns:
        Response[SsoConfigurationListResponse]
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

) -> Optional[SsoConfigurationListResponse]:
    """List

     List all SSO configurations for the organization
    Resource: organization
    Authorized roles: administrator

    Returns:
        Response[SsoConfigurationListResponse]
    """


    return (await asyncio_detailed(
        client=client,

    )).parsed

