from formant.sdk.cloud.v2.src.resources.resources import Resources
from . import Query, Response, StreamDataListResponse, query_controller_query

class Queries(Resources):

    def query(self, query: Query, app_id='formant/sdk'):
        """Queries objects based on data types"""
        client = self._get_client()
        response: Response[StreamDataListResponse] = query_controller_query.sync_detailed(client=client, json_body=query, app_id=app_id)
        return response

    async def query_async(self, query: Query, app_id='formant/sdk'):
        """Queries objects based on data types"""
        client = self._get_client()
        response: Response[StreamDataListResponse] = await query_controller_query.asyncio_detailed(client=client, json_body=query, app_id=app_id)
        return response