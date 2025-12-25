from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from ...client import AuthenticatedClient
from ...models.usage_record_query import UsageRecordQuery
from ...models.usage_record_query_response import UsageRecordQueryResponse
from ...types import Response


def _get_kwargs(
    id: str,
    *,
    client: AuthenticatedClient,
    json_body: UsageRecordQuery,

) -> Dict[str, Any]:
    url = "{}/organizations/{id}/usage-record/query".format(
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


def _parse_response(*, response: httpx.Response) -> Optional[UsageRecordQueryResponse]:
    if response.status_code == 200:
        response_200 = UsageRecordQueryResponse.from_dict(response.json())



        return response_200
    return None


def _build_response(*, response: httpx.Response) -> Response[UsageRecordQueryResponse]:
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
    json_body: UsageRecordQuery,

) -> Response[UsageRecordQueryResponse]:
    """Query usage records

     Query for usage records
    Resource: organization
    Authorized roles: administrator

    Args:
        id (str):
        json_body (UsageRecordQuery):

    Returns:
        Response[UsageRecordQueryResponse]
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
    json_body: UsageRecordQuery,

) -> Optional[UsageRecordQueryResponse]:
    """Query usage records

     Query for usage records
    Resource: organization
    Authorized roles: administrator

    Args:
        id (str):
        json_body (UsageRecordQuery):

    Returns:
        Response[UsageRecordQueryResponse]
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
    json_body: UsageRecordQuery,

) -> Response[UsageRecordQueryResponse]:
    """Query usage records

     Query for usage records
    Resource: organization
    Authorized roles: administrator

    Args:
        id (str):
        json_body (UsageRecordQuery):

    Returns:
        Response[UsageRecordQueryResponse]
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
    json_body: UsageRecordQuery,

) -> Optional[UsageRecordQueryResponse]:
    """Query usage records

     Query for usage records
    Resource: organization
    Authorized roles: administrator

    Args:
        id (str):
        json_body (UsageRecordQuery):

    Returns:
        Response[UsageRecordQueryResponse]
    """


    return (await asyncio_detailed(
        id=id,
client=client,
json_body=json_body,

    )).parsed

