import ntpath
import os

import requests
from formant.sdk.cloud.v2.src.resources.resources import Resources

from . import (
    Any,
    BeginUploadRequest,
    BeginUploadResponse,
    CompleteUploadRequest,
    Response,
    file_controller_begin_upload,
    file_controller_complete_upload,
)


class Files(Resources):
    def upload(self, path: str, timeout: int = 60):
        """Uploads a file"""
        file_name = ntpath.basename(path)
        file_size = os.path.getsize(path)
        if not file_size > 0:
            raise ValueError("File is empty")
        begin_upload_request = BeginUploadRequest(
            file_name, file_size, force_overwrite=False
        )
        begin_upload_result = self._begin_upload(begin_upload_request, timeout)
        file_id = begin_upload_result.parsed.file_id
        upload_id = begin_upload_result.parsed.upload_id
        part_urls = begin_upload_result.parsed.part_urls
        part_size = begin_upload_result.parsed.part_size
        etags = self._create_etags(path, part_urls, part_size)
        complete_upload_request = CompleteUploadRequest(
            file_id, upload_id, etags, force_overwrite=False
        )
        complete_upload_response = self._complete_upload(
            complete_upload_request, timeout
        )
        return file_id, complete_upload_response

    def _begin_upload(self, begin_upload_request: BeginUploadRequest, timeout: int):
        client = self._get_client().with_timeout(timeout)
        response: Response[BeginUploadResponse] = (
            file_controller_begin_upload.sync_detailed(
                client=client, json_body=begin_upload_request
            )
        )
        return response

    def _complete_upload(
        self, complete_upload_request: CompleteUploadRequest, timeout: int
    ):
        client = self._get_client().with_timeout(timeout)
        response: Response[Any] = file_controller_complete_upload.sync_detailed(
            client=client, json_body=complete_upload_request
        )
        return response

    def _create_etags(self, path: str, part_urls: list, part_size: int):
        etags = []
        part_index = 0
        file_obj = open(path, "rb")
        for part_url in part_urls:
            file_obj.seek(part_index * part_size)
            part_index = part_index + 1
            data = file_obj.read(part_size)
            response = requests.put(part_url, data=data)
            etags.append(response.headers["etag"])
        file_obj.close()
        return etags

    async def upload_async(self, path: str, timeout: int = 60):
        """Uploads a file"""
        file_name = ntpath.basename(path)
        file_size = os.path.getsize(path)
        if not file_size > 0:
            raise ValueError("File is empty")
        begin_upload_request = BeginUploadRequest(
            file_name, file_size, force_overwrite=False
        )
        begin_upload_result = await self._begin_upload_async(
            begin_upload_request, timeout
        )
        file_id = begin_upload_result.parsed.file_id
        upload_id = begin_upload_result.parsed.upload_id
        part_urls = begin_upload_result.parsed.part_urls
        part_size = begin_upload_result.parsed.part_size
        etags = self._create_etags(path, part_urls, part_size)
        complete_upload_request = CompleteUploadRequest(
            file_id, upload_id, etags, force_overwrite=False
        )
        complete_upload_response = await self._complete_upload_async(
            complete_upload_request, timeout
        )
        return file_id, complete_upload_response

    def _begin_upload_async(
        self, begin_upload_request: BeginUploadRequest, timeout: int
    ):
        client = self._get_client().with_timeout(timeout)
        response: Response[BeginUploadResponse] = (
            file_controller_begin_upload.asyncio_detailed(
                client=client, json_body=begin_upload_request
            )
        )
        return response

    def _complete_upload_async(
        self, complete_upload_request: CompleteUploadRequest, timeout: int
    ):
        client = self._get_client().with_timeout(timeout)
        response: Response[Any] = file_controller_complete_upload.asyncio_detailed(
            client=client, json_body=complete_upload_request
        )
        return response
