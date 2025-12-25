import asyncio
import logging
import os
import time
from typing import List
from typing import Literal
from typing import Optional
from urllib.parse import urljoin

from httpx import AsyncClient
from httpx import Auth
from httpx import Client
from httpx import AsyncClient
from httpx import USE_CLIENT_DEFAULT
from sapure.services.base.entities import ProjectEntity
from sapure.services.base.entities import FolderEntity
from sapure.services.base.entities import ItemEntity
from sapure.services.base.entities import ProjectEntity
from sapure.services.base.service_provider import AsyncSAServiceProvider
from sapure.services.base.service_provider import BaseSAServiceProvider
from sapure.services.base.service_provider import Response
from sapure.services.explore.conditions import Condition
from sapure.services.monolith.entities import Attachment
from sapure.services.monolith.entities import AttachmentMeta

logger = logging.getLogger("__file__")


class MonolithServiceBase:
    """Base class with shared logic for MonolithService"""

    URL_PROJECTS = "project"
    URL_PROJECTS_GET = "project/{project_id}"
    URL_SETTINGS = "project/{project_id}/settings"
    URL_GET_ITEM = "image/{item_id}"
    URL_ATTACH_ITEM = "image/ext-create"
    URL_COPY_MULTIPLE_ITEMS = "images/copy-image-or-folders"
    URL_ITEM_COPY_PROGRESS = "images/copy-image-progress"
    URL_MOVE_MULTIPLE_ITEM = "image/move"
    URL_COPY_MOVE_MULTIPLE_ITEM = "images/copy-move-images-folders"
    URL_SET_ITEM_ANNOTATION_STATUS_BULK = "image/updateAnnotationStatusBulk"
    URL_SET_ITEM_APPROVAL_STATUSES = "/items/bulk/change"
    URL_DELETE_ITEMS = "image/delete/images"
    URL_ATTACH_ITEM_CATEGORIES = "items/bulk/setcategory"
    URL_LIST_FOLDERS = "folders"
    URL_GET_FOLDER_BY_ID = "folder/getFolderById"
    URL_SET_ITEM_ANNOTATION_STATUS = "image/{item_id}/annotation/save"

    def __init__(
        self,
        team_id: int,
        service_url: Optional[str] = None,
        auth: Optional[Auth] = USE_CLIENT_DEFAULT,
    ):
        self.team_id = team_id
        self._service_url = service_url or f"{os.environ['SA_BED_URL']}/"
        self.auth = auth

    def _build_attach_items_data(
        self,
        project_id: int,
        folder_id: int,
        attachments: List[Attachment],
        upload_state_code,
        metadata: dict[str, AttachmentMeta],
        annotation_status_code=None,
    ) -> dict:
        """Build data payload for attaching items"""
        data = {
            "team_id": self.team_id,
            "project_id": project_id,
            "folder_id": folder_id,
            "images": [i.model_dump() for i in attachments],
            "upload_state": upload_state_code,
            "meta": metadata,
        }
        if annotation_status_code:
            data["annotation_status"] = annotation_status_code
        return data

    def _build_copy_items_data(
            self,
            source_folder_id: int,
            destination_folder_id: int,
            item_names: List[str],
            include_annotations: bool,
            include_pin: bool,
    ) -> dict:
        """Build data payload for copying items"""
        return {
            "is_folder_copy": False,
            "image_names": item_names,
            "destination_folder_id": destination_folder_id,
            "source_folder_id": source_folder_id,
            "include_annotations": include_annotations,
            "keep_pin_status": include_pin,
        }

    def _build_copy_move_items_data(
            self,
            from_folder_id: int,
            to_folder_id: int,
            item_names: List[str],
            duplicate_strategy: Literal["skip", "replace", "replace_annotations_only"],
            operation: Literal["copy", "move"],
            include_annotations: bool,
            include_pin: bool,
    ) -> dict:
        """Build data payload for copy/move items"""
        duplicate_behaviour_map = {
            "skip": "skip_duplicates",
            "replace": "replace_all",
            "replace_annotations_only": "replace_annotation",
        }
        return {
            "is_folder_copy": False,
            "image_names": item_names,
            "destination_folder_id": to_folder_id,
            "source_folder_id": from_folder_id,
            "include_annotations": include_annotations,
            "keep_pin_status": include_pin,
            "duplicate_behaviour": duplicate_behaviour_map[duplicate_strategy],
            "operate_function": operation,
        }


class MonolithService(MonolithServiceBase, BaseSAServiceProvider):
    """Synchronous MonolithService"""

    def __init__(
        self,
        team_id: int,
        client: Client,
        service_url: Optional[str] = None,
        auth: Optional[Auth] = USE_CLIENT_DEFAULT,
    ):
        MonolithServiceBase.__init__(self, team_id, service_url, auth=auth)
        BaseSAServiceProvider.__init__(self, client)


    def create_project(self, payload) -> Response[ProjectEntity]:
        response = self.client.request(
            "get",
            url=urljoin(self._service_url, self.URL_PROJECTS),
            params={"team_id": self.team_id},
            data=payload,
            auth=self.auth,
        )
        return self.serialize_response(response, entity_cls=ProjectEntity)

    def update_project(self, project_id: int, payload) -> Response[ProjectEntity]:
        response = self.client.request(
            "put",
            url=urljoin(
                self._service_url, self.URL_PROJECTS_GET.format(project_id=project_id)
            ),
            params={"team_id": self.team_id},
            data=payload,
            auth=self.auth,
        )
        return self.serialize_response(response, entity_cls=ProjectEntity)

    def delete_project(self, project_id: int) -> Response:
        response = self.client.request(
            "delete",
            url=urljoin(
                self._service_url, self.URL_PROJECTS_GET.format(project_id=project_id)
            ),
            params={"team_id": self.team_id},
        )
        return self.serialize_response(response, entity_cls=dict)

    def list_settings(self, project_id: int) -> Response[dict]:
        return self.client.request(
            self.URL_SETTINGS.format(project_id=project_id),
            "get",
            params={"team_id": self.team_id},
            auth=self.auth,
        )

    async def set_settings(
        self, project_id: int, payload: list[dict]
    ) -> Response[dict]:
        return self.client.request(
            self.URL_SETTINGS.format(project_id=project_id),
            "get",
            params={"team_id": self.team_id},
            data=payload,
            auth=self.auth,
        )

    def get_folder_by_id(
            self, project_id: int, folder_id: int
    ) -> Response[FolderEntity]:
        params = {
            "team_id": self.team_id,
            "folder_id": folder_id,
            "project_id": project_id,
        }
        response = self.client.request(
            "get",
            url=urljoin(self._service_url, self.URL_GET_FOLDER_BY_ID),
            params=params,
        )
        return self.serialize_response(response, entity_cls=FolderEntity)

    def update_item(
            self, project_id: int, item_id: int, payload: dict
    ) -> Response[ItemEntity]:
        response = self.client.request(
            "put",
            url=urljoin(self._service_url, self.URL_GET_ITEM.format(item_id=item_id)),
            data=payload,
            params={"project_id": project_id},
        )
        return self.serialize_response(response, entity_cls=ItemEntity)

    def attach_items(
            self,
            project_id: int,
            folder_id: int,
            attachments: List[Attachment],
            upload_state_code,
            metadata: dict[str, AttachmentMeta],
            annotation_status_code=None,
    ) -> Response[dict]:
        data = self._build_attach_items_data(
            project_id,
            folder_id,
            attachments,
            upload_state_code,
            metadata,
            annotation_status_code,
        )
        response = self.client.request(
            "post", url=urljoin(self._service_url, self.URL_ATTACH_ITEM), data=data
        )
        return self.serialize_response(response, entity_cls=dict)

    def bulk_copy_items(
            self,
            project_id: int,
            source_folder_id: int,
            destination_folder_id: int,
            item_names: List[str],
            include_annotations: bool = False,
            include_pin: bool = False,
    ) -> Response[dict]:
        """
        Returns poll id.
        """
        data = self._build_copy_items_data(
            source_folder_id,
            destination_folder_id,
            item_names,
            include_annotations,
            include_pin,
        )
        response = self.client.request(
            "post",
            url=urljoin(self._service_url, self.URL_COPY_MULTIPLE_ITEMS),
            params={"project_id": project_id},
            data=data,
        )
        return self.serialize_response(response, entity_cls=dict)

    def await_copy(self, project_id: int, poll_id: int, items_count: int) -> None:
        await_time = items_count * 0.3
        timeout_start = time.time()
        while time.time() < timeout_start + await_time:
            response = self.client.request(
                self.URL_ITEM_COPY_PROGRESS,
                "get",
                params={"project_id": project_id, "poll_id": poll_id},
            )
            done_count, skipped, _ = self.serialize_response(response, entity_cls=dict)
            if done_count + skipped == items_count:
                break
            time.sleep(4)

    def bulk_move_items(
            self,
            project_id: int,
            from_folder_id: int,
            to_folder_id: int,
            item_names: List[str],
    ) -> Response[dict]:
        response = self.client.request(
            self.URL_MOVE_MULTIPLE_ITEM,
            "post",
            params={"project_id": project_id},
            data={
                "image_names": item_names,
                "destination_folder_id": to_folder_id,
                "source_folder_id": from_folder_id,
            },
        )
        return self.serialize_response(response, entity_cls=dict)

    def bulk_copy_move_items(
            self,
            project_id: int,
            from_folder_id: int,
            to_folder_id: int,
            item_names: List[str],
            duplicate_strategy: Literal["skip", "replace", "replace_annotations_only"],
            operation: Literal["copy", "move"],
            include_annotations: bool = True,
            include_pin: bool = False,
    ) -> Response[dict]:
        """
        Returns poll id.
        """
        data = self._build_copy_move_items_data(
            from_folder_id,
            to_folder_id,
            item_names,
            duplicate_strategy,
            operation,
            include_annotations,
            include_pin,
        )
        response = self.client.request(
            self.URL_COPY_MOVE_MULTIPLE_ITEM,
            "post",
            params={"project_id": project_id},
            data=data,
            auth=self.auth,
        )
        return self.serialize_response(response, entity_cls=dict)

    def get_copy_items_progress(self, project_id: int, poll_id: int) -> Response[list]:
        response = self.client.request(
            "get",
            url=urljoin(self._service_url, self.URL_ITEM_COPY_PROGRESS),
            params={"project_id": project_id, "poll_id": poll_id},
            auth=self.auth,
        )
        return self.serialize_response(response, entity_cls=list)

    def bulk_set_items_statuses(
            self,
            project_id: int,
            folder_id: int,
            item_names: List[str],
            annotation_status: int,
    ) -> Response[dict]:
        response = self.client.request(
            "put",
            url=urljoin(self._service_url, self.URL_SET_ITEM_ANNOTATION_STATUS_BULK),
            params={"project_id": project_id},
            data={
                "folder_id": folder_id,
                "annotation_status": annotation_status,
                "image_names": item_names,
            },
            auth=self.auth,
        )
        return self.serialize_response(response, entity_cls=dict)

    def set_item_status(
        self,
        project_id: int,
        folder_id: int,
        item_id: int,
        annotation_status: int,
    ) -> Response[dict]:
        response = self.client.request(
            "put",
            url=urljoin(
                self._service_url,
                self.URL_SET_ITEM_ANNOTATION_STATUS.format(item_id=item_id),
            ),
            params={
                "team_id": self.team_id,
                "project_id": project_id,
                "folder_id": folder_id,
            },
            data={"annotation_status": annotation_status},
            auth=self.auth,
        )
        return self.serialize_response(response, entity_cls=dict)

    def set_approval_items_statuses(
        self,
        project_id: int,
        folder_id: int,
        item_names: List[str],
        approval_status: int,
    ) -> Response[dict]:
        response = self.client.request(
            "post",
            url=urljoin(self._service_url, self.URL_SET_ITEM_APPROVAL_STATUSES),
            params={"project_id": project_id, "folder_id": folder_id},
            data={
                "item_names": item_names,
                "change_actions": {"APPROVAL_STATUS": approval_status},
            },
        )
        return self.serialize_response(response, entity_cls=dict)

    def bulk_delete_items(self, project_id: int, item_ids: List[int]) -> Response[dict]:
        response = self.client.request(
            "put",
            url=urljoin(self._service_url, self.URL_DELETE_ITEMS),
            params={"project_id": project_id},
            data={"image_ids": item_ids},
        )
        return self.serialize_response(response, entity_cls=dict)

    def bulk_attach_item_categories(
        self, project_id: int, folder_id: int, item_category_map: dict[int, int]
    ) -> Response[dict]:
        params = {"project_id": project_id, "folder_id": folder_id}
        response = self.client.request(
            "post",
            url=urljoin(self._service_url, self.URL_ATTACH_ITEM_CATEGORIES),
            params=params,
            data={
                "bulk": [
                    {"item_id": item_id, "categories": [category]}
                    for item_id, category in item_category_map.items()
                ]
            },
        )
        return self.serialize_response(response, entity_cls=dict)

    def list_folders(self, project_id: int) -> Response[FolderEntity]:
        return self.paginate(
            url=urljoin(self._service_url, self.URL_LIST_FOLDERS),
            query_params={"team_id": self.team_id, "project_id": project_id},
        )


class AsyncMonolithService(MonolithServiceBase, AsyncSAServiceProvider):
    """Asynchronous MonolithService"""

    def __init__(
        self,
        team_id: int,
        client: AsyncClient,
        service_url: Optional[str] = None,
        auth: Optional[Auth] = USE_CLIENT_DEFAULT,
    ):
        MonolithServiceBase.__init__(self, team_id, service_url, auth=auth)
        AsyncSAServiceProvider.__init__(self, client)

    async def create_project(self, payload) -> Response[ProjectEntity]:
        response = await self.client.request(
            "get",
            url=urljoin(self._service_url, self.URL_PROJECTS),
            params={"team_id": self.team_id},
            data=payload,
            auth=self.auth,
        )
        return self.serialize_response(response, entity_cls=ProjectEntity)

    async def update_project(self, project_id: int, payload) -> Response[ProjectEntity]:
        response = await self.client.request(
            "put",
            url=urljoin(
                self._service_url, self.URL_PROJECTS_GET.format(project_id=project_id)
            ),
            params={"team_id": self.team_id},
            data=payload,
            auth=self.auth,
        )
        return self.serialize_response(response, entity_cls=ProjectEntity)

    async def delete_project(self, project_id: int) -> Response:
        response = await self.client.request(
            "delete",
            url=urljoin(
                self._service_url, self.URL_PROJECTS_GET.format(project_id=project_id)
            ),
            params={"team_id": self.team_id},
            auth=self.auth,
        )
        return self.serialize_response(response, entity_cls=dict)

    async def list_settings(self, project_id: int) -> Response[dict]:
        return await self.client.request(
            self.URL_SETTINGS.format(project_id=project_id),
            "get",
            params={"team_id": self.team_id},
            auth=self.auth,
        )

    async def set_settings(
        self, project_id: int, payload: list[dict]
    ) -> Response[dict]:
        return await self.client.request(
            self.URL_SETTINGS.format(project_id=project_id),
            "get",
            params={"team_id": self.team_id},
            data=payload,  # noqa
            auth=self.auth,
        )

    async def get_folder(
            self, project_id: int, folder_id: int
    ) -> Response[FolderEntity]:
        params = {
            "team_id": self.team_id,
            "folder_id": folder_id,
            "project_id": project_id,
        }
        response = await self.client.request(
            "get",
            url=urljoin(self._service_url, self.URL_GET_FOLDER_BY_ID),
            params=params,
            auth=self.auth,
        )
        return self.serialize_response(response, entity_cls=FolderEntity)

    async def update_item(
            self, project_id: int, item_id: int, payload: dict
    ) -> Response[ItemEntity]:
        response = await self.client.request(
            "put",
            url=urljoin(self._service_url, self.URL_GET_ITEM.format(item_id=item_id)),
            data=payload,
            params={"project_id": project_id},
            auth=self.auth,
        )
        return self.serialize_response(response, entity_cls=ItemEntity)

    async def attach_items(
        self,
        project_id: int,
        folder_id: int,
        attachments: List[Attachment],
        upload_state_code,
        metadata: dict[str, AttachmentMeta],
        annotation_status_code=None,
    ) -> Response[dict]:
        data = self._build_attach_items_data(
            project_id,
            folder_id,
            attachments,
            upload_state_code,
            metadata,
            annotation_status_code,
        )
        response = await self.client.request(
            "post",
            url=urljoin(self._service_url, self.URL_ATTACH_ITEM),
            data=data,
            auth=self.auth,
        )
        return self.serialize_response(response, entity_cls=dict)

    async def bulk_copy_items(
            self,
            project_id: int,
            source_folder_id: int,
            destination_folder_id: int,
            item_names: List[str],
            include_annotations: bool = False,
            include_pin: bool = False,
    ) -> Response[dict]:
        """
        Returns poll id.
        """
        data = self._build_copy_items_data(
            source_folder_id,
            destination_folder_id,
            item_names,
            include_annotations,
            include_pin,
        )
        response = await self.client.request(
            "post",
            url=urljoin(self._service_url, self.URL_COPY_MULTIPLE_ITEMS),
            params={"project_id": project_id},
            data=data,
            auth=self.auth,
        )
        return self.serialize_response(response, entity_cls=dict)

    async def await_copy(self, project_id: int, poll_id: int, items_count: int) -> None:
        await_time = items_count * 0.3
        timeout_start = time.time()
        while time.time() < timeout_start + await_time:
            response = await self.client.request(
                self.URL_ITEM_COPY_PROGRESS,
                "get",
                params={"project_id": project_id, "poll_id": poll_id},
                auth=self.auth,
            )
            done_count, skipped, _ = self.serialize_response(response, entity_cls=dict)
            if done_count + skipped == items_count:
                break
            await asyncio.sleep(4)

    async def bulk_move_items(
        self,
        project_id: int,
        from_folder_id: int,
        to_folder_id: int,
        item_names: List[str],
    ) -> Response[dict]:
        response = await self.client.request(
            self.URL_MOVE_MULTIPLE_ITEM,
            "post",
            params={"project_id": project_id},
            data={
                "image_names": item_names,
                "destination_folder_id": to_folder_id,
                "source_folder_id": from_folder_id,
            },
            auth=self.auth,
        )
        return self.serialize_response(response, entity_cls=dict)

    async def bulk_copy_move_items(
        self,
        project_id: int,
        from_folder_id: int,
        to_folder_id: int,
        item_names: List[str],
        duplicate_strategy: Literal["skip", "replace", "replace_annotations_only"],
        operation: Literal["copy", "move"],
        include_annotations: bool = True,
        include_pin: bool = False,
    ) -> Response[dict]:
        """
        Returns poll id.
        """
        data = self._build_copy_move_items_data(
            from_folder_id,
            to_folder_id,
            item_names,
            duplicate_strategy,
            operation,
            include_annotations,
            include_pin,
        )
        response = await self.client.request(
            self.URL_COPY_MOVE_MULTIPLE_ITEM,
            "post",
            params={"project_id": project_id},
            data=data,
            auth=self.auth,
        )
        return self.serialize_response(response, entity_cls=dict)

    async def get_copy_items_progress(
        self, project_id: int, poll_id: int
    ) -> Response[list]:
        response = await self.client.request(
            "get",
            url=urljoin(self._service_url, self.URL_ITEM_COPY_PROGRESS),
            params={"project_id": project_id, "poll_id": poll_id},
        )
        return self.serialize_response(response, entity_cls=list)

    async def bulk_set_items_statuses(
        self,
        project_id: int,
        folder_id: int,
        item_names: List[str],
        annotation_status: int,
    ) -> Response[dict]:
        response = await self.client.request(
            "put",
            url=urljoin(self._service_url, self.URL_SET_ITEM_ANNOTATION_STATUS_BULK),
            params={"project_id": project_id},
            data={
                "folder_id": folder_id,
                "annotation_status": annotation_status,
                "image_names": item_names,
            },
            auth=self.auth,
        )
        return self.serialize_response(response, entity_cls=dict)

    async def set_item_status(
        self,
        project_id: int,
        folder_id: int,
        item_id: int,
        annotation_status: int,
    ) -> Response[dict]:
        response = await self.client.request(
            method="put",
            url=urljoin(
                self._service_url,
                self.URL_SET_ITEM_ANNOTATION_STATUS.format(item_id=item_id),
            ),
            params={
                "team_id": self.team_id,
                "project_id": project_id,
                "folder_id": folder_id,
            },
            json={"annotation_status": annotation_status},
            auth=self.auth,
        )
        return self.serialize_response(response, entity_cls=dict)

    async def set_approval_items_statuses(
            self,
            project_id: int,
            folder_id: int,
            item_names: List[str],
            approval_status: int,
    ) -> Response[dict]:
        response = await self.client.request(
            "post",
            url=urljoin(self._service_url, self.URL_SET_ITEM_APPROVAL_STATUSES),
            params={"project_id": project_id, "folder_id": folder_id},
            data={
                "item_names": item_names,
                "change_actions": {"APPROVAL_STATUS": approval_status},
            },
            auth=self.auth,
        )
        return self.serialize_response(response, entity_cls=dict)

    async def bulk_delete_items(
            self, project_id: int, item_ids: List[int]
    ) -> Response[dict]:
        response = await self.client.request(
            "put",
            url=urljoin(self._service_url, self.URL_DELETE_ITEMS),
            params={"project_id": project_id},
            data={"image_ids": item_ids},
            auth=self.auth,
        )
        return self.serialize_response(response, entity_cls=dict)

    async def bulk_attach_item_categories(
            self, project_id: int, folder_id: int, item_category_map: dict[int, int]
    ) -> Response[dict]:
        params = {"project_id": project_id, "folder_id": folder_id}
        response = await self.client.request(
            "post",
            url=urljoin(self._service_url, self.URL_ATTACH_ITEM_CATEGORIES),
            params=params,
            data={
                "bulk": [
                    {"item_id": item_id, "categories": [category]}
                    for item_id, category in item_category_map.items()
                ]
            },
            auth=self.auth,
        )
        return self.serialize_response(response, entity_cls=dict)

    async def list_folders(
            self,
            project_id: Optional[int] = None,
            condition: Condition = None,
    ) -> Response[FolderEntity]:
        if not project_id and not condition:
            raise ValueError("Either project_id or condition must be provided")

        if project_id and not condition:
            query_params = {"team_id": self.team_id, "project_id": project_id}
        else:
            query_params = condition.get_as_params_dict()
        return await self.paginate(
            url=urljoin(self._service_url, self.URL_LIST_FOLDERS),
            query_params=query_params,
            auth=self.auth,
        )
