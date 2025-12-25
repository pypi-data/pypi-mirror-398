import logging
import os
from typing import Optional
from urllib.parse import urljoin

import httpx
from httpx import AsyncClient
from httpx import Client
from httpx import USE_CLIENT_DEFAULT
from sapure.services.base.entities import ItemEntity
from sapure.services.base.service_provider import AsyncSAServiceProvider
from sapure.services.base.service_provider import BaseSAServiceProvider
from sapure.services.base.service_provider import Response
from sapure.services.filters import Query
from sapure.services.utils import generate_context
from sapure.services.utils import join_url

logger = logging.getLogger("__file__")


class ItemServiceBase:
    """Base class with shared logic for ItemService"""

    URL_LIST = "items/search"
    URL_GET = "items/{item_id}"

    def __init__(
        self,
        team_id: int,
        service_url: Optional[str] = None,
        auth: Optional[httpx.Auth] = USE_CLIENT_DEFAULT,
    ):
        self.team_id = team_id
        self.auth = auth
        self._service_url = (
            service_url
            if service_url
            else join_url(os.environ["SA_ITEM_SERVICE_URL"], "api/v1/")
        )

    def _get_url(self, item_id: int) -> str:
        """Build URL for getting a single item"""
        return urljoin(self._service_url, self.URL_GET.format(item_id=item_id))

    def _get_list_url(self) -> str:
        """Build URL for listing items"""
        return urljoin(self._service_url, self.URL_LIST)

    def _get_headers(self, project_id: int, folder_id: Optional[int] = None) -> dict:
        """Build headers with entity context"""
        entity_context = {
            "team_id": self.team_id,
            "project_id": project_id,
        }
        if folder_id:
            entity_context["folder_id"] = folder_id
        return {"x-sa-entity-context": generate_context(**entity_context)}


class ItemService(ItemServiceBase, BaseSAServiceProvider):
    """Synchronous ItemService"""

    def __init__(
        self,
        team_id: int,
        client: Client,
        service_url: Optional[str] = None,
        auth: Optional[httpx.Auth] = USE_CLIENT_DEFAULT,
    ):
        ItemServiceBase.__init__(self, team_id, service_url, auth=auth)
        BaseSAServiceProvider.__init__(self, client)

    def get(self, project_id: int, item_id: int) -> Response[ItemEntity]:
        response = self.client.request(
            url=self._get_url(item_id),
            method="GET",
            headers=self._get_headers(project_id),
            auth=self.auth,
        )
        return self.serialize_response(response, entity_cls=ItemEntity)

    def list(
        self,
        project_id: int,
        query: Query,
        folder_id: Optional[int] = None,
        chunk_size: int = 200,
    ) -> Response[ItemEntity]:
        response = self.jsx_paginate(
            url=self._get_list_url(),
            method="post",
            headers=self._get_headers(project_id, folder_id),
            chunk_size=chunk_size,
            body_query=query,
            entity_cls=ItemEntity,
            auth=self.auth,
        )
        return response


class AsyncItemService(ItemServiceBase, AsyncSAServiceProvider):
    """Asynchronous ItemService"""

    def __init__(
        self,
        team_id: int,
        client: AsyncClient,
        service_url: Optional[str] = None,
        auth: Optional[httpx.Auth] = USE_CLIENT_DEFAULT,
    ):
        ItemServiceBase.__init__(self, team_id, service_url, auth=auth)
        AsyncSAServiceProvider.__init__(self, client)

    async def get(self, project_id: int, item_id: int) -> Response[ItemEntity]:
        response = await self.client.request(
            url=self._get_url(item_id),
            method="GET",
            headers=self._get_headers(project_id),
            auth=self.auth,
        )
        return self.serialize_response(response, entity_cls=ItemEntity)

    async def list(
        self,
        project_id: int,
        query: Query,
        folder_id: Optional[int] = None,
        chunk_size: int = 200,
    ) -> Response[ItemEntity]:
        response = await self.jsx_paginate(
            url=self._get_list_url(),
            method="post",
            headers=self._get_headers(project_id, folder_id),
            chunk_size=chunk_size,
            body_query=query,
            entity_cls=ItemEntity,
            auth=self.auth,
        )
        return response
