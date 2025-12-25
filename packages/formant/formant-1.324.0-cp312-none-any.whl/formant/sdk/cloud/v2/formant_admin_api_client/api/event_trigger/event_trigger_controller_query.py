from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from ...client import AuthenticatedClient
from ...models.updated_event_trigger_request import UpdatedEventTriggerRequest
from ...models.updated_event_trigger_response import \
    UpdatedEventTriggerResponse
from ...types import Response


def _get_kwargs(
    *,
    client: AuthenticatedClient,
    json_body: UpdatedEventTriggerRequest,

) -> Dict[str, Any]:
    url = "{}/event-triggers/updated".format(
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


def _parse_response(*, response: httpx.Response) -> Optional[UpdatedEventTriggerResponse]:
    if response.status_code == 201:
        response_201 = UpdatedEventTriggerResponse.from_dict(response.json())



        return response_201
    return None


def _build_response(*, response: httpx.Response) -> Response[UpdatedEventTriggerResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    json_body: UpdatedEventTriggerRequest,

) -> Response[UpdatedEventTriggerResponse]:
    """Query

     Get updated event trigger configuration
    Resource: events
    Authorized roles: device

    Args:
        json_body (UpdatedEventTriggerRequest):

    Returns:
        Response[UpdatedEventTriggerResponse]
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
    json_body: UpdatedEventTriggerRequest,

) -> Optional[UpdatedEventTriggerResponse]:
    """Query

     Get updated event trigger configuration
    Resource: events
    Authorized roles: device

    Args:
        json_body (UpdatedEventTriggerRequest):

    Returns:
        Response[UpdatedEventTriggerResponse]
    """


    return sync_detailed(
        client=client,
json_body=json_body,

    ).parsed

async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    json_body: UpdatedEventTriggerRequest,

) -> Response[UpdatedEventTriggerResponse]:
    """Query

     Get updated event trigger configuration
    Resource: events
    Authorized roles: device

    Args:
        json_body (UpdatedEventTriggerRequest):

    Returns:
        Response[UpdatedEventTriggerResponse]
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
    json_body: UpdatedEventTriggerRequest,

) -> Optional[UpdatedEventTriggerResponse]:
    """Query

     Get updated event trigger configuration
    Resource: events
    Authorized roles: device

    Args:
        json_body (UpdatedEventTriggerRequest):

    Returns:
        Response[UpdatedEventTriggerResponse]
    """


    return (await asyncio_detailed(
        client=client,
json_body=json_body,

    )).parsed

