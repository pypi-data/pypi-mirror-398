from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ...client import AuthenticatedClient
from ...models.event_list_response import EventListResponse
from ...models.event_query import EventQuery
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    client: AuthenticatedClient,
    json_body: EventQuery,
    app_id: Union[Unset, str] = UNSET,

) -> Dict[str, Any]:
    url = "{}/events/query".format(
        client.base_url)

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    if not isinstance(app_id, Unset):
        headers["app-id"] = app_id



    

    

    json_json_body = json_body.to_dict()



    

    return {
	    "method": "post",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
        "json": json_json_body,
    }


def _parse_response(*, response: httpx.Response) -> Optional[EventListResponse]:
    if response.status_code == 200:
        response_200 = EventListResponse.from_dict(response.json())



        return response_200
    return None


def _build_response(*, response: httpx.Response) -> Response[EventListResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    json_body: EventQuery,
    app_id: Union[Unset, str] = UNSET,

) -> Response[EventListResponse]:
    """Query

     Query events
    Resource: events
    Authorized roles: viewer

    Args:
        app_id (Union[Unset, str]):
        json_body (EventQuery):

    Returns:
        Response[EventListResponse]
    """


    kwargs = _get_kwargs(
        client=client,
json_body=json_body,
app_id=app_id,

    )

    response = httpx.request(
        verify=client.verify_ssl,
        **kwargs,
    )

    return _build_response(response=response)

def sync(
    *,
    client: AuthenticatedClient,
    json_body: EventQuery,
    app_id: Union[Unset, str] = UNSET,

) -> Optional[EventListResponse]:
    """Query

     Query events
    Resource: events
    Authorized roles: viewer

    Args:
        app_id (Union[Unset, str]):
        json_body (EventQuery):

    Returns:
        Response[EventListResponse]
    """


    return sync_detailed(
        client=client,
json_body=json_body,
app_id=app_id,

    ).parsed

async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    json_body: EventQuery,
    app_id: Union[Unset, str] = UNSET,

) -> Response[EventListResponse]:
    """Query

     Query events
    Resource: events
    Authorized roles: viewer

    Args:
        app_id (Union[Unset, str]):
        json_body (EventQuery):

    Returns:
        Response[EventListResponse]
    """


    kwargs = _get_kwargs(
        client=client,
json_body=json_body,
app_id=app_id,

    )

    async with httpx.AsyncClient(verify=client.verify_ssl) as _client:
        response = await _client.request(
            **kwargs
        )

    return _build_response(response=response)

async def asyncio(
    *,
    client: AuthenticatedClient,
    json_body: EventQuery,
    app_id: Union[Unset, str] = UNSET,

) -> Optional[EventListResponse]:
    """Query

     Query events
    Resource: events
    Authorized roles: viewer

    Args:
        app_id (Union[Unset, str]):
        json_body (EventQuery):

    Returns:
        Response[EventListResponse]
    """


    return (await asyncio_detailed(
        client=client,
json_body=json_body,
app_id=app_id,

    )).parsed

