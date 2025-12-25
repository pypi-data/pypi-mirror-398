from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from ...client import AuthenticatedClient
from ...models.task_summary import TaskSummary
from ...types import Response


def _get_kwargs(
    *,
    client: AuthenticatedClient,
    json_body: TaskSummary,

) -> Dict[str, Any]:
    url = "{}/task-summaries/".format(
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


def _parse_response(*, response: httpx.Response) -> Optional[TaskSummary]:
    if response.status_code == 201:
        response_201 = TaskSummary.from_dict(response.json())



        return response_201
    return None


def _build_response(*, response: httpx.Response) -> Response[TaskSummary]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    json_body: TaskSummary,

) -> Response[TaskSummary]:
    """Post

     Create a new task summary. Before you can create a task summary, you must first create a task
    summary format.
    Resource: taskSummaries
    Authorized roles: operator, device

    Args:
        json_body (TaskSummary):

    Returns:
        Response[TaskSummary]
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
    json_body: TaskSummary,

) -> Optional[TaskSummary]:
    """Post

     Create a new task summary. Before you can create a task summary, you must first create a task
    summary format.
    Resource: taskSummaries
    Authorized roles: operator, device

    Args:
        json_body (TaskSummary):

    Returns:
        Response[TaskSummary]
    """


    return sync_detailed(
        client=client,
json_body=json_body,

    ).parsed

async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    json_body: TaskSummary,

) -> Response[TaskSummary]:
    """Post

     Create a new task summary. Before you can create a task summary, you must first create a task
    summary format.
    Resource: taskSummaries
    Authorized roles: operator, device

    Args:
        json_body (TaskSummary):

    Returns:
        Response[TaskSummary]
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
    json_body: TaskSummary,

) -> Optional[TaskSummary]:
    """Post

     Create a new task summary. Before you can create a task summary, you must first create a task
    summary format.
    Resource: taskSummaries
    Authorized roles: operator, device

    Args:
        json_body (TaskSummary):

    Returns:
        Response[TaskSummary]
    """


    return (await asyncio_detailed(
        client=client,
json_body=json_body,

    )).parsed

