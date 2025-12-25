import asyncio
import io
import json
import logging
import os
from pathlib import Path
from typing import Callable
from typing import List
from typing import Literal
from typing import Optional
from urllib.parse import urljoin

import aiofiles
from httpx import AsyncClient
from sapure.enums import ProjectNumericEnum
from sapure.enums import ProjectTypeEnum
from sapure.services.assets_provider.entities import ClassifiedItems
from sapure.services.assets_provider.entities import UploadAnnotationsResponse
from sapure.services.assets_provider.utils import async_retry_on_generator
from sapure.services.assets_provider.utils import divide_to_chunks
from sapure.services.assets_provider.utils import store_annotation
from sapure.services.base.service_provider import AsyncSAServiceProvider
from sapure.services.base.service_provider import ErrorDetail
from sapure.services.base.service_provider import Response
from sapure.services.exceptions import SAConnectioError
from sapure.services.utils import join_url

logger = logging.getLogger("sa")


class AssetsProviderService(AsyncSAServiceProvider):
    DELIMITER = "\\n;)\\n"
    DELIMITER_LEN = len(DELIMITER)

    URL_ANNOTATIONS_SCHEMA = "items/annotations/schema"
    URL_GET_CLASSIFIED_ITEMS = "items/annotations/download/method"
    URL_GET_SMALL_ANNOTATIONS = "items/annotations/download"
    URL_UPLOAD_ANNOTATIONS = "items/annotations/upload"
    URL_START_FILE_SYNC = "items/{item_id}/annotations/sync"
    URL_START_FILE_SYNC_STATUS = "items/{item_id}/annotations/sync/status"
    URL_START_FILE_UPLOAD_PROCESS = "items/{item_id}/annotations/upload/multipart/start"
    URL_START_FILE_SEND_PART = "items/{item_id}/annotations/upload/multipart/part"
    URL_START_FILE_SEND_FINISH = "items/{item_id}/annotations/upload/multipart/finish"
    URL_RETRIEVE_ANNOTATIONS = "items/{item_id}/annotations/download"
    URL_SET_ITEM_ANNOTATIONS = "items/{item_id}/annotations/upload"

    def __init__(
        self, team_id: int, client: AsyncClient, service_url: Optional[str] = None
    ):
        self.team_id = team_id
        self._service_url = service_url or join_url(
            os.environ["SA_ASSETS_PROVIDER_URL"], "api/v4/"
        )
        super().__init__(client)

    @staticmethod
    def annotation_is_valid(annotation: dict) -> bool:
        annotation_keys = annotation.keys()
        if (
            "errors" in annotation_keys
            or "error" in annotation_keys
            or "metadata" not in annotation_keys
        ):
            return False
        return True

    async def get_annotation_schema(
        self, project_type: int, version: str
    ) -> Response[dict]:
        return self.serialize_response(
            await self.client.request(
                urljoin(self._service_url, self.URL_ANNOTATIONS_SCHEMA),
                "get",
                params={"project_type": project_type, "version": version},
            ),
        )

    async def get_classified_upload_items(
        self,
        project_id: int,
        project_type: ProjectNumericEnum,
        items: List[dict],
        chunk_size: int = 1000,
    ) -> Response[ClassifiedItems]:
        small, large = [], []
        for chunk in divide_to_chunks(items, chunk_size):
            response = await self.client.request(
                method="post",
                url=urljoin(self._service_url, self.URL_GET_CLASSIFIED_ITEMS),
                params={"team_id": self.team_id, "limit": len(chunk)},
                json={
                    "project_id": project_id,
                    "project_type": project_type.value,
                    "items": chunk,
                },
            )
            if not response.is_success:
                return Response.error_response("Annotations classify call failed.")

            res_data = response.json()
            small.extend([i["data"] for i in res_data.get("small", {}).values()])
            large.extend(res_data.get("large", []))
        return Response[ClassifiedItems](data={"small": small, "large": large})

    async def download_small_annotations(
        self,
        project_id: int,
        workflow_id: int,
        project_type: ProjectTypeEnum,
        *,
        classes: List[dict],
        download_path: str,
        postfix: str,
        items_ids: List[int] = None,
        transform_version: Optional[
            Literal["V1", "llmJson", "llmJsonV2", "export"]
        ] = None,
    ):
        annotations = await self.list_small_annotations(
            project_id=project_id,
            workflow_id=workflow_id,
            project_type=project_type,
            classes=classes,
            item_ids=items_ids,
            transform_version=transform_version,
        )
        for annotation in annotations:
            await store_annotation(download_path, postfix, annotation)

    async def list_small_annotations(
        self,
        project_id: int,
        workflow_id: Optional[int] = None,
        item_ids: List[int] = None,
        *,
        classes: List[dict] = None,
        project_type: ProjectTypeEnum = None,
        transform_version: Optional[
            Literal["V1", "llmJson", "llmJsonV2", "export"]
        ] = None,
    ) -> List[dict]:
        payload = {
            "image_ids": item_ids,
            "project": {"id": project_id},
        }
        if project_type:
            payload["project"]["type"] = project_type.value
        if workflow_id:
            payload["project"]["workflow_id"] = workflow_id
        if classes:
            payload["classes"] = classes

        query_params = {
            "team_id": self.team_id,
            "project_id": project_id,
            "limit": len(item_ids),
        }
        query_params["transform_version"] = (
            transform_version if transform_version else "llmJsonV2"
        )
        parser = AnnotationStreamParser(self.DELIMITER)
        parser.setup(
            client=self.client,
            method="post",
            url=urljoin(self._service_url, self.URL_GET_SMALL_ANNOTATIONS),
            data=payload,
            params=query_params,
        )
        return [annotation async for annotation in parser]

    async def download_small_annotations_prepared(
        self,
        project_id: int,
        workflow_id: int,
        project_type: ProjectTypeEnum,
        *,
        classes: List[dict],
        download_path: str,
        postfix: str,
        items_ids: List[int] = None,
        items: List[dict] = None,
        transform_version: Optional[
            Literal["V1", "llmJson", "llmJsonV2", "export"]
        ] = None,
    ):
        annotations = await self.list_small_annotations_prepared(
            project_id=project_id,
            workflow_id=workflow_id,
            project_type=project_type,
            classes=classes,
            item_ids=items_ids,
            items=items,
            transform_version=transform_version,
        )
        for annotation in annotations:
            await store_annotation(download_path, postfix, annotation)

    async def list_small_annotations_prepared(
        self,
        project_id: int,
        workflow_id: int,
        project_type: ProjectTypeEnum,
        *,
        classes: List[dict],
        item_ids: List[int] = None,
        items: List[dict],
        transform_version: Optional[
            Literal["V1", "llmJson", "llmJsonV2", "export"]
        ] = None,
    ) -> List[dict]:
        """Got items data for send assets-provider"""
        payload = {
            "project": {
                "id": project_id,
                "type": project_type,
                "workflow_id": workflow_id,
            },
        }
        if item_ids:
            payload["image_ids"] = item_ids
        if items:
            payload["items"] = items
        if classes:
            payload["classes"] = classes

        query_params = {
            "team_id": self.team_id,
            "project_id": project_id,
            "transform_version": transform_version,
            "limit": len(items) if items else len(item_ids),
        }

        parser = AnnotationStreamParser(self.DELIMITER)
        parser.setup(
            client=self.client,
            method="post",
            url=urljoin(self._service_url, "items/annotations/download/prepared"),
            data=payload,
            params=query_params,
        )
        return [annotation async for annotation in parser]

    async def upload_small_annotations(
        self,
        project_id: int,
        folder_id: int,
        item_id_annotation_map: dict[int, dict],
        transform_version: str,
    ) -> Response[UploadAnnotationsResponse]:
        params = [
            ("team_id", self.team_id),
            ("project_id", project_id),
            ("folder_id", folder_id),
            ("transform_version", transform_version),
            *[("image_ids[]", item_id) for item_id in item_id_annotation_map.keys()],
        ]
        files = {}
        for item_id, data in item_id_annotation_map.items():
            item_id_str = str(item_id)
            buffer = io.BytesIO(
                json.dumps({"data": data}, allow_nan=False).encode("utf-8")
            )
            files[item_id_str] = (item_id_str, buffer, "application/json")
        response = await self.client.request(
            url=urljoin(self._service_url, self.URL_UPLOAD_ANNOTATIONS),
            method="post",
            params=params,
            files=files,
        )
        return self.serialize_response(response, entity_cls=UploadAnnotationsResponse)

    async def _sync_large_annotation(
        self, project_id: int, item_id: int, desired_transform_version: str = None
    ):
        sync_params = {
            "team_id": self.team_id,
            "project_id": project_id,
            "desired_version": "V1.00",
            "current_transform_version": "V1.00",
            "current_source": "main",
            "desired_source": "secondary",
        }
        if desired_transform_version:
            sync_params["desired_transform_version"] = desired_transform_version
        sync_url = urljoin(
            self._service_url,
            self.URL_START_FILE_SYNC.format(item_id=item_id),
        )
        await self.client.request("post", sync_url, params=sync_params)
        sync_params.pop("current_source")
        sync_params.pop("desired_source")
        synced = False
        sync_status_url = urljoin(
            self._service_url, self.URL_START_FILE_SYNC_STATUS.format(item_id=item_id)
        )
        while synced != "SUCCESS":
            synced = await self.client.request(
                "get", sync_status_url, params=sync_params
            )
            synced = synced.json()
            synced = synced["status"]
            await asyncio.sleep(1)
        return synced

    async def download_large_annotation(
        self,
        project_id: int,
        download_path: str,
        postfix: str,
        item: dict,
        callback: Callable = None,
        transform_version: Optional[Literal["llmJson", "llmJsonV2", "export"]] = None,
    ) -> Response:
        item_id = item["id"]
        item_name = item["name"]
        query_params = {
            "team_id": self.team_id,
            "project_id": project_id,
            "annotation_type": "MAIN",
            "version": "V1.00",
        }
        if transform_version is not None:
            query_params["transform_version"] = transform_version

        logging.info(f"Downloading large annotation; item_id [{item_id}]")
        await self._sync_large_annotation(
            project_id=project_id,
            item_id=item_id,
            desired_transform_version=transform_version,
        )

        url = urljoin(
            self._service_url,
            self.URL_RETRIEVE_ANNOTATIONS.format(item_id=item_id),
        )
        start_response = await self.client.request("post", url, params=query_params)
        if not start_response.is_success:
            return Response.error_response("Download failed.")
        res = start_response.json()
        if start_response.status_code > 299 or not self.annotation_is_valid(res):
            logging.error(
                f"Failed to download large annotation; item_id [{item_id}];"
                f" response: {res}; http_status: {start_response.status_code}"
            )
            raise Exception(f"Failed to download large annotation, ID: {item_id}")
        Path(download_path).mkdir(exist_ok=True, parents=True)
        dest_path = Path(download_path) / (item_name + postfix)
        async with aiofiles.open(dest_path, "w") as file:
            if callback:
                res = callback(res)
            await file.write(json.dumps(res))
        return Response[str](success=True, data=str(dest_path))

    async def upload_large_annotation(
        self,
        project_id: int,
        folder_id: int,
        item_id: int,
        data: io.StringIO,
        chunk_size: int,
        transform_version: str,
    ) -> Response[str]:
        params = {
            "team_id": self.team_id,
            "project_id": project_id,
            "folder_id": folder_id,
            "desired_transform_version": transform_version,
        }

        start_result = await self._start_upload(item_id, params)
        if not start_result["success"]:
            return Response[str](
                success=False, errors=[ErrorDetail(message="Upload failed.")]
            )

        upload_info = start_result["data"]
        success = await self._upload_chunks(
            item_id, data, chunk_size, params, upload_info
        )
        if not success:
            return Response[str](
                success=False, errors=[ErrorDetail(message="Upload failed.")]
            )

        return await self._finalize_and_sync(item_id, params, upload_info)

    async def _start_upload(self, item_id: int, params: dict) -> dict:
        response = await self.client.request(
            "post",
            urljoin(
                self._service_url,
                self.URL_START_FILE_UPLOAD_PROCESS.format(item_id=item_id),
            ),
            params=params,
        )
        if not response.is_success:
            return {"success": False, "data": response.json()}

        return {"success": True, "data": response.json()}

    async def _upload_chunks(
        self,
        item_id: int,
        data: io.StringIO,
        chunk_size: int,
        params: dict,
        upload_info: dict,
    ) -> bool:
        params["path"] = upload_info["path"]
        headers = {"upload_id": upload_info["upload_id"]}
        chunk_id = 1
        data_sent = False

        while True:
            chunk = data.read(chunk_size)
            params["chunk_id"] = chunk_id
            if chunk:
                data_sent = True
                response = await self.client.request(
                    "post",
                    urljoin(
                        self._service_url,
                        self.URL_START_FILE_UPLOAD_PROCESS.format(item_id=item_id),
                    ),
                    params=params,
                    headers=headers,
                    json=json.dumps({"data_chunk": chunk}, allow_nan=False),
                )
                if not response.is_success:
                    return False
                chunk_id += 1
            if not chunk and not data_sent:
                return False
            if len(chunk) < chunk_size:
                break
        del params["chunk_id"]
        return True

    async def _finalize_and_sync(
        self, item_id: int, params: dict, upload_info: dict
    ) -> Response[str]:
        headers = {"upload_id": upload_info["upload_id"]}
        del params["path"]
        finish_url = urljoin(
            self._service_url,
            self.URL_START_FILE_UPLOAD_PROCESS.format(item_id=item_id),
        )
        response = await self.client.request(
            "post", finish_url, headers=headers, params=params
        )
        if not response.is_success:
            return Response[str](
                success=False, errors=[ErrorDetail(message="Upload failed.")]
            )

        sync_url = urljoin(
            self._service_url, self.URL_START_FILE_SYNC.format(item_id=item_id)
        )
        response = await self.client.request(
            "post", sync_url, params=params, headers=headers
        )
        if not response.is_success:
            return Response[str](
                success=False, errors=[ErrorDetail(message="Upload failed.")]
            )

        while True:
            status_url = urljoin(
                self._service_url,
                self.URL_START_FILE_SYNC_STATUS.format(item_id=item_id),
            )
            response = await self.client.request(
                "get", status_url, params=params, headers=headers
            )
            if response.is_success:
                data = response.json()
                status = data.get("status")
                if status == "SUCCESS":
                    return Response[str](success=True, data="Upload successful.")
                if status.startswith("FAILED"):
                    return Response[str](
                        success=False, errors=[ErrorDetail(message="Upload failed.")]
                    )
                await asyncio.sleep(15)
            else:
                return Response[str](
                    success=False, errors=[ErrorDetail(message="Upload failed.")]
                )

    async def get_item_annotations(
        self,
        project_id: int,
        project_type: int,
        item_id: int,
        transform_version: str,
        folder_id: Optional[int] = None,
    ) -> Response[dict]:
        params = {
            "team_id": self.team_id,
            "project_id": project_id,
            "project_type": project_type,
            "transform_version": transform_version,
        }
        if folder_id:
            params["folder_id"] = folder_id
        response = await self.client.request(
            "get",
            urljoin(
                self._service_url,
                self.URL_RETRIEVE_ANNOTATIONS.format(item_id=item_id),
            ),
            params=params,
        )
        return self.serialize_response(response, entity_cls=dict, dispatcher=None)

    async def set_item_annotations(
        self,
        project_id: int,
        project_type: int,
        item_id: int,
        data: dict,
        transform_version: str,
        *,
        folder_id: Optional[int] = None,
        overwrite: bool = True,
        etag: str = None,
    ) -> Response[str]:
        params = {
            "team_id": self.team_id,
            "project_id": project_id,
            "project_type": project_type,
            "transform_version": transform_version,
            "overwrite": overwrite,
        }
        if folder_id:
            params["folder_id"] = folder_id
        if etag:
            params["etag"] = etag
        response = await self.client.request(
            url=urljoin(
                self._service_url, self.URL_SET_ITEM_ANNOTATIONS.format(item_id=item_id)
            ),
            method="put",
            params=params,
            json=data,
        )
        if response.is_success:
            return Response[str](success=True, data="Upload successful.")
        return Response[str](
            success=False, errors=[ErrorDetail(message="Upload failed.")]
        )


class AnnotationStreamParser:
    def __init__(self, delimiter: str):
        self.delimiter = delimiter
        self.delimiter_len = len(delimiter)
        self.client: Optional[AsyncClient] = None
        self.method: Optional[str] = None
        self.url: Optional[str] = None
        self.data: Optional[dict] = None
        self.params: Optional[dict] = None

    def setup(
        self,
        client: AsyncClient,
        method: Literal["get", "post", "put"],
        url: str,
        data: Optional[dict] = None,
        params: Optional[dict] = None,
    ):
        self.client = client
        self.method = method
        self.url = url
        self.data = data
        self.params = params

    @staticmethod
    def annotation_is_valid(annotation: dict) -> bool:
        annotation_keys = annotation.keys()
        if (
            "errors" in annotation_keys
            or "error" in annotation_keys
            or "metadata" not in annotation_keys
        ):
            return False
        return True

    def __aiter__(self):
        return self._parse()

    @async_retry_on_generator((SAConnectioError,))
    async def _parse(self):
        assert self.client is not None
        response = await self.client.request(
            self.method, self.url, params=self.params, json=self.data
        )
        if response.is_error:
            logger.error(response.text)

        text_buffer = ""
        raw_chunk = b""
        decoder = json.JSONDecoder()

        async for line in response.aiter_bytes():
            raw_chunk += line
            try:
                text_buffer += raw_chunk.decode("utf-8")
                raw_chunk = b""
            except UnicodeDecodeError:
                continue

            while text_buffer:
                try:
                    if text_buffer.startswith(self.delimiter):
                        text_buffer = text_buffer[self.delimiter_len :]

                    json_obj, index = decoder.raw_decode(text_buffer)
                    yield json_obj

                    remainder = text_buffer[index:]
                    if remainder.startswith(self.delimiter):
                        text_buffer = remainder[self.delimiter_len :]
                    else:
                        text_buffer = remainder
                        break
                except json.JSONDecodeError as e:
                    logger.debug(
                        "Failed to parse buffer (len: %d): start: %s ... end: %s | error: %s",
                        len(text_buffer),
                        text_buffer[:50],
                        text_buffer[-50:],
                        e,
                    )
                    break
