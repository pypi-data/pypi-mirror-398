
from formant.sdk.cloud.v2.src.resources.resources import Resources
from . import EventListResponse, EventQuery, Response, event_controller_query

class Events(Resources):

    def query(self, event_query: EventQuery):
        'Get an event'
        client = self._get_client()
        response: Response[EventListResponse] = event_controller_query.sync_detailed(client=client, json_body=event_query)
        return response

    async def query_async(self, event_query: EventQuery):
        'Get an event'
        client = self._get_client()
        response: Response[EventListResponse] = (await event_controller_query.asyncio_detailed(client=client, json_body=event_query))
        return response
