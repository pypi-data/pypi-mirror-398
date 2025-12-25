
from formant.sdk.cloud.v2.src.resources.resources import Resources
from . import MetadataListResponse, Response, ScopeFilter, StringListResponse, UuidListResponse, metadata_controller_list_device_ids, metadata_controller_list_metadata, metadata_controller_list_stream_names

class Metadata(Resources):

    def list_metadata(self, scope_filer: ScopeFilter):
        'List stream metadata'
        client = self._get_client()
        response: Response[MetadataListResponse] = metadata_controller_list_metadata.sync_detailed(client=client, json_body=scope_filer)
        return response

    async def list_metadata_async(self, scope_filer: ScopeFilter):
        'List stream metadata'
        client = self._get_client()
        response: Response[MetadataListResponse] = (await metadata_controller_list_metadata.asyncio_detailed(client=client, json_body=scope_filer))
        return response

    def list_stream_names(self, scope_filer: ScopeFilter):
        'List stream names'
        client = self._get_client()
        response: Response[StringListResponse] = metadata_controller_list_stream_names.sync_detailed(client=client, json_body=scope_filer)
        return response

    async def list_stream_names_async(self, scope_filer: ScopeFilter):
        'List stream names'
        client = self._get_client()
        response: Response[StringListResponse] = (await metadata_controller_list_stream_names.asyncio_detailed(client=client, json_body=scope_filer))
        return response

    def list_device_ids(self, scope_filer: ScopeFilter):
        'List device ids'
        client = self._get_client()
        response: Response[UuidListResponse] = metadata_controller_list_device_ids.sync_detailed(client=client, json_body=scope_filer)
        return response

    async def list_device_ids_async(self, scope_filer: ScopeFilter):
        'List device ids'
        client = self._get_client()
        response: Response[UuidListResponse] = (await metadata_controller_list_device_ids.asyncio_detailed(client=client, json_body=scope_filer))
        return response
