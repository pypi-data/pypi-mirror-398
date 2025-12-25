from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ...client import AuthenticatedClient
from ...models.account_list_response import AccountListResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    id: str,
    *,
    client: AuthenticatedClient,
    only_ids: Union[Unset, None, bool] = UNSET,

) -> Dict[str, Any]:
    url = "{}/accounts/{id}/children".format(
        client.base_url,id=id)

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    

    

    params: Dict[str, Any] = {}
    params["onlyIds"] = only_ids



    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}


    

    

    return {
	    "method": "get",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
        "params": params,
    }


def _parse_response(*, response: httpx.Response) -> Optional[AccountListResponse]:
    if response.status_code == HTTPStatus.OK:
        response_200 = AccountListResponse.from_dict(response.json())



        return response_200
    return None


def _build_response(*, response: httpx.Response) -> Response[AccountListResponse]:
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
    only_ids: Union[Unset, None, bool] = UNSET,

) -> Response[AccountListResponse]:
    """Get children

     Get child accounts.
    Resource: organization
    Authorized roles: viewer

    Args:
        id (str):
        only_ids (Union[Unset, None, bool]):

    Returns:
        Response[AccountListResponse]
    """


    kwargs = _get_kwargs(
        id=id,
client=client,
only_ids=only_ids,

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
    only_ids: Union[Unset, None, bool] = UNSET,

) -> Optional[AccountListResponse]:
    """Get children

     Get child accounts.
    Resource: organization
    Authorized roles: viewer

    Args:
        id (str):
        only_ids (Union[Unset, None, bool]):

    Returns:
        Response[AccountListResponse]
    """


    return sync_detailed(
        id=id,
client=client,
only_ids=only_ids,

    ).parsed

async def asyncio_detailed(
    id: str,
    *,
    client: AuthenticatedClient,
    only_ids: Union[Unset, None, bool] = UNSET,

) -> Response[AccountListResponse]:
    """Get children

     Get child accounts.
    Resource: organization
    Authorized roles: viewer

    Args:
        id (str):
        only_ids (Union[Unset, None, bool]):

    Returns:
        Response[AccountListResponse]
    """


    kwargs = _get_kwargs(
        id=id,
client=client,
only_ids=only_ids,

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
    only_ids: Union[Unset, None, bool] = UNSET,

) -> Optional[AccountListResponse]:
    """Get children

     Get child accounts.
    Resource: organization
    Authorized roles: viewer

    Args:
        id (str):
        only_ids (Union[Unset, None, bool]):

    Returns:
        Response[AccountListResponse]
    """


    return (await asyncio_detailed(
        id=id,
client=client,
only_ids=only_ids,

    )).parsed

