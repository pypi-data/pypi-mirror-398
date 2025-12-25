
from formant.sdk.cloud.v2.formant_query_api_client.api.presence import presence_controller_count
from formant.sdk.cloud.v2.formant_query_api_client.models.interval_query import IntervalQuery
from formant.sdk.cloud.v2.src.resources.resources import Resources

class Presence(Resources):

    def count(self, interval_query: IntervalQuery):
        'Tells you if data has been ingested within a certain time period'
        client = self._get_client()
        response = presence_controller_count.sync_detailed(client=client, json_body=interval_query)
        return response

    async def count_async(self, interval_query: IntervalQuery):
        'Tells you if data has been ingested within a certain time period'
        client = self._get_client()
        response = (await presence_controller_count.asyncio_detailed(client=client, json_body=interval_query))
        return response
