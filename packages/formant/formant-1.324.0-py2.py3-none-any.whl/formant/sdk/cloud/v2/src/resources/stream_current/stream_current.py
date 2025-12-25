
from formant.sdk.cloud.v2.src.resources.resources import Resources
from . import Response, ScopeFilter, StreamCurrentValueListResponse, stream_current_value_controller_query

class StreamCurrent(Resources):

    def query(self, scope_filter: ScopeFilter):
        'Gets you the current value of  a stream that has been configured to cache the current value'
        client = self._get_client()
        response: Response[StreamCurrentValueListResponse] = stream_current_value_controller_query.sync_detailed(client=client, json_body=scope_filter)
        return response

    async def query_async(self, scope_filter: ScopeFilter):
        'Gets you the current value of  a stream that has been configured to cache the current value'
        client = self._get_client()
        response: Response[StreamCurrentValueListResponse] = (await stream_current_value_controller_query.asyncio_detailed(client=client, json_body=scope_filter))
        return response
