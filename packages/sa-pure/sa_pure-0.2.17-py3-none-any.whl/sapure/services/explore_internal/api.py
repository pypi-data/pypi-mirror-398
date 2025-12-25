import logging
import os
from typing import Optional
from urllib.parse import urljoin

from httpx import AsyncClient
from httpx import Client
from sapure.services.base.service_provider import AsyncSAServiceProvider
from sapure.services.base.service_provider import BaseSAServiceProvider
from sapure.services.base.service_provider import Response

logger = logging.getLogger("__file__")


class ExploreInternalServiceBase:
    """Base class with shared logic for ExploreInternalService"""

    URL_GET_ITEM_IDS_BY_QUERY = "internal/query/item/ids"

    def __init__(self, team_id: int, service_url: Optional[str] = None):
        self.team_id = team_id
        self._service_url = service_url or os.environ["EXPLORE_SERVICE_URL"]

    def _build_query_params(
        self,
        project_id: int,
        project_type: int,
        folder_ids: list[int] = None,
        subset_id: int = None,
    ) -> dict:
        """Build query parameters for item IDs query"""
        params = {
            "project_id": project_id,
            "project_type": project_type,
        }
        if folder_ids:
            params["folder_id"] = folder_ids[0]
        if subset_id:
            params["subset_id"] = subset_id
        return params

    def _build_query_data(self, query: str = None) -> dict:
        """Build data payload for item IDs query"""
        data = {}
        if query:
            data["query"] = query
        return data


class ExploreInternalService(ExploreInternalServiceBase, BaseSAServiceProvider):
    """Synchronous ExploreInternalService"""

    def __init__(self, team_id: int, client: Client, service_url: Optional[str] = None):
        ExploreInternalServiceBase.__init__(self, team_id, service_url)
        BaseSAServiceProvider.__init__(self, client)

    def get_item_ids_by_query(
        self,
        project_id: int,
        project_type: int,
        query: str = None,
        folder_ids: list[int] = None,
        subset_id: int = None,
        chunk_size: int = 2000,
    ) -> Response[list]:
        params = self._build_query_params(
            project_id, project_type, folder_ids, subset_id
        )
        data = self._build_query_data(query)

        return self.paginate_post(
            base_body=data,
            url=urljoin(self._service_url, self.URL_GET_ITEM_IDS_BY_QUERY),
            query_params=params,
            entity_cls=list,
            chunk_size=chunk_size,
        )


class AsyncExploreInternalService(ExploreInternalServiceBase, AsyncSAServiceProvider):
    """Asynchronous ExploreInternalService"""

    def __init__(
        self, team_id: int, client: AsyncClient, service_url: Optional[str] = None
    ):
        ExploreInternalServiceBase.__init__(self, team_id, service_url)
        AsyncSAServiceProvider.__init__(self, client)

    async def get_item_ids_by_query(
        self,
        project_id: int,
        project_type: int,
        query: str = None,
        folder_ids: list[int] = None,
        subset_id: int = None,
        chunk_size: int = 2000,
    ) -> Response[list]:
        params = self._build_query_params(
            project_id, project_type, folder_ids, subset_id
        )
        data = self._build_query_data(query)

        return await self.paginate_post(
            base_body=data,
            url=urljoin(self._service_url, self.URL_GET_ITEM_IDS_BY_QUERY),
            query_params=params,
            entity_cls=list,
            chunk_size=chunk_size,
        )
