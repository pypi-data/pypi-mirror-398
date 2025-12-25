
from formant.sdk.cloud.v2.src.resources.resources import Resources
from . import IngestionRequest, List, Response, ingest_controller_post, ingest_controller_post_all

class Ingest(Resources):

    def post(self, ingestion_request: IngestionRequest):
        client = self._get_client()
        response: Response = ingest_controller_post.sync_detailed(client=client, json_body=ingestion_request)
        return response

    async def post_async(self, ingestion_request: IngestionRequest):
        client = self._get_client()
        response: Response = (await ingest_controller_post.asyncio_detailed(client=client, json_body=ingestion_request))
        return response

    def post_all(self, ingestion_requests: List[IngestionRequest]):
        client = self._get_client()
        response: Response = ingest_controller_post_all.sync_detailed(client=client, json_body=ingestion_requests)
        return response

    async def post_all_async(self, ingestion_requests: List[IngestionRequest]):
        client = self._get_client()
        response: Response = (await ingest_controller_post_all.asyncio_detailed(client=client, json_body=ingestion_requests))
        return response
