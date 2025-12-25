from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ...client import AuthenticatedClient
from ...models.updated_configuration_response import \
    UpdatedConfigurationResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    id: str,
    *,
    client: AuthenticatedClient,
    reported_configuration_version: Union[Unset, None, int] = UNSET,
    agent_wall_clock_timestamp: Union[Unset, None, int] = UNSET,
    app_version: Union[Unset, str] = UNSET,

) -> Dict[str, Any]:
    url = "{}/devices/{id}/updated-configuration".format(
        client.base_url,id=id)

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    if not isinstance(app_version, Unset):
        headers["app-version"] = app_version



    

    params: Dict[str, Any] = {}
    params["reportedConfigurationVersion"] = reported_configuration_version


    params["agentWallClockTimestamp"] = agent_wall_clock_timestamp



    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}


    

    

    return {
	    "method": "get",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
        "params": params,
    }


def _parse_response(*, response: httpx.Response) -> Optional[UpdatedConfigurationResponse]:
    if response.status_code == HTTPStatus.OK:
        response_200 = UpdatedConfigurationResponse.from_dict(response.json())



        return response_200
    return None


def _build_response(*, response: httpx.Response) -> Response[UpdatedConfigurationResponse]:
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
    reported_configuration_version: Union[Unset, None, int] = UNSET,
    agent_wall_clock_timestamp: Union[Unset, None, int] = UNSET,
    app_version: Union[Unset, str] = UNSET,

) -> Response[UpdatedConfigurationResponse]:
    """Get updated configuration

     Check for updated device configuration
    Resource: devices
    Authorized roles: device

    Args:
        id (str):
        reported_configuration_version (Union[Unset, None, int]):
        agent_wall_clock_timestamp (Union[Unset, None, int]):
        app_version (Union[Unset, str]):

    Returns:
        Response[UpdatedConfigurationResponse]
    """


    kwargs = _get_kwargs(
        id=id,
client=client,
reported_configuration_version=reported_configuration_version,
agent_wall_clock_timestamp=agent_wall_clock_timestamp,
app_version=app_version,

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
    reported_configuration_version: Union[Unset, None, int] = UNSET,
    agent_wall_clock_timestamp: Union[Unset, None, int] = UNSET,
    app_version: Union[Unset, str] = UNSET,

) -> Optional[UpdatedConfigurationResponse]:
    """Get updated configuration

     Check for updated device configuration
    Resource: devices
    Authorized roles: device

    Args:
        id (str):
        reported_configuration_version (Union[Unset, None, int]):
        agent_wall_clock_timestamp (Union[Unset, None, int]):
        app_version (Union[Unset, str]):

    Returns:
        Response[UpdatedConfigurationResponse]
    """


    return sync_detailed(
        id=id,
client=client,
reported_configuration_version=reported_configuration_version,
agent_wall_clock_timestamp=agent_wall_clock_timestamp,
app_version=app_version,

    ).parsed

async def asyncio_detailed(
    id: str,
    *,
    client: AuthenticatedClient,
    reported_configuration_version: Union[Unset, None, int] = UNSET,
    agent_wall_clock_timestamp: Union[Unset, None, int] = UNSET,
    app_version: Union[Unset, str] = UNSET,

) -> Response[UpdatedConfigurationResponse]:
    """Get updated configuration

     Check for updated device configuration
    Resource: devices
    Authorized roles: device

    Args:
        id (str):
        reported_configuration_version (Union[Unset, None, int]):
        agent_wall_clock_timestamp (Union[Unset, None, int]):
        app_version (Union[Unset, str]):

    Returns:
        Response[UpdatedConfigurationResponse]
    """


    kwargs = _get_kwargs(
        id=id,
client=client,
reported_configuration_version=reported_configuration_version,
agent_wall_clock_timestamp=agent_wall_clock_timestamp,
app_version=app_version,

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
    reported_configuration_version: Union[Unset, None, int] = UNSET,
    agent_wall_clock_timestamp: Union[Unset, None, int] = UNSET,
    app_version: Union[Unset, str] = UNSET,

) -> Optional[UpdatedConfigurationResponse]:
    """Get updated configuration

     Check for updated device configuration
    Resource: devices
    Authorized roles: device

    Args:
        id (str):
        reported_configuration_version (Union[Unset, None, int]):
        agent_wall_clock_timestamp (Union[Unset, None, int]):
        app_version (Union[Unset, str]):

    Returns:
        Response[UpdatedConfigurationResponse]
    """


    return (await asyncio_detailed(
        id=id,
client=client,
reported_configuration_version=reported_configuration_version,
agent_wall_clock_timestamp=agent_wall_clock_timestamp,
app_version=app_version,

    )).parsed

