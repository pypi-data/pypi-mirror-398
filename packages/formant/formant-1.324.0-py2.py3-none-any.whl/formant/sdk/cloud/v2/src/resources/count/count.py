
from formant.sdk.cloud.v2.src.resources.resources import Resources
from . import ActiveDevicesQuery, Response, UuidListResponse, count_controller_active_devices

class Count(Resources):

    def active_devices(self, active_devices_query: ActiveDevicesQuery):
        'Gets all the active devices during the timestamp'
        client = self._get_client()
        response: Response[UuidListResponse] = count_controller_active_devices.sync_detailed(client=client, json_body=active_devices_query)
        return response

    async def active_devices_async(self, active_devices_query: ActiveDevicesQuery):
        'Gets all the active devices during the timestamp'
        client = self._get_client()
        response: Response[UuidListResponse] = (await count_controller_active_devices.asyncio_detailed(client=client, json_body=active_devices_query))
        return response
