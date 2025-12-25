from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from ...client import AuthenticatedClient
from ...models.command_template_list_response import \
    CommandTemplateListResponse
from ...types import Response


def _get_kwargs(
    *,
    client: AuthenticatedClient,

) -> Dict[str, Any]:
    url = "{}/command-templates/".format(
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


def _parse_response(*, response: httpx.Response) -> Optional[CommandTemplateListResponse]:
    if response.status_code == HTTPStatus.OK:
        response_200 = CommandTemplateListResponse.from_dict(response.json())



        return response_200
    return None


def _build_response(*, response: httpx.Response) -> Response[CommandTemplateListResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,

) -> Response[CommandTemplateListResponse]:
    """List

     List command templates in your organization.
    Resource: commands
    Authorized roles: viewer

    Returns:
        Response[CommandTemplateListResponse]
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

) -> Optional[CommandTemplateListResponse]:
    """List

     List command templates in your organization.
    Resource: commands
    Authorized roles: viewer

    Returns:
        Response[CommandTemplateListResponse]
    """


    return sync_detailed(
        client=client,

    ).parsed

async def asyncio_detailed(
    *,
    client: AuthenticatedClient,

) -> Response[CommandTemplateListResponse]:
    """List

     List command templates in your organization.
    Resource: commands
    Authorized roles: viewer

    Returns:
        Response[CommandTemplateListResponse]
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

) -> Optional[CommandTemplateListResponse]:
    """List

     List command templates in your organization.
    Resource: commands
    Authorized roles: viewer

    Returns:
        Response[CommandTemplateListResponse]
    """


    return (await asyncio_detailed(
        client=client,

    )).parsed

