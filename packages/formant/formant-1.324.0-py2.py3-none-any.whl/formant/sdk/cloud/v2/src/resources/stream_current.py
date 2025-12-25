
from formant.sdk.cloud.v2.formant_query_api_client.api.stream_current_value import stream_current_value_controller_query
from formant.sdk.cloud.v2.formant_query_api_client.models.scope_filter import ScopeFilter
from formant.sdk.cloud.v2.src.resources.resources import Resources

class StreamCurrent(Resources):

    def query(self, scope_filter: ScopeFilter):
        'Gets you the current value of  a stream that has been configured to cache the current value'
        client = self._get_client()
        response = stream_current_value_controller_query.sync_detailed(client=client, json_body=scope_filter)
        return response

    async def query_async(self, scope_filter: ScopeFilter):
        'Gets you the current value of  a stream that has been configured to cache the current value'
        client = self._get_client()
        response = (await stream_current_value_controller_query.asyncio_detailed(client=client, json_body=scope_filter))
        return response
