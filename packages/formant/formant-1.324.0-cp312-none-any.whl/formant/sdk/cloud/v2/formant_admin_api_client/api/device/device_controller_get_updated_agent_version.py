from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ...client import AuthenticatedClient
from ...models.updated_agent_version_response import \
    UpdatedAgentVersionResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    id: str,
    *,
    client: AuthenticatedClient,
    reported_agent_version: Union[Unset, None, str] = UNSET,

) -> Dict[str, Any]:
    url = "{}/devices/{id}/updated-agent-version".format(
        client.base_url,id=id)

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    

    

    params: Dict[str, Any] = {}
    params["reportedAgentVersion"] = reported_agent_version



    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}


    

    

    return {
	    "method": "get",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
        "params": params,
    }


def _parse_response(*, response: httpx.Response) -> Optional[UpdatedAgentVersionResponse]:
    if response.status_code == 200:
        response_200 = UpdatedAgentVersionResponse.from_dict(response.json())



        return response_200
    return None


def _build_response(*, response: httpx.Response) -> Response[UpdatedAgentVersionResponse]:
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
    reported_agent_version: Union[Unset, None, str] = UNSET,

) -> Response[UpdatedAgentVersionResponse]:
    """Get updated agent version

     Check for agent version updates
    Resource: devices
    Authorized roles: device

    Args:
        id (str):
        reported_agent_version (Union[Unset, None, str]):

    Returns:
        Response[UpdatedAgentVersionResponse]
    """


    kwargs = _get_kwargs(
        id=id,
client=client,
reported_agent_version=reported_agent_version,

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
    reported_agent_version: Union[Unset, None, str] = UNSET,

) -> Optional[UpdatedAgentVersionResponse]:
    """Get updated agent version

     Check for agent version updates
    Resource: devices
    Authorized roles: device

    Args:
        id (str):
        reported_agent_version (Union[Unset, None, str]):

    Returns:
        Response[UpdatedAgentVersionResponse]
    """


    return sync_detailed(
        id=id,
client=client,
reported_agent_version=reported_agent_version,

    ).parsed

async def asyncio_detailed(
    id: str,
    *,
    client: AuthenticatedClient,
    reported_agent_version: Union[Unset, None, str] = UNSET,

) -> Response[UpdatedAgentVersionResponse]:
    """Get updated agent version

     Check for agent version updates
    Resource: devices
    Authorized roles: device

    Args:
        id (str):
        reported_agent_version (Union[Unset, None, str]):

    Returns:
        Response[UpdatedAgentVersionResponse]
    """


    kwargs = _get_kwargs(
        id=id,
client=client,
reported_agent_version=reported_agent_version,

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
    reported_agent_version: Union[Unset, None, str] = UNSET,

) -> Optional[UpdatedAgentVersionResponse]:
    """Get updated agent version

     Check for agent version updates
    Resource: devices
    Authorized roles: device

    Args:
        id (str):
        reported_agent_version (Union[Unset, None, str]):

    Returns:
        Response[UpdatedAgentVersionResponse]
    """


    return (await asyncio_detailed(
        id=id,
client=client,
reported_agent_version=reported_agent_version,

    )).parsed

