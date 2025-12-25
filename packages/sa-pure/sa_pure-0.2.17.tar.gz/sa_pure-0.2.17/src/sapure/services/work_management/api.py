import base64
import os
from dataclasses import dataclass
from typing import Literal
from typing import Optional
from urllib.parse import urljoin

import httpx
from httpx import AsyncClient
from httpx import USE_CLIENT_DEFAULT
from sapure.enums import CustomFieldEntityEnum
from sapure.services.base.entities import BaseEntity
from sapure.services.base.entities import ProjectEntity
from sapure.services.base.service_provider import AsyncSAServiceProvider
from sapure.services.base.service_provider import BaseSAServiceProvider
from sapure.services.base.service_provider import Response
from sapure.services.filters import Filter
from sapure.services.filters import Query
from sapure.services.utils import generate_context
from sapure.services.utils import join_url
from sapure.services.work_management.entities import CustomRoleEntity
from sapure.services.work_management.entities import CustomStatusEntity
from sapure.services.work_management.entities import ItemCategory
from sapure.services.work_management.entities import WMUserEntity
from sapure.services.work_management.entities import WorkflowEntity


@dataclass
class EntitySpec:
    entity: CustomFieldEntityEnum
    parent_entity: CustomFieldEntityEnum


def prepare_validation_error(func):
    def wrapper(*args, **kwargs):
        res = func(*args, **kwargs)
        if res.error and isinstance(res.error, list):
            if res.error[0].get("code") == "VALIDATION_ERROR":
                error_types_map = {
                    "Array": "list",
                    "string": "str",
                    "number": "numeric",
                }
                valid_types = res.error[0]["details"]["valid_types"]
                prepared_valid_types = [error_types_map.get(i, i) for i in valid_types]
                error_msg = (
                    f"Invalid input: The provided value is not valid.\n"
                    f"Expected type: {' or '.join(prepared_valid_types)}."
                )
                expected_values = res.error[0]["details"].get("expected_values")
                if expected_values:
                    error_msg += f"\nValid options are: {', '.join(expected_values)}."
                res.res_error = error_msg
        res.raise_for_status()

    return wrapper


class WorkflowsServiceBase:
    """Base class with shared logic for WorkflowsService"""

    URL_LIST = "workflows"
    URL_LIST_STATUSES = "workflows/{workflow_id}/workflowstatuses"
    URL_LIST_ROLES = "workflows/{workflow_id}/workflowroles"

    def __init__(
        self,
        team_id: int,
        service_url: str,
        auth: Optional[httpx.Auth] = USE_CLIENT_DEFAULT,
    ):
        self.team_id = team_id
        self._service_url = service_url
        self.auth = auth


class WorkflowsService(WorkflowsServiceBase, BaseSAServiceProvider):
    """Synchronous WorkflowsService"""

    def __init__(
        self,
        client: httpx.Client,
        team_id: int,
        service_url: str,
        auth: Optional[httpx.Auth] = USE_CLIENT_DEFAULT,
    ):
        WorkflowsServiceBase.__init__(self, team_id, service_url, auth=auth)
        BaseSAServiceProvider.__init__(self, client)

    def list_statuses(self, project_id: int, workflow_id: int):
        return self.serialize_response(
            self.client.request(
                url=urljoin(
                    self._service_url,
                    self.URL_LIST_STATUSES.format(workflow_id=workflow_id),
                ),
                method="get",
                headers={
                    "x-sa-entity-context": generate_context(
                        team_id=self.team_id, project_id=project_id
                    )
                },
                params={
                    "join": "status",
                },
                auth=self.auth,
            )
        )

    def list_roles(self, project_id: int, workflow_id: int):
        return self.client.request(
            url=urljoin(
                self._service_url, self.URL_LIST_ROLES.format(workflow_id=workflow_id)
            ),
            method="get",
            headers={
                "x-sa-entity-context": generate_context(
                    team_id=self.team_id, project_id=project_id
                )
            },
            params={
                "join": "role",
            },
            auth=self.auth,
        )

    def list(self, query: Query) -> Response[list[WorkflowEntity]]:
        return self.paginate(
            url=urljoin(self._service_url, f"{self.URL_LIST}?{query.build_query()}"),
            headers={"x-sa-entity-context": generate_context(team_id=self.team_id)},
            entity_cls=list[WorkflowEntity],
            auth=self.auth,
        )

    def create(self, data: dict) -> Response[WorkflowEntity]:
        response = self.client.post(
            url=urljoin(self._service_url, self.URL_LIST),
            json=data,
            headers={"x-sa-entity-context": generate_context(team_id=self.team_id)},
            auth=self.auth,
        )
        return self.serialize_response(response, entity_cls=WorkflowEntity)


class AsyncWorkflowsService(WorkflowsServiceBase, AsyncSAServiceProvider):
    """Asynchronous WorkflowsService"""

    def __init__(
        self,
        client: AsyncClient,
        team_id: int,
        service_url: str,
        auth: Optional[httpx.Auth] = USE_CLIENT_DEFAULT,
    ):
        WorkflowsServiceBase.__init__(self, team_id, service_url, auth=auth)
        AsyncSAServiceProvider.__init__(self, client)

    async def list_statuses(self, project_id: int, workflow_id: int):
        return self.serialize_response(
            await self.client.request(
                url=urljoin(
                    self._service_url,
                    self.URL_LIST_STATUSES.format(workflow_id=workflow_id),
                ),
                method="get",
                headers={
                    "x-sa-entity-context": generate_context(
                        team_id=self.team_id, project_id=project_id
                    )
                },
                params={
                    "join": "status",
                },
                auth=self.auth,
            )
        )

    async def list_roles(self, project_id: int, workflow_id: int):
        return await self.client.request(
            url=urljoin(
                self._service_url, self.URL_LIST_ROLES.format(workflow_id=workflow_id)
            ),
            method="get",
            headers={
                "x-sa-entity-context": generate_context(
                    team_id=self.team_id, project_id=project_id
                )
            },
            params={
                "join": "role",
            },
            auth=self.auth,
        )

    async def list(self, query: Query) -> Response[list[WorkflowEntity]]:
        return await self.paginate(
            url=urljoin(self._service_url, f"{self.URL_LIST}?{query.build_query()}"),
            headers={"x-sa-entity-context": generate_context(team_id=self.team_id)},
            entity_cls=list[WorkflowEntity],
            auth=self.auth,
        )

    async def create(self, data: dict) -> Response[WorkflowEntity]:
        response = await self.client.post(
            url=urljoin(self._service_url, self.URL_LIST),
            json=data,
            headers={"x-sa-entity-context": generate_context(team_id=self.team_id)},
            auth=self.auth,
        )
        return self.serialize_response(response, entity_cls=WorkflowEntity)


class CategoriesServiceBase:
    """Base class with shared logic for CategoriesService"""

    URL_LIST_CATEGORIES = "categories"
    URL_RETRIEVE_CATEGORY = "categories/{category_id}"
    URL_CREATE_CATEGORIES = "categories/bulk"

    def __init__(
        self,
        team_id: int,
        service_url: str,
        auth: Optional[httpx.Auth] = USE_CLIENT_DEFAULT,
    ):
        self.team_id = team_id
        self._service_url = service_url
        self.auth = auth


class CategoriesService(CategoriesServiceBase, BaseSAServiceProvider):
    """Synchronous CategoriesService"""

    def __init__(
        self,
        client: httpx.Client,
        team_id: int,
        service_url: str,
        auth: Optional[httpx.Auth] = USE_CLIENT_DEFAULT,
    ):
        CategoriesServiceBase.__init__(self, team_id, service_url, auth=auth)
        BaseSAServiceProvider.__init__(self, client)

    def create(self, project_id: int, names: list[str]) -> Response[list[ItemCategory]]:
        response = self.client.post(
            url=urljoin(self._service_url, self.URL_CREATE_CATEGORIES),
            params={"team_id": self.team_id, "project_id": project_id},
            json={"bulk": [{"name": name} for name in names]},
            headers={
                "x-sa-entity-context": generate_context(
                    team_id=self.team_id, project_id=project_id
                )
            },
            auth=self.auth,
        )
        return self.serialize_response(response, entity_cls=ItemCategory)

    def list(
        self, project_id: int, user_id: str = None
    ) -> Response[list[ItemCategory]]:
        context = {"x-sa-entity-context": generate_context(team_id=self.team_id)}
        if user_id:
            context["x-sa-user-context"] = base64.b64encode(user_id.encode())
        return self.paginate(
            url=urljoin(self._service_url, self.URL_LIST_CATEGORIES),
            query_params={"project_id": project_id},
            headers=context,
            auth=self.auth,
        )

    def update(self, category_id: int, payload: dict) -> Response[dict]:
        response = self.client.patch(
            url=urljoin(
                self._service_url,
                self.URL_RETRIEVE_CATEGORY.format(category_id=category_id),
            ),
            params={"team_id": self.team_id},
            data=payload,
            auth=self.auth,
        )
        return self.serialize_response(response, entity_cls=dict)

    def get(self, category_id: int) -> Response[dict]:
        response = self.client.get(
            url=urljoin(
                self._service_url,
                self.URL_RETRIEVE_CATEGORY.format(category_id=category_id),
            ),
            params={"team_id": self.team_id},
            auth=self.auth,
        )
        return self.serialize_response(response, entity_cls=dict)

    def delete_categories(self, query: Filter) -> Response[dict]:
        response = self.client.delete(
            url=urljoin(
                self._service_url, f"{self.URL_CREATE_CATEGORIES}?{query.build_query()}"
            ),
            params={"team_id": self.team_id},
            headers={"x-sa-entity-context": generate_context(team_id=self.team_id)},
            auth=self.auth,
        )
        return self.serialize_response(response, entity_cls=dict)


class AsyncCategoriesService(CategoriesServiceBase, AsyncSAServiceProvider):
    """Asynchronous CategoriesService"""

    def __init__(
        self,
        client: AsyncClient,
        team_id: int,
        service_url: str,
        auth: Optional[httpx.Auth] = USE_CLIENT_DEFAULT,
    ):
        CategoriesServiceBase.__init__(self, team_id, service_url, auth=auth)
        AsyncSAServiceProvider.__init__(self, client)

    async def create(
        self, project_id: int, names: list[str]
    ) -> Response[list[ItemCategory]]:
        response = await self.client.post(
            url=urljoin(self._service_url, self.URL_CREATE_CATEGORIES),
            params={"team_id": self.team_id, "project_id": project_id},
            json={"bulk": [{"name": name} for name in names]},
            headers={
                "x-sa-entity-context": generate_context(
                    team_id=self.team_id, project_id=project_id
                )
            },
            auth=self.auth,
        )
        return self.serialize_response(response, entity_cls=ItemCategory)

    async def list(
        self, project_id: int, user_id: str = None
    ) -> Response[list[ItemCategory]]:
        context = {"x-sa-entity-context": generate_context(team_id=self.team_id)}
        if user_id:
            context["x-sa-user-context"] = base64.b64encode(user_id.encode())
        return await self.paginate(
            url=urljoin(self._service_url, self.URL_LIST_CATEGORIES),
            query_params={"project_id": project_id},
            headers=context,
            auth=self.auth,
        )

    async def update(self, category_id: int, payload: dict) -> Response[dict]:
        response = await self.client.patch(
            url=urljoin(
                self._service_url,
                self.URL_RETRIEVE_CATEGORY.format(category_id=category_id),
            ),
            params={"team_id": self.team_id},
            data=payload,
            auth=self.auth,
        )
        return self.serialize_response(response, entity_cls=dict)

    async def get(self, category_id: int) -> Response[dict]:
        response = await self.client.get(
            url=urljoin(
                self._service_url,
                self.URL_RETRIEVE_CATEGORY.format(category_id=category_id),
            ),
            params={"team_id": self.team_id},
            auth=self.auth,
        )
        return self.serialize_response(response, entity_cls=dict)

    async def delete_categories(self, query: Filter) -> Response[dict]:
        response = await self.client.delete(
            url=urljoin(
                self._service_url, f"{self.URL_CREATE_CATEGORIES}?{query.build_query()}"
            ),
            params={"team_id": self.team_id},
            headers={"x-sa-entity-context": generate_context(team_id=self.team_id)},
            auth=self.auth,
        )
        return self.serialize_response(response, entity_cls=dict)


class ScoresServiceBase:
    """Base class with shared logic for ScoresService"""

    URL_SCORES = "scores"
    URL_DELETE_SCORE = "scores/{score_id}"

    def __init__(
        self,
        team_id: int,
        service_url: str,
        auth: Optional[httpx.Auth] = USE_CLIENT_DEFAULT,
    ):
        self.team_id = team_id
        self._service_url = service_url
        self.auth = auth


class ScoresService(ScoresServiceBase, BaseSAServiceProvider):
    """Synchronous ScoresService"""

    def __init__(
        self,
        client: httpx.Client,
        team_id: int,
        service_url: str,
        auth: Optional[httpx.Auth] = USE_CLIENT_DEFAULT,
    ):
        ScoresServiceBase.__init__(self, team_id, service_url, auth=auth)
        BaseSAServiceProvider.__init__(self, client)

    def list(self) -> list[dict]:
        return self.paginate(
            url=urljoin(self._service_url, self.URL_SCORES),
            headers={"x-sa-entity-context": generate_context(team_id=self.team_id)},
            auth=self.auth,
        )

    def create(
        self, name: str, description: Optional[str], score_type: str, payload: dict
    ):
        data = {
            "name": name,
            "description": description,
            "type": score_type,
            "payload": payload,
        }
        return self.client.post(
            url=urljoin(self._service_url, self.URL_SCORES),
            data=data,
            headers={"x-sa-entity-context": generate_context(team_id=self.team_id)},
            auth=self.auth,
        )

    def delete(self, score_id: int):
        return self.client.delete(
            url=urljoin(
                self._service_url, self.URL_DELETE_SCORE.format(score_id=score_id)
            ),
            headers={"x-sa-entity-context": generate_context(team_id=self.team_id)},
            auth=self.auth,
        )


class AsyncScoresService(ScoresServiceBase, AsyncSAServiceProvider):
    """Asynchronous ScoresService"""

    def __init__(
        self,
        client: AsyncClient,
        team_id: int,
        service_url: str,
        auth: Optional[httpx.Auth] = USE_CLIENT_DEFAULT,
    ):
        ScoresServiceBase.__init__(self, team_id, service_url, auth=auth)
        AsyncSAServiceProvider.__init__(self, client)

    async def list(self) -> list[dict]:
        return await self.paginate(
            url=urljoin(self._service_url, self.URL_SCORES),
            headers={"x-sa-entity-context": generate_context(team_id=self.team_id)},
            auth=self.auth,
        )

    async def create(
        self, name: str, description: Optional[str], score_type: str, payload: dict
    ):
        data = {
            "name": name,
            "description": description,
            "type": score_type,
            "payload": payload,
        }
        return await self.client.post(
            url=urljoin(self._service_url, self.URL_SCORES),
            data=data,
            headers={"x-sa-entity-context": generate_context(team_id=self.team_id)},
            auth=self.auth,
        )

    async def delete(self, score_id: int):
        return await self.client.delete(
            url=urljoin(
                self._service_url, self.URL_DELETE_SCORE.format(score_id=score_id)
            ),
            headers={"x-sa-entity-context": generate_context(team_id=self.team_id)},
            auth=self.auth,
        )


class CustomFieldsServiceBase:
    """Base class with shared logic for CustomFieldsService"""

    URL_CUSTOM_FIELD_TEMPLATES = "customfieldtemplates"
    URL_CUSTOM_FIELD_TEMPLATE_DELETE = "customfieldtemplates/{template_id}"
    URL_SET_CUSTOM_ENTITIES = "customentities/{pk}"

    def __init__(
        self,
        team_id: int,
        service_url: str,
        auth: Optional[httpx.Auth] = USE_CLIENT_DEFAULT,
    ):
        self.team_id = team_id
        self._service_url = service_url
        self.auth = auth


class CustomFieldsService(CustomFieldsServiceBase, BaseSAServiceProvider):
    """Synchronous CustomFieldsService"""

    def __init__(
        self,
        client: httpx.Client,
        team_id: int,
        service_url: str,
        auth: Optional[httpx.Auth] = USE_CLIENT_DEFAULT,
    ):
        CustomFieldsServiceBase.__init__(self, team_id, service_url, auth=auth)
        BaseSAServiceProvider.__init__(self, client)

    def list_templates(self, entity_spec: EntitySpec, context: dict = None):
        return self.client.get(
            url=urljoin(self._service_url, self.URL_CUSTOM_FIELD_TEMPLATES),
            headers={
                "x-sa-entity-context": generate_context(
                    team_id=self.team_id, **(context or {})
                )
            },
            params={
                "entity": entity_spec.entity,
                "parentEntity": entity_spec.parent_entity,
            },
            auth=self.auth,
        )

    def create_project_template(self, data: dict):
        return self.client.post(
            url=urljoin(self._service_url, self.URL_CUSTOM_FIELD_TEMPLATES),
            data=data,
            headers={"x-sa-entity-context": generate_context(team_id=self.team_id)},
            params={
                "entity": CustomFieldEntityEnum.PROJECT,
                "parentEntity": CustomFieldEntityEnum.TEAM,
            },
            auth=self.auth,
        )

    @prepare_validation_error
    def set_custom_field_value(
        self,
        entity_id: int,
        template_id: int,
        data: dict,
        entity: CustomFieldEntityEnum,
        parent_entity: CustomFieldEntityEnum,
        context: Optional[dict] = None,
    ):
        return self.client.request(
            url=self.URL_SET_CUSTOM_ENTITIES.format(pk=entity_id),
            method="patch",
            headers={
                "x-sa-entity-context": generate_context(**context),
            },
            data={"customField": {"custom_field_values": {template_id: data}}},
            params={
                "entity": entity.value,
                "parentEntity": parent_entity.value,
            },
            auth=self.auth,
        )

    def delete_template(
        self, template_id: int, entity_spec: EntitySpec, context: dict = None
    ):
        return self.client.delete(
            url=urljoin(
                self._service_url,
                self.URL_CUSTOM_FIELD_TEMPLATE_DELETE.format(template_id=template_id),
            ),
            headers={
                "x-sa-entity-context": generate_context(
                    team_id=self.team_id, **(context or {})
                )
            },
            params={
                "entity": entity_spec.entity,
                "parentEntity": entity_spec.parent_entity,
            },
            auth=self.auth,
        )


class AsyncCustomFieldsService(CustomFieldsServiceBase, AsyncSAServiceProvider):
    """Asynchronous CustomFieldsService"""

    def __init__(
        self,
        client: AsyncClient,
        team_id: int,
        service_url: str,
        auth: Optional[httpx.Auth] = USE_CLIENT_DEFAULT,
    ):
        CustomFieldsServiceBase.__init__(self, team_id, service_url, auth=auth)
        AsyncSAServiceProvider.__init__(self, client)

    async def list_templates(self, entity_spec: EntitySpec, context: dict = None):
        return await self.client.get(
            url=urljoin(self._service_url, self.URL_CUSTOM_FIELD_TEMPLATES),
            headers={
                "x-sa-entity-context": generate_context(
                    team_id=self.team_id, **(context or {})
                )
            },
            params={
                "entity": entity_spec.entity,
                "parentEntity": entity_spec.parent_entity,
            },
            auth=self.auth,
        )

    async def create_project_template(self, data: dict):
        return await self.client.post(
            url=urljoin(self._service_url, self.URL_CUSTOM_FIELD_TEMPLATES),
            data=data,
            headers={"x-sa-entity-context": generate_context(team_id=self.team_id)},
            params={
                "entity": CustomFieldEntityEnum.PROJECT,
                "parentEntity": CustomFieldEntityEnum.TEAM,
            },
            auth=self.auth,
        )

    @prepare_validation_error
    async def set_custom_field_value(
        self,
        entity_id: int,
        template_id: int,
        data: dict,
        entity: CustomFieldEntityEnum,
        parent_entity: CustomFieldEntityEnum,
        context: Optional[dict] = None,
    ):
        return await self.client.request(
            url=self.URL_SET_CUSTOM_ENTITIES.format(pk=entity_id),
            method="patch",
            headers={
                "x-sa-entity-context": generate_context(**context),
            },
            data={"customField": {"custom_field_values": {template_id: data}}},
            params={
                "entity": entity.value,
                "parentEntity": parent_entity.value,
            },
            auth=self.auth,
        )

    async def delete_template(
        self, template_id: int, entity_spec: EntitySpec, context: dict = None
    ):
        return await self.client.delete(
            url=urljoin(
                self._service_url,
                self.URL_CUSTOM_FIELD_TEMPLATE_DELETE.format(template_id=template_id),
            ),
            headers={
                "x-sa-entity-context": generate_context(
                    team_id=self.team_id, **(context or {})
                )
            },
            params={
                "entity": entity_spec.entity,
                "parentEntity": entity_spec.parent_entity,
            },
            auth=self.auth,
        )


class UsersServiceBase:
    """Base class with shared logic for UsersService"""

    URL_SEARCH_CUSTOM_ENTITIES = "customentities/search"
    URL_SEARCH_TEAM_USERS = "teamusers/search"
    URL_SEARCH_PROJECT_USERS = "projectusers/search"

    def __init__(
        self,
        team_id: int,
        service_url: str,
        auth: Optional[httpx.Auth] = USE_CLIENT_DEFAULT,
    ):
        self.team_id = team_id
        self._service_url = service_url
        self.auth = auth

    def _get_list_url(
        self, entity_spec: EntitySpec, include_custom_fields: bool = False
    ) -> str:
        """Get the appropriate URL for listing users"""
        if include_custom_fields:
            return urljoin(self._service_url, self.URL_SEARCH_CUSTOM_ENTITIES)
        elif entity_spec.parent_entity == CustomFieldEntityEnum.TEAM:
            return urljoin(self._service_url, self.URL_SEARCH_TEAM_USERS)
        else:
            return urljoin(self._service_url, self.URL_SEARCH_PROJECT_USERS)

    def _get_context(self, project_id: int = None) -> str:
        """Generate context header"""
        if project_id:
            return generate_context(team_id=self.team_id, project_id=project_id)
        else:
            return generate_context(team_id=self.team_id)


class UsersService(UsersServiceBase, BaseSAServiceProvider):
    """Synchronous UsersService"""

    def __init__(
        self,
        client: httpx.Client,
        team_id: int,
        service_url: str,
        auth: Optional[httpx.Auth] = USE_CLIENT_DEFAULT,
    ):
        UsersServiceBase.__init__(self, team_id, service_url, auth=auth)
        BaseSAServiceProvider.__init__(self, client)

    def list(
        self,
        body_query: Query,
        entity_spec: EntitySpec,
        project_id=None,
        include_custom_fields=False,
    ) -> Response[list[WMUserEntity]]:
        url = self._get_list_url(entity_spec, include_custom_fields)
        context = self._get_context(project_id)

        return self.jsx_paginate(
            url=url,
            method="post",
            body_query=body_query,
            query_params={
                "entity": CustomFieldEntityEnum.CONTRIBUTOR,
                "parentEntity": entity_spec.parent_entity,
            },
            headers={"x-sa-entity-context": context},
            chunk_size=100,
            entity_cls=list[WMUserEntity],
            auth=self.auth,
        )


class AsyncUsersService(UsersServiceBase, AsyncSAServiceProvider):
    """Asynchronous UsersService"""

    def __init__(
        self,
        client: AsyncClient,
        team_id: int,
        service_url: str,
        auth: Optional[httpx.Auth] = USE_CLIENT_DEFAULT,
    ):
        UsersServiceBase.__init__(self, team_id, service_url, auth=auth)
        AsyncSAServiceProvider.__init__(self, client)

    async def list(
        self,
        body_query: Query,
        entity_spec: EntitySpec,
        project_id=None,
        include_custom_fields=False,
    ) -> Response[list[WMUserEntity]]:
        url = self._get_list_url(entity_spec, include_custom_fields)
        context = self._get_context(project_id)

        return await self.jsx_paginate(
            url=url,
            method="post",
            body_query=body_query,
            query_params={
                "entity": CustomFieldEntityEnum.CONTRIBUTOR,
                "parentEntity": entity_spec.parent_entity,
            },
            headers={"x-sa-entity-context": context},
            chunk_size=100,
            entity_cls=list[WMUserEntity],
            auth=self.auth,
        )


class ProjectsServiceBase:
    """Base class with shared logic for ProjectsService"""

    URL_GET_PROJECT = "projects/{project_id}"
    URL_SEARCH_PROJECTS = "projects/search"
    URL_SEARCH_CUSTOM_ENTITIES = "customentities/search"

    def __init__(
        self,
        team_id: int,
        service_url: str,
        auth: Optional[httpx.Auth] = USE_CLIENT_DEFAULT,
    ):
        self.team_id = team_id
        self._service_url = service_url
        self.auth = auth


class ProjectsService(ProjectsServiceBase, BaseSAServiceProvider):
    """Synchronous ProjectsService"""

    def __init__(
        self,
        client: httpx.Client,
        team_id: int,
        service_url: str,
        auth: Optional[httpx.Auth] = USE_CLIENT_DEFAULT,
    ):
        ProjectsServiceBase.__init__(self, team_id, service_url, auth=auth)
        BaseSAServiceProvider.__init__(self, client)

    def get_project(self, project_id: int) -> Response[dict]:
        response = self.client.request(
            url=urljoin(
                self._service_url, self.URL_GET_PROJECT.format(project_id=project_id)
            ),
            method="get",
            headers={"x-sa-entity-context": generate_context(team_id=self.team_id)},
            auth=self.auth,
        )
        return self.serialize_response(response, entity_cls=ProjectEntity)

    def search(
        self, body_query: Query, chunk_size=100
    ) -> Response[list[ProjectEntity]]:
        return self.jsx_paginate(
            url=urljoin(self._service_url, self.URL_SEARCH_PROJECTS),
            method="post",
            body_query=body_query,
            headers={"x-sa-entity-context": generate_context(team_id=self.team_id)},
            chunk_size=chunk_size,
            entity_cls=list[ProjectEntity],
            auth=self.auth,
        )

    def list_with_custom_fields(
        self, body_query: Query, chunk_size=100
    ) -> Response[list[ProjectEntity]]:
        return self.jsx_paginate(
            url=urljoin(self._service_url, self.URL_SEARCH_CUSTOM_ENTITIES),
            method="post",
            body_query=body_query,
            query_params={"entity": "Project", "parentEntity": "Team"},
            headers={"x-sa-entity-context": generate_context(team_id=self.team_id)},
            chunk_size=chunk_size,
            auth=self.auth,
        )


class AsyncProjectsService(ProjectsServiceBase, AsyncSAServiceProvider):
    """Asynchronous ProjectsService"""

    def __init__(
        self,
        client: AsyncClient,
        team_id: int,
        service_url: str,
        auth: Optional[httpx.Auth] = USE_CLIENT_DEFAULT,
    ):
        ProjectsServiceBase.__init__(self, team_id, service_url, auth=auth)
        AsyncSAServiceProvider.__init__(self, client)

    async def get_project(self, project_id: int) -> Response[dict]:
        response = await self.client.request(
            url=urljoin(
                self._service_url, self.URL_GET_PROJECT.format(project_id=project_id)
            ),
            method="get",
            headers={"x-sa-entity-context": generate_context(team_id=self.team_id)},
            auth=self.auth,
        )
        return self.serialize_response(response, entity_cls=ProjectEntity)

    async def search(
        self, body_query: Query, chunk_size=100
    ) -> Response[list[ProjectEntity]]:
        return await self.jsx_paginate(
            url=urljoin(self._service_url, self.URL_SEARCH_PROJECTS),
            method="post",
            body_query=body_query,
            headers={"x-sa-entity-context": generate_context(team_id=self.team_id)},
            chunk_size=chunk_size,
            entity_cls=list[ProjectEntity],
            auth=self.auth,
        )

    async def list_with_custom_fields(
        self, body_query: Query, chunk_size=100
    ) -> Response[list[ProjectEntity]]:
        return await self.jsx_paginate(
            url=urljoin(self._service_url, self.URL_SEARCH_CUSTOM_ENTITIES),
            method="post",
            body_query=body_query,
            query_params={"entity": "Project", "parentEntity": "Team"},
            headers={"x-sa-entity-context": generate_context(team_id=self.team_id)},
            chunk_size=chunk_size,
            auth=self.auth,
        )


class WorkManagementServiceBase:
    """Base class with shared logic for WorkManagementService"""

    URL_CREATE_ROLE = "roles"
    URL_CREATE_STATUS = "statuses"
    URL_LIST_STATUSES = "workflows/{workflow_id}/workflowstatuses"
    URL_RESUME_PAUSE_USER = "teams/editprojectsusers"

    def __init__(
        self,
        team_id: int,
        service_url: Optional[str] = None,
        auth: Optional[httpx.Auth] = USE_CLIENT_DEFAULT,
    ):
        self.team_id = team_id
        self.service_url = (
            service_url
            if service_url
            else join_url(os.environ["SA_WORK_MANAGEMENT_URL"], "api/v1/")
        )
        self.auth = auth


class WorkManagementService(WorkManagementServiceBase, BaseSAServiceProvider):
    """Synchronous WorkManagementService"""

    def __init__(
        self,
        team_id: int,
        client: httpx.Client,
        service_url: Optional[str] = None,
        auth: Optional[httpx.Auth] = USE_CLIENT_DEFAULT,
    ):
        WorkManagementServiceBase.__init__(self, team_id, service_url, auth=auth)
        BaseSAServiceProvider.__init__(self, client)

        self.workflows = WorkflowsService(client, team_id, self.service_url, auth=auth)
        self.categories = CategoriesService(
            client, team_id, self.service_url, auth=auth
        )
        self.scores = ScoresService(client, team_id, self.service_url, auth=auth)
        self.custom_fields = CustomFieldsService(
            client, team_id, self.service_url, auth=auth
        )
        self.projects = ProjectsService(client, team_id, self.service_url, auth=auth)
        self.users = UsersService(client, team_id, self.service_url, auth=auth)

    def create_custom_role(
        self, org_id: str, data: dict
    ) -> Response[list[CustomRoleEntity]]:
        response = self.client.request(
            url=self.URL_CREATE_ROLE,
            method="post",
            headers={
                "x-sa-entity-context": generate_context(
                    team_id=self.team_id, organization_id=org_id
                )
            },
            data=data,
            auth=self.auth,
        )
        return self.serialize_response(response, entity_cls=CustomStatusEntity)

    def create_custom_status(
        self, org_id: str, data: dict
    ) -> Response[CustomStatusEntity]:
        response = self.client.request(
            url=self.URL_CREATE_STATUS,
            method="post",
            headers={
                "x-sa-entity-context": generate_context(
                    team_id=self.team_id, organization_id=org_id
                )
            },
            data=data,
            auth=self.auth,
        )
        return self.serialize_response(response, entity_cls=CustomStatusEntity)

    def list_statuses(
        self,
        project_id: int,
        workflow_id: int,
    ) -> Response[CustomStatusEntity]:
        response = self.client.request(
            url=self.URL_LIST_STATUSES.format(workflow_id=workflow_id),
            method="get",
            headers={
                "x-sa-entity-context": generate_context(
                    team_id=self.team_id,
                    project_id=project_id,
                )
            },
            auth=self.auth,
        )
        return self.serialize_response(response, entity_cls=CustomStatusEntity)

    def update_user_activity(
        self, body_query: Query, action=Literal["resume", "pause"]
    ):
        """resume or pause user by projects"""
        body = body_query.body_builder()
        body["body"] = {
            "projectUsers": {"permissions": {"paused": 1 if action == "pause" else 0}}
        }
        response = self.client.request(
            url=self.URL_RESUME_PAUSE_USER,
            method="post",
            data=body,
            headers={
                "x-sa-entity-context": generate_context(team_id=self.team_id),
            },
            auth=self.auth,
        )
        return self.serialize_response(response, entity_cls=BaseEntity)


class AsyncWorkManagementService(WorkManagementServiceBase, AsyncSAServiceProvider):
    """Asynchronous WorkManagementService"""

    def __init__(
        self,
        team_id: int,
        client: AsyncClient,
        service_url: Optional[str] = None,
        auth: Optional[httpx.Auth] = USE_CLIENT_DEFAULT,
    ):
        WorkManagementServiceBase.__init__(self, team_id, service_url, auth=auth)
        AsyncSAServiceProvider.__init__(self, client)

        self.workflows = AsyncWorkflowsService(
            client, team_id, self.service_url, auth=auth
        )
        self.categories = AsyncCategoriesService(
            client, team_id, self.service_url, auth=auth
        )
        self.scores = AsyncScoresService(client, team_id, self.service_url, auth=auth)
        self.custom_fields = AsyncCustomFieldsService(
            client, team_id, self.service_url, auth=auth
        )
        self.projects = AsyncProjectsService(
            client, team_id, self.service_url, auth=auth
        )
        self.users = AsyncUsersService(client, team_id, self.service_url, auth=auth)

    async def create_custom_role(
        self, org_id: str, data: dict
    ) -> Response[list[CustomRoleEntity]]:
        response = await self.client.request(
            url=self.URL_CREATE_ROLE,
            method="post",
            headers={
                "x-sa-entity-context": generate_context(
                    team_id=self.team_id, organization_id=org_id
                )
            },
            data=data,
            auth=self.auth,
        )
        return self.serialize_response(response, entity_cls=CustomStatusEntity)

    async def create_custom_status(
        self, org_id: str, data: dict
    ) -> Response[CustomStatusEntity]:
        response = await self.client.request(
            url=self.URL_CREATE_STATUS,
            method="post",
            headers={
                "x-sa-entity-context": generate_context(
                    team_id=self.team_id, organization_id=org_id
                )
            },
            data=data,
            auth=self.auth,
        )
        return self.serialize_response(response, entity_cls=CustomStatusEntity)

    async def list_statuses(
        self,
        project_id: int,
        workflow_id: int,
        query: Optional[Query] = None,
    ) -> Response[CustomStatusEntity]:
        response = await self.client.request(
            url=join_url(
                self.service_url, self.URL_LIST_STATUSES.format(workflow_id=workflow_id)
            ),
            method="get",
            headers={
                "x-sa-entity-context": generate_context(
                    team_id=self.team_id,
                    project_id=project_id,
                )
            },
            params=query.build_query() if query else None,
            auth=self.auth,
        )
        return self.serialize_response(response, entity_cls=CustomStatusEntity)

    async def update_user_activity(
        self, body_query: Query, action=Literal["resume", "pause"]
    ):
        """resume or pause user by projects"""
        body = body_query.body_builder()
        body["body"] = {
            "projectUsers": {"permissions": {"paused": 1 if action == "pause" else 0}}
        }
        response = await self.client.request(
            url=self.URL_RESUME_PAUSE_USER,
            method="post",
            data=body,
            headers={
                "x-sa-entity-context": generate_context(team_id=self.team_id),
            },
            auth=self.auth,
        )
        return self.serialize_response(response, entity_cls=BaseEntity)
