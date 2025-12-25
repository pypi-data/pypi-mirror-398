from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from ...client import AuthenticatedClient
from ...models.event_trigger_group import EventTriggerGroup
from ...types import Response


def _get_kwargs(
    id: str,
    *,
    client: AuthenticatedClient,

) -> Dict[str, Any]:
    url = "{}/event-trigger-groups/{id}".format(
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


def _parse_response(*, response: httpx.Response) -> Optional[EventTriggerGroup]:
    if response.status_code == HTTPStatus.OK:
        response_200 = EventTriggerGroup.from_dict(response.json())



        return response_200
    return None


def _build_response(*, response: httpx.Response) -> Response[EventTriggerGroup]:
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

) -> Response[EventTriggerGroup]:
    """Get one

     Get an event trigger group
    Resource: events
    Authorized roles: viewer, device

    Args:
        id (str):

    Returns:
        Response[EventTriggerGroup]
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

) -> Optional[EventTriggerGroup]:
    """Get one

     Get an event trigger group
    Resource: events
    Authorized roles: viewer, device

    Args:
        id (str):

    Returns:
        Response[EventTriggerGroup]
    """


    return sync_detailed(
        id=id,
client=client,

    ).parsed

async def asyncio_detailed(
    id: str,
    *,
    client: AuthenticatedClient,

) -> Response[EventTriggerGroup]:
    """Get one

     Get an event trigger group
    Resource: events
    Authorized roles: viewer, device

    Args:
        id (str):

    Returns:
        Response[EventTriggerGroup]
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

) -> Optional[EventTriggerGroup]:
    """Get one

     Get an event trigger group
    Resource: events
    Authorized roles: viewer, device

    Args:
        id (str):

    Returns:
        Response[EventTriggerGroup]
    """


    return (await asyncio_detailed(
        id=id,
client=client,

    )).parsed

