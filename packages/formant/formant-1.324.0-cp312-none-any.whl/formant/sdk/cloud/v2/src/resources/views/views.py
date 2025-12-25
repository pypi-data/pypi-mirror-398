from formant.sdk.cloud.v2.src.resources.resources import Resources
from . import PartialView, Response, View, ViewListResponse, view_controller_get_all, view_controller_get_one, view_controller_patch

class Views(Resources):

    def get(self, device_id: str):
        """Get a device layout"""
        client = self._get_client()
        response: Response[View] = view_controller_get_one.sync_detailed(client=client, id=device_id)
        return response

    async def get_async(self, device_id: str):
        """Get a device layout"""
        client = self._get_client()
        response: Response[View] = await view_controller_get_one.asyncio_detailed(client=client, id=device_id)
        return response

    def get_all(self):
        """List all device layouts"""
        client = self._get_client()
        response: Response[ViewListResponse] = view_controller_get_all.sync_detailed(client=client)
        return response

    async def get_all_async(self):
        """List all device layouts"""
        client = self._get_client()
        response: Response[ViewListResponse] = await view_controller_get_all.asyncio_detailed(client=client)
        return response

    def patch(self, id: str, partial_view: PartialView):
        """Update a device layout"""
        client = self._get_client()
        response: Response[View] = view_controller_patch.sync_detailed(client=client, id=id, json_body=partial_view)
        return response

    async def patch_async(self, id: str, partial_view: PartialView):
        """Update a device layout"""
        client = self._get_client()
        response: Response[View] = await view_controller_patch.asyncio_detailed(client=client, id=id, json_body=partial_view)
        return response