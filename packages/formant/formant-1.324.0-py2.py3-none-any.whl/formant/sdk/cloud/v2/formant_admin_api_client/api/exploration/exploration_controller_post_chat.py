from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from ...client import AuthenticatedClient
from ...models.chat_message_list_response import ChatMessageListResponse
from ...models.chat_message_request import ChatMessageRequest
from ...types import Response


def _get_kwargs(
    id: str,
    *,
    client: AuthenticatedClient,
    json_body: ChatMessageRequest,

) -> Dict[str, Any]:
    url = "{}/exploration/{id}/chat".format(
        client.base_url,id=id)

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


def _parse_response(*, response: httpx.Response) -> Optional[ChatMessageListResponse]:
    if response.status_code == HTTPStatus.CREATED:
        response_201 = ChatMessageListResponse.from_dict(response.json())



        return response_201
    return None


def _build_response(*, response: httpx.Response) -> Response[ChatMessageListResponse]:
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
    json_body: ChatMessageRequest,

) -> Response[ChatMessageListResponse]:
    """Post chat

     Create a chat message
    Resource: commands
    Authorized roles: viewer

    Args:
        id (str):
        json_body (ChatMessageRequest):

    Returns:
        Response[ChatMessageListResponse]
    """


    kwargs = _get_kwargs(
        id=id,
client=client,
json_body=json_body,

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
    json_body: ChatMessageRequest,

) -> Optional[ChatMessageListResponse]:
    """Post chat

     Create a chat message
    Resource: commands
    Authorized roles: viewer

    Args:
        id (str):
        json_body (ChatMessageRequest):

    Returns:
        Response[ChatMessageListResponse]
    """


    return sync_detailed(
        id=id,
client=client,
json_body=json_body,

    ).parsed

async def asyncio_detailed(
    id: str,
    *,
    client: AuthenticatedClient,
    json_body: ChatMessageRequest,

) -> Response[ChatMessageListResponse]:
    """Post chat

     Create a chat message
    Resource: commands
    Authorized roles: viewer

    Args:
        id (str):
        json_body (ChatMessageRequest):

    Returns:
        Response[ChatMessageListResponse]
    """


    kwargs = _get_kwargs(
        id=id,
client=client,
json_body=json_body,

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
    json_body: ChatMessageRequest,

) -> Optional[ChatMessageListResponse]:
    """Post chat

     Create a chat message
    Resource: commands
    Authorized roles: viewer

    Args:
        id (str):
        json_body (ChatMessageRequest):

    Returns:
        Response[ChatMessageListResponse]
    """


    return (await asyncio_detailed(
        id=id,
client=client,
json_body=json_body,

    )).parsed

