from http import HTTPStatus
from typing import Any, Dict, List, Optional

import httpx

from ...client import AuthenticatedClient
from ...models.http_integration import HttpIntegration
from ...types import Response


def _get_kwargs(
    *,
    client: AuthenticatedClient,

) -> Dict[str, Any]:
    url = "{}/integrations/http/".format(
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


def _parse_response(*, response: httpx.Response) -> Optional[List['HttpIntegration']]:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in (_response_200):
            response_200_item = HttpIntegration.from_dict(response_200_item_data)



            response_200.append(response_200_item)

        return response_200
    return None


def _build_response(*, response: httpx.Response) -> Response[List['HttpIntegration']]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,

) -> Response[List['HttpIntegration']]:
    """Get http integrations

     Get HTTP integrations
    Resource: integrations
    Authorized roles: administrator

    Returns:
        Response[List['HttpIntegration']]
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

) -> Optional[List['HttpIntegration']]:
    """Get http integrations

     Get HTTP integrations
    Resource: integrations
    Authorized roles: administrator

    Returns:
        Response[List['HttpIntegration']]
    """


    return sync_detailed(
        client=client,

    ).parsed

async def asyncio_detailed(
    *,
    client: AuthenticatedClient,

) -> Response[List['HttpIntegration']]:
    """Get http integrations

     Get HTTP integrations
    Resource: integrations
    Authorized roles: administrator

    Returns:
        Response[List['HttpIntegration']]
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

) -> Optional[List['HttpIntegration']]:
    """Get http integrations

     Get HTTP integrations
    Resource: integrations
    Authorized roles: administrator

    Returns:
        Response[List['HttpIntegration']]
    """


    return (await asyncio_detailed(
        client=client,

    )).parsed

