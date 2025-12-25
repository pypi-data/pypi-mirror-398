from formant.sdk.cloud.v2.src.resources.resources import Resources
from . import Adapter, Any, Response, adapter_controller_delete, adapter_controller_post

class Adapters(Resources):

    def create(self, adapter: Adapter):
        """Creates an Adapter"""
        client = self._get_client()
        response: Response[Adapter] = adapter_controller_post.sync_detailed(client=client, json_body=adapter)
        return response

    async def create_async(self, adapter: Adapter):
        """Creates an Adapter"""
        client = self._get_client()
        response: Response[Adapter] = await adapter_controller_post.asyncio_detailed(client=client, json_body=adapter)
        return response

    def delete(self, id: str):
        """Deletes and Adapter"""
        client = self._get_client()
        response: Response[Any] = adapter_controller_delete.sync_detailed(client=client, id=id)
        return response

    async def delete_async(self, id: str):
        """Deletes and Adapter"""
        client = self._get_client()
        response: Response[Any] = await adapter_controller_delete.asyncio_detailed(client=client, id=id)
        return response