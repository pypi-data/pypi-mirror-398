from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ...client import AuthenticatedClient
from ...models.intervention_request_controller_list_order import \
    InterventionRequestControllerListOrder
from ...models.intervention_request_list_response import \
    InterventionRequestListResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    client: AuthenticatedClient,
    page: Union[Unset, None, Any] = UNSET,
    limit: Union[Unset, None, int] = UNSET,
    order: Union[Unset, None, InterventionRequestControllerListOrder] = UNSET,

) -> Dict[str, Any]:
    url = "{}/intervention-requests/".format(
        client.base_url)

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    

    

    params: Dict[str, Any] = {}
    params["page"] = page


    params["limit"] = limit


    json_order: Union[Unset, None, str] = UNSET
    if not isinstance(order, Unset):
        json_order = order.value if order else None

    params["order"] = json_order



    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}


    

    

    return {
	    "method": "get",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
        "params": params,
    }


def _parse_response(*, response: httpx.Response) -> Optional[InterventionRequestListResponse]:
    if response.status_code == HTTPStatus.OK:
        response_200 = InterventionRequestListResponse.from_dict(response.json())



        return response_200
    return None


def _build_response(*, response: httpx.Response) -> Response[InterventionRequestListResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    page: Union[Unset, None, Any] = UNSET,
    limit: Union[Unset, None, int] = UNSET,
    order: Union[Unset, None, InterventionRequestControllerListOrder] = UNSET,

) -> Response[InterventionRequestListResponse]:
    """List

     List all intervention requests in your organization.
    Resource: interventions
    Authorized roles: viewer

    Args:
        page (Union[Unset, None, Any]):
        limit (Union[Unset, None, int]):
        order (Union[Unset, None, InterventionRequestControllerListOrder]):

    Returns:
        Response[InterventionRequestListResponse]
    """


    kwargs = _get_kwargs(
        client=client,
page=page,
limit=limit,
order=order,

    )

    response = httpx.request(
        verify=client.verify_ssl,
        **kwargs,
    )

    return _build_response(response=response)

def sync(
    *,
    client: AuthenticatedClient,
    page: Union[Unset, None, Any] = UNSET,
    limit: Union[Unset, None, int] = UNSET,
    order: Union[Unset, None, InterventionRequestControllerListOrder] = UNSET,

) -> Optional[InterventionRequestListResponse]:
    """List

     List all intervention requests in your organization.
    Resource: interventions
    Authorized roles: viewer

    Args:
        page (Union[Unset, None, Any]):
        limit (Union[Unset, None, int]):
        order (Union[Unset, None, InterventionRequestControllerListOrder]):

    Returns:
        Response[InterventionRequestListResponse]
    """


    return sync_detailed(
        client=client,
page=page,
limit=limit,
order=order,

    ).parsed

async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    page: Union[Unset, None, Any] = UNSET,
    limit: Union[Unset, None, int] = UNSET,
    order: Union[Unset, None, InterventionRequestControllerListOrder] = UNSET,

) -> Response[InterventionRequestListResponse]:
    """List

     List all intervention requests in your organization.
    Resource: interventions
    Authorized roles: viewer

    Args:
        page (Union[Unset, None, Any]):
        limit (Union[Unset, None, int]):
        order (Union[Unset, None, InterventionRequestControllerListOrder]):

    Returns:
        Response[InterventionRequestListResponse]
    """


    kwargs = _get_kwargs(
        client=client,
page=page,
limit=limit,
order=order,

    )

    async with httpx.AsyncClient(verify=client.verify_ssl) as _client:
        response = await _client.request(
            **kwargs
        )

    return _build_response(response=response)

async def asyncio(
    *,
    client: AuthenticatedClient,
    page: Union[Unset, None, Any] = UNSET,
    limit: Union[Unset, None, int] = UNSET,
    order: Union[Unset, None, InterventionRequestControllerListOrder] = UNSET,

) -> Optional[InterventionRequestListResponse]:
    """List

     List all intervention requests in your organization.
    Resource: interventions
    Authorized roles: viewer

    Args:
        page (Union[Unset, None, Any]):
        limit (Union[Unset, None, int]):
        order (Union[Unset, None, InterventionRequestControllerListOrder]):

    Returns:
        Response[InterventionRequestListResponse]
    """


    return (await asyncio_detailed(
        client=client,
page=page,
limit=limit,
order=order,

    )).parsed

