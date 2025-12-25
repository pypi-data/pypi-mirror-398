import logging
import os
from typing import Optional
from urllib.parse import urljoin

from httpx import AsyncClient
from httpx import Client
from sapure.enums import ExportStatus
from sapure.services.base.entities import AnnotationClassEntity
from sapure.services.base.entities import FolderEntity
from sapure.services.base.entities import ItemEntity
from sapure.services.base.service_provider import AsyncSAServiceProvider
from sapure.services.base.service_provider import BaseSAServiceProvider
from sapure.services.base.service_provider import Response
from sapure.services.work_management.entities import ItemCategory

logger = logging.getLogger("__file__")


class MonolithInternalServiceBase:
    """Base class with shared logic for MonolithInternalService"""

    URL_LIST_FOLDERS = "internal/get-folders"
    URL_LIST_FOLDERS_BY_IDS = "internal/getFoldersByIds"
    URL_UPDATE_EXPORT = "internal/update-export-internal"
    URL_GET_INTEGRATION = "/internal/integration/{}"
    URL_ANNOTATION_CLASSES = "internal/classes"
    URL_UPLOAD_PROCESS = "internal/update-video"
    URL_ATTACH_ITEMS = "/internal/createImagesForVideo"
    URL_CREATE_FOLDER = "internal/create-folder"
    URL_ATTACH_CATEGORIES = "items/bulk/setcategory"
    URL_DELETE_ITEMS = "/internal/Images"
    URL_GET_SDK_TOKEN = "/internal/get-sdk-token"

    def __init__(self, team_id: int, service_url: Optional[str] = None):
        self.team_id = team_id
        self._service_url = service_url or os.environ["SA_BED_URL"]

    def _build_update_upload_process_data(
        self, percentage: int, error: str = None
    ) -> dict:
        """Build data payload for update upload process"""
        data = {"progress_percent": percentage}
        if error:
            data["error_message"] = error
        return data


class MonolithInternalService(MonolithInternalServiceBase, BaseSAServiceProvider):
    """Synchronous MonolithInternalService"""

    def __init__(self, team_id: int, client: Client, service_url: Optional[str] = None):
        MonolithInternalServiceBase.__init__(self, team_id, service_url)
        BaseSAServiceProvider.__init__(self, client)

    def get_sdk_token(self) -> Response[dict]:
        response = self.client.request(
            method="get",
            url=urljoin(self._service_url, self.URL_GET_SDK_TOKEN),
            params={"team_id": self.team_id},
        )
        response.raise_for_status()
        return self.serialize_response(response, entity_cls=dict, dispatcher=None)

    def list_folders(
        self, project_id: int, folder_ids: list[int] = None
    ) -> Response[FolderEntity]:
        if folder_ids:
            response = self.client.request(
                method="post",
                url=urljoin(self._service_url, self.URL_LIST_FOLDERS_BY_IDS),
                json={"folder_ids": folder_ids},
            )
            return self.serialize_response(
                response, entity_cls=FolderEntity, dispatcher=None
            )
        else:
            return self.paginate(
                url=urljoin(self._service_url, self.URL_LIST_FOLDERS),
                query_params={"team_id": self.team_id, "project_id": project_id},
            )

    def create_folder(self, project_id: int, name: str, user_id: str):
        response = self.client.request(
            method="post",
            url=urljoin(self._service_url, self.URL_CREATE_FOLDER),
            data={
                "team_id": self.team_id,
                "project_id": project_id,
                "name": name,
            },
            headers={"x-sa-on-behalf-of": user_id},
        )
        return self.serialize_response(
            response, entity_cls=FolderEntity, dispatcher=None
        )

    def update_export(
        self, export_id: int, status: ExportStatus, progress: int
    ) -> Response[list]:
        response = self.client.request(
            "put",
            url=urljoin(self._service_url, self.URL_UPDATE_EXPORT),
            params={
                "id": export_id,
                "status": status.value,
                "progress_percent": progress,
            },
        )
        return self.serialize_response(response, entity_cls=list, dispatcher=None)

    def get_integration(self, integration_id: int) -> Response[dict]:
        response = self.client.request(
            url=urljoin(
                self._service_url, self.URL_GET_INTEGRATION.format(integration_id)
            ),
            method="get",
            params={"team_id": self.team_id},
        )
        return self.serialize_response(response, entity_cls=dict)

    def list_classes(self, project_id: int) -> Response[AnnotationClassEntity]:
        return self.paginate(
            url=urljoin(self._service_url, self.URL_ANNOTATION_CLASSES),
            query_params={"team_id": self.team_id, "project_id": project_id},
            entity_cls=AnnotationClassEntity,
        )

    def update_upload_process(
        self,
        project_id: int,
        folder_id: int,
        user_id: str,
        percentage: int,
        error: str = None,
    ) -> Response[dict]:
        """
        Update upload process in frontend
        """
        data = self._build_update_upload_process_data(percentage, error)
        response = self.client.request(
            method="post",
            url=urljoin(self._service_url, self.URL_UPLOAD_PROCESS),
            data=data,
            params={
                "team_id": self.team_id,
                "user_id": user_id,
                "project_id": project_id,
                "folder_id": folder_id,
            },
        )
        return self.serialize_response(response, entity_cls=dict)

    def attach_items(
        self,
        project_id: int,
        folder_id: int,
        items: list[dict],
        meta: dict,
        annotation_status: int,
        upload_state: int,
        integration_id: int = None,
    ) -> Response:
        response = self.client.request(
            method="post",
            url=urljoin(self._service_url, self.URL_ATTACH_ITEMS),
            json={
                "team_id": self.team_id,
                "project_id": project_id,
                "folder_id": folder_id,
                "images": items,
                "meta": meta,
                "annotation_status": annotation_status,
                "upload_state": upload_state,
                "integration_id": integration_id,
            },
            params={"team_id": self.team_id, "project_id": project_id},
        )
        return self.serialize_response(response, entity_cls=ItemEntity, dispatcher=None)

    def delete_items(
        self, project_id: int, folder_id: int, item_ids: list[int]
    ) -> Response:
        response = self.client.request(
            "delete",
            url=urljoin(self._service_url, self.URL_DELETE_ITEMS),
            params={"team_id": self.team_id, "project_id": project_id},
            json={
                "project_id": project_id,
                "folder_id": folder_id,
                "team_id": self.team_id,
                "image_ids": item_ids,
                "force_delete": True,
                "reduce_from_billing": True,
            },
        )
        return self.serialize_response(response, dispatcher=None)

    def attach_categories(
        self,
        project_id: int,
        folder_id: int,
        item_id_category_id_map: dict[int, dict],
    ) -> Response[list[ItemCategory]]:
        response = self.client.post(
            url=urljoin(self._service_url, self.URL_ATTACH_CATEGORIES),
            params={
                "team_id": self.team_id,
                "project_id": project_id,
                "folder_id": folder_id,
            },
            json={
                "bulk": [
                    {"item_id": item_id, "categories": [category]}
                    for item_id, category in item_id_category_id_map.items()
                ]
            },
        )
        return self.serialize_response(response, dispatcher=None)


class AsyncMonolithInternalService(MonolithInternalServiceBase, AsyncSAServiceProvider):
    """Asynchronous MonolithInternalService"""

    def __init__(
        self, team_id: int, client: AsyncClient, service_url: Optional[str] = None
    ):
        MonolithInternalServiceBase.__init__(self, team_id, service_url)
        AsyncSAServiceProvider.__init__(self, client)

    async def get_sdk_token(self) -> Response[dict]:
        response = await self.client.request(
            method="get",
            url=urljoin(self._service_url, self.URL_GET_SDK_TOKEN),
            params={"team_id": self.team_id},
        )
        response.raise_for_status()
        return self.serialize_response(response, entity_cls=dict, dispatcher=None)

    async def list_folders(
        self, project_id: int, folder_ids: list[int] = None
    ) -> Response[FolderEntity]:
        if folder_ids:
            response = await self.client.request(
                method="post",
                url=urljoin(self._service_url, self.URL_LIST_FOLDERS_BY_IDS),
                json={"folder_ids": folder_ids},
            )
            return self.serialize_response(
                response, entity_cls=FolderEntity, dispatcher=None
            )
        else:
            return await self.paginate(
                url=urljoin(self._service_url, self.URL_LIST_FOLDERS),
                query_params={"team_id": self.team_id, "project_id": project_id},
            )

    async def create_folder(self, project_id: int, name: str, user_id: str):
        response = await self.client.request(
            method="post",
            url=urljoin(self._service_url, self.URL_CREATE_FOLDER),
            data={
                "team_id": self.team_id,
                "project_id": project_id,
                "name": name,
            },
            headers={"x-sa-on-behalf-of": user_id},
        )
        return self.serialize_response(
            response, entity_cls=FolderEntity, dispatcher=None
        )

    async def update_export(
        self, export_id: int, status: ExportStatus, progress: int
    ) -> Response[list]:
        response = await self.client.request(
            "put",
            url=urljoin(self._service_url, self.URL_UPDATE_EXPORT),
            params={
                "id": export_id,
                "status": status.value,
                "progress_percent": progress,
            },
        )
        return self.serialize_response(response, entity_cls=list, dispatcher=None)

    async def get_integration(self, integration_id: int) -> Response[dict]:
        response = await self.client.request(
            url=urljoin(
                self._service_url, self.URL_GET_INTEGRATION.format(integration_id)
            ),
            method="get",
            params={"team_id": self.team_id},
        )
        return self.serialize_response(response, entity_cls=dict)

    async def list_classes(self, project_id: int) -> Response[AnnotationClassEntity]:
        return await self.paginate(
            url=urljoin(self._service_url, self.URL_ANNOTATION_CLASSES),
            query_params={"team_id": self.team_id, "project_id": project_id},
            entity_cls=AnnotationClassEntity,
        )

    async def update_upload_process(
        self,
        project_id: int,
        folder_id: int,
        user_id: str,
        percentage: int,
        error: str = None,
    ) -> Response[dict]:
        """
        Update upload process in frontend
        """
        data = self._build_update_upload_process_data(percentage, error)
        response = await self.client.request(
            method="post",
            url=urljoin(self._service_url, self.URL_UPLOAD_PROCESS),
            data=data,
            params={
                "team_id": self.team_id,
                "user_id": user_id,
                "project_id": project_id,
                "folder_id": folder_id,
            },
        )
        return self.serialize_response(response, entity_cls=dict)

    async def attach_items(
        self,
        project_id: int,
        folder_id: int,
        items: list[dict],
        meta: dict,
        annotation_status: int,
        upload_state: int,
        integration_id: int = None,
    ) -> Response:
        response = await self.client.request(
            method="post",
            url=urljoin(self._service_url, self.URL_ATTACH_ITEMS),
            json={
                "team_id": self.team_id,
                "project_id": project_id,
                "folder_id": folder_id,
                "images": items,
                "meta": meta,
                "annotation_status": annotation_status,
                "upload_state": upload_state,
                "integration_id": integration_id,
            },
            params={"team_id": self.team_id, "project_id": project_id},
        )
        return self.serialize_response(response, entity_cls=ItemEntity, dispatcher=None)

    async def delete_items(
        self, project_id: int, folder_id: int, item_ids: list[int]
    ) -> Response:
        response = await self.client.request(
            "delete",
            url=urljoin(self._service_url, self.URL_DELETE_ITEMS),
            params={"team_id": self.team_id, "project_id": project_id},
            json={
                "project_id": project_id,
                "folder_id": folder_id,
                "team_id": self.team_id,
                "image_ids": item_ids,
                "force_delete": True,
                "reduce_from_billing": True,
            },
        )
        return self.serialize_response(response, dispatcher=None)

    async def attach_categories(
        self,
        project_id: int,
        folder_id: int,
        item_id_category_id_map: dict[int, dict],
    ) -> Response[list[ItemCategory]]:
        response = await self.client.post(
            url=urljoin(self._service_url, self.URL_ATTACH_CATEGORIES),
            params={
                "team_id": self.team_id,
                "project_id": project_id,
                "folder_id": folder_id,
            },
            json={
                "bulk": [
                    {"item_id": item_id, "categories": [category]}
                    for item_id, category in item_id_category_id_map.items()
                ]
            },
        )
        return self.serialize_response(response, dispatcher=None)
