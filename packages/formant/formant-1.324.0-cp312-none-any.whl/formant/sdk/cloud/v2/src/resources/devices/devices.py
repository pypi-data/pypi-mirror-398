from formant.sdk.cloud.v2.src.resources.resources import Resources
from . import Device, DeviceConfiguration, DeviceListResponse, DeviceQuery, Optional, PartialDevice, Response, device_controller_get_configuration, device_controller_get_one, device_controller_patch, device_controller_post_configuration, device_controller_query

class Devices(Resources):

    def query(self, device_query: DeviceQuery):
        """Query devices by name and/or tags"""
        client = self._get_client()
        response: Response[DeviceListResponse] = device_controller_query.sync_detailed(client=client, json_body=device_query)
        return response

    async def query_async(self, device_query: DeviceQuery):
        """Query devices by name and/or tags"""
        client = self._get_client()
        response: Response[DeviceListResponse] = await device_controller_query.asyncio_detailed(client=client, json_body=device_query)
        return response

    def patch(self, device_id: str, partial_device: PartialDevice):
        """Update a device"""
        client = self._get_client()
        response: Response[Device] = device_controller_patch.sync_detailed(client=client, id=device_id, json_body=partial_device)
        return response

    async def patch_async(self, device_id: str, partial_device: PartialDevice):
        """Update a device"""
        client = self._get_client()
        response: Response[Device] = await device_controller_patch.asyncio_detailed(client=client, id=device_id, json_body=partial_device)
        return response

    def get_device(self, device_id: str):
        """Get a device"""
        client = self._get_client()
        response: Response[Device] = device_controller_get_one.sync_detailed(client=client, id=device_id)
        return response

    async def get_device_async(self, device_id: str):
        """Get a device"""
        client = self._get_client()
        response: Response[Device] = await device_controller_get_one.asyncio_detailed(client=client, id=device_id)
        return response

    def get_device_configuration(self, device_id: str, desired_configuration_version: int):
        """Get a device configuration"""
        client = self._get_client()
        response: Response[Optional[DeviceConfiguration]] = device_controller_get_configuration.sync_detailed(client=client, id=device_id, version=desired_configuration_version)
        return response

    async def get_device_configuration_async(self, device_id: str, desired_configuration_version: int):
        """Get a device configuration"""
        client = self._get_client()
        response: Response[Optional[DeviceConfiguration]] = await device_controller_get_configuration.asyncio_detailed(client=client, id=device_id, version=desired_configuration_version)
        return response

    def post_device_configuration(self, device_id, device_configuration: DeviceConfiguration):
        """Create a device configuration"""
        client = self._get_client()
        response: Response[Optional[DeviceConfiguration]] = device_controller_post_configuration.sync_detailed(client=client, id=device_id, json_body=device_configuration)
        return response

    async def post_device_configuration_async(self, device_id, device_configuration: DeviceConfiguration):
        """Create a device configuration"""
        client = self._get_client()
        response: Response[Optional[DeviceConfiguration]] = await device_controller_post_configuration.asyncio_detailed(client=client, id=device_id, json_body=device_configuration)
        return response