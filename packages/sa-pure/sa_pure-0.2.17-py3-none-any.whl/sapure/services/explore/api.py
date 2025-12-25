import logging
import os
from collections import ChainMap
from typing import Dict
from typing import List
from typing import Optional
from urllib.parse import urljoin

from httpx import AsyncClient
from httpx import Client
from sapure.services.base.service_provider import AsyncSAServiceProvider
from sapure.services.base.service_provider import BaseSAServiceProvider
from sapure.services.base.service_provider import Response
from sapure.services.explore.conditions import Condition

logger = logging.getLogger("__file__")


class ExploreServiceBase:
    """Base class with shared logic for ExploreService"""

    MAX_ITEMS_COUNT = 50_1000
    CHUNK_SIZE = 5_000
    SAQUL_CHUNK_SIZE = 50

    URL_SUBSET = "subsets"
    URL_LIST_CUSTOM_FIELDS = "custom/metadata/item/value"
    URL_ADD_ITEMS_TO_SUBSET = "subsets/change"
    URL_CUSTOM_SCHEMA = "custom/metadata/schema"
    URL_UPLOAD_CUSTOM_VALUE = "custom/metadata/item"
    URL_SAQUL_QUERY = "items/search"
    URL_VALIDATE_SAQUL_QUERY = "items/parse/query"
    URL_QUERY_COUNT = "items/count"

    def __init__(self, team_id: int, service_url: Optional[str] = None):
        self.team_id = team_id
        self._service_url = service_url or os.environ["EXPLORE_SERVICE_URL"]

    def _build_saqul_query_params(
        self, project_id: int, folder_id: int = None, subset_id: int = None
    ) -> dict:
        """Build query parameters for SAQUL query"""
        params = {
            "project_id": project_id,
            "includeFolderNames": True,
        }
        if folder_id:
            params["folder_id"] = folder_id
        if subset_id:
            params["subset_id"] = subset_id
        return params


class ExploreService(ExploreServiceBase, BaseSAServiceProvider):
    """Synchronous ExploreService"""

    def __init__(self, team_id: int, client: Client, service_url: Optional[str] = None):
        ExploreServiceBase.__init__(self, team_id, service_url)
        BaseSAServiceProvider.__init__(self, client)

    def create_schema(self, project_id: int, schema: dict) -> Response[dict]:
        response = self.client.request(
            url=urljoin(self._service_url, self.URL_CUSTOM_SCHEMA),
            method="post",
            params={"project_id": project_id},
            data=dict(data=schema),
        )
        return self.serialize_response(response, entity_cls=dict)

    def get_schema(self, project_id: int) -> Response[dict]:
        response = self.client.request(
            url=urljoin(self._service_url, self.URL_CUSTOM_SCHEMA),
            method="get",
            params={"project_id": project_id},
        )
        return self.serialize_response(response, entity_cls=dict)

    def delete_fields(self, project_id: int, fields: List[str]) -> Response[dict]:
        response = self.client.request(
            url=urljoin(self._service_url, self.URL_CUSTOM_SCHEMA),
            method="delete",
            params={"project_id": project_id},
            data=dict(custom_fields=fields),
        )
        return self.serialize_response(response, entity_cls=dict)

    def upload_fields(
        self,
        project_id: int,
        folder_id: int,
        items: List[dict],
    ) -> Response[dict]:
        response = self.client.request(
            url=urljoin(self._service_url, self.URL_UPLOAD_CUSTOM_VALUE),
            method="post",
            params={"project_id": project_id, "folder_id": folder_id},
            data=dict(data=dict(ChainMap(*items))),
        )
        return self.serialize_response(response, entity_cls=dict)

    def delete_values(
        self,
        project_id: int,
        folder_id: int,
        items: List[Dict[str, List[str]]],
    ) -> Response[dict]:
        response = self.client.request(
            url=urljoin(self._service_url, self.URL_UPLOAD_CUSTOM_VALUE),
            method="delete",
            params={"project_id": project_id, "folder_id": folder_id},
            data=dict(data=dict(ChainMap(*items))),
        )
        return self.serialize_response(response, entity_cls=dict)

    def list_fields(self, project_id: int, item_ids: List[int]) -> Response[list]:
        assert len(item_ids) <= self.CHUNK_SIZE
        response = self.client.request(
            url=urljoin(self._service_url, self.URL_LIST_CUSTOM_FIELDS),
            method="POST",
            params={"project_id": project_id},
            data={
                "item_id": item_ids,
            },
        )
        return self.serialize_response(response, entity_cls=list)

    def list_subsets(
        self, project_id: int, condition: Condition = None
    ) -> Response[list]:
        url = urljoin(self._service_url, self.URL_SUBSET)
        return self.paginate(
            url=f"{url}?{condition.build_query()}" if condition else url,
            query_params={"project_id": project_id},
            entity_cls=list,
        )

    def create_multiple_subsets(
        self, project_id: int, name: List[str]
    ) -> Response[list]:
        response = self.client.request(
            method="POST",
            url=urljoin(self._service_url, self.URL_SUBSET),
            params={"project_id": project_id},
            data={"names": name},
        )
        return self.serialize_response(response, entity_cls=dict)

    def add_items_to_subset(
        self,
        project_id: int,
        subset_id: int,
        item_ids: List[int],
    ) -> Response[dict]:
        data = {"action": "ATTACH", "item_ids": item_ids}
        response = self.client.request(
            url=urljoin(self._service_url, self.URL_ADD_ITEMS_TO_SUBSET),
            method="POST",
            params={"project_id": project_id, "subset_id": subset_id},
            data=data,
        )
        return self.serialize_response(response, entity_cls=dict)

    def validate_saqul_query(self, project_id: int, query: str) -> Response[dict]:
        params = {
            "project_id": project_id,
        }
        data = {
            "query": query,
        }
        response = self.client.request(
            urljoin(self._service_url, self.URL_VALIDATE_SAQUL_QUERY),
            "post",
            params=params,
            data=data,
        )
        return self.serialize_response(response, entity_cls=dict)

    def saqul_query(
        self,
        project_id: int,
        folder_id: int = None,
        query: str = None,
        subset_id: int = None,
    ) -> Response[list]:
        params = self._build_saqul_query_params(project_id, folder_id, subset_id)
        data = {"image_index": 0}
        if query:
            data["query"] = query
        items = []
        for _ in range(0, self.MAX_ITEMS_COUNT, self.SAQUL_CHUNK_SIZE):
            response = self.client.request(
                urljoin(self._service_url, self.URL_SAQUL_QUERY),
                "post",
                params=params,
                data=data,
            )
            response.raise_for_status()
            response_items = response.json()
            items.extend(response_items)
            if len(response_items) < self.SAQUL_CHUNK_SIZE:
                break
            data["image_index"] += self.SAQUL_CHUNK_SIZE
        return Response[list](data=items)

    def query_item_count(
        self,
        project_id: int,
        query: str = None,
    ) -> Response[dict]:
        params = {
            "project_id": project_id,
            "includeFolderNames": True,
        }
        data = {"query": query}
        response = self.client.request(
            urljoin(self._service_url, self.URL_QUERY_COUNT),
            "post",
            params=params,
            data=data,
        )
        return self.serialize_response(response, entity_cls=dict)


class AsyncExploreService(ExploreServiceBase, AsyncSAServiceProvider):
    """Asynchronous ExploreService"""

    def __init__(
        self, team_id: int, client: AsyncClient, service_url: Optional[str] = None
    ):
        ExploreServiceBase.__init__(self, team_id, service_url)
        AsyncSAServiceProvider.__init__(self, client)

    async def create_schema(self, project_id: int, schema: dict) -> Response[dict]:
        response = await self.client.request(
            url=urljoin(self._service_url, self.URL_CUSTOM_SCHEMA),
            method="post",
            params={"project_id": project_id},
            data=dict(data=schema),
        )
        return self.serialize_response(response, entity_cls=dict)

    async def get_schema(self, project_id: int) -> Response[dict]:
        response = await self.client.request(
            url=urljoin(self._service_url, self.URL_CUSTOM_SCHEMA),
            method="get",
            params={"project_id": project_id},
        )
        return self.serialize_response(response, entity_cls=dict)

    async def delete_fields(self, project_id: int, fields: List[str]) -> Response[dict]:
        response = await self.client.request(
            url=urljoin(self._service_url, self.URL_CUSTOM_SCHEMA),
            method="delete",
            params={"project_id": project_id},
            data=dict(custom_fields=fields),
        )
        return self.serialize_response(response, entity_cls=dict)

    async def upload_fields(
        self,
        project_id: int,
        folder_id: int,
        items: List[dict],
    ) -> Response[dict]:
        response = await self.client.request(
            url=urljoin(self._service_url, self.URL_UPLOAD_CUSTOM_VALUE),
            method="post",
            params={"project_id": project_id, "folder_id": folder_id},
            data=dict(data=dict(ChainMap(*items))),
        )
        return self.serialize_response(response, entity_cls=dict)

    async def delete_values(
        self,
        project_id: int,
        folder_id: int,
        items: List[Dict[str, List[str]]],
    ) -> Response[dict]:
        response = await self.client.request(
            url=urljoin(self._service_url, self.URL_UPLOAD_CUSTOM_VALUE),
            method="delete",
            params={"project_id": project_id, "folder_id": folder_id},
            data=dict(data=dict(ChainMap(*items))),
        )
        return self.serialize_response(response, entity_cls=dict)

    async def list_fields(self, project_id: int, item_ids: List[int]) -> Response[list]:
        assert len(item_ids) <= self.CHUNK_SIZE
        response = await self.client.request(
            url=urljoin(self._service_url, self.URL_LIST_CUSTOM_FIELDS),
            method="POST",
            params={"project_id": project_id},
            data={
                "item_id": item_ids,
            },
        )
        return self.serialize_response(response, entity_cls=list)

    async def list_subsets(
        self, project_id: int, condition: Condition = None
    ) -> Response[list]:
        url = urljoin(self._service_url, self.URL_SUBSET)
        return await self.paginate(
            url=f"{url}?{condition.build_query()}" if condition else url,
            query_params={"project_id": project_id},
            entity_cls=list,
        )

    async def create_multiple_subsets(
        self, project_id: int, name: List[str]
    ) -> Response[list]:
        response = await self.client.request(
            method="POST",
            url=urljoin(self._service_url, self.URL_SUBSET),
            params={"project_id": project_id},
            data={"names": name},
        )
        return self.serialize_response(response, entity_cls=dict)

    async def add_items_to_subset(
        self,
        project_id: int,
        subset_id: int,
        item_ids: List[int],
    ) -> Response[dict]:
        data = {"action": "ATTACH", "item_ids": item_ids}
        response = await self.client.request(
            url=urljoin(self._service_url, self.URL_ADD_ITEMS_TO_SUBSET),
            method="POST",
            params={"project_id": project_id, "subset_id": subset_id},
            data=data,
        )
        return self.serialize_response(response, entity_cls=dict)

    async def validate_saqul_query(self, project_id: int, query: str) -> Response[dict]:
        params = {
            "project_id": project_id,
        }
        data = {
            "query": query,
        }
        response = await self.client.request(
            urljoin(self._service_url, self.URL_VALIDATE_SAQUL_QUERY),
            "post",
            params=params,
            data=data,
        )
        return self.serialize_response(response, entity_cls=dict)

    async def saqul_query(
        self,
        project_id: int,
        folder_id: int = None,
        query: str = None,
        subset_id: int = None,
    ) -> Response[list]:
        params = self._build_saqul_query_params(project_id, folder_id, subset_id)
        data = {"image_index": 0}
        if query:
            data["query"] = query
        items = []
        for _ in range(0, self.MAX_ITEMS_COUNT, self.SAQUL_CHUNK_SIZE):
            response = await self.client.request(
                urljoin(self._service_url, self.URL_SAQUL_QUERY),
                "post",
                params=params,
                data=data,
            )
            response.raise_for_status()
            response_items = response.json()
            items.extend(response_items)
            if len(response_items) < self.SAQUL_CHUNK_SIZE:
                break
            data["image_index"] += self.SAQUL_CHUNK_SIZE
        return Response[list](data=items)

    async def query_item_count(
        self,
        project_id: int,
        query: str = None,
    ) -> Response[dict]:
        params = {
            "project_id": project_id,
            "includeFolderNames": True,
        }
        data = {"query": query}
        response = await self.client.request(
            urljoin(self._service_url, self.URL_QUERY_COUNT),
            "post",
            params=params,
            data=data,
        )
        return self.serialize_response(response, entity_cls=dict)
