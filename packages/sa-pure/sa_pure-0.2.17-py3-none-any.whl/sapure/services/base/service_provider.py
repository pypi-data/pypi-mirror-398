import json
from abc import ABC
from typing import Any
from typing import Generic
from typing import List
from typing import Literal
from typing import Optional
from typing import Type
from typing import TypeVar
from typing import Union

import httpx
from httpx import AsyncClient
from httpx import Client
from pydantic import BaseModel
from sapure.services.base.entities import BaseEntity
from sapure.services.filters import Limit
from sapure.services.filters import Offset
from sapure.services.filters import Query

T = TypeVar("T")


class ErrorDetail(BaseModel):
    message: str
    code: Optional[str] = None

    def __str__(self) -> str:
        return self.message


class Response(BaseModel, Generic[T]):
    success: Optional[bool] = True
    data: Optional[Union[T, List[T]]] = None
    errors: Optional[List[ErrorDetail]] = None

    @staticmethod
    def error_response(msg: str) -> "Response[Any]":
        res = Response[Any](success=False)
        res.errors = [ErrorDetail(message=msg)]
        return res

    def first(self) -> Optional[Union[T]]:
        if self.success and isinstance(self.data, list):
            return self.data[0]

    def raise_for_status(self):
        if not self.success:
            error_msg = self.errors[0].message if self.errors else "Unknown error"
            raise RuntimeError(f"Response failed: {error_msg}")


class BaseServiceProvider(ABC):
    def serialize_response(
        self,
        response: httpx.Response,
        dispatcher: Optional[str] = "data",
        entity_cls: Optional[
            Union[Type[BaseModel], Type[list[BaseModel]], Type[dict], Type[list]]
        ] = None,
    ) -> Response:
        entity_cls = entity_cls or getattr(self, "entity_cls", None)
        result = Response[entity_cls](success=response.is_success)
        if response.is_success:
            data_json = response.json()
            if isinstance(data_json, str):
                data_json = json.loads(data_json)
            if dispatcher:
                payload = data_json.pop(dispatcher, data_json)
            else:
                payload = data_json
            if entity_cls:
                if entity_cls is dict or entity_cls is list:
                    result.data = payload
                elif isinstance(payload, list):
                    result.data = [entity_cls(**item) for item in payload]
                elif isinstance(payload, dict):
                    result.data = entity_cls(**payload)
                else:
                    result.data = payload
            else:
                result.data = payload
        else:
            status_code = response.status_code
            if status_code in (502, 504):
                result.errors = [
                    ErrorDetail(
                        message="Our service is currently unavailable, please try again later."
                    )
                ]
            else:
                data_json = response.json()
                if "error" in data_json:
                    result.errors = [
                        ErrorDetail(
                            code=str(status_code),
                            message=self.__retrieve_error(data_json["error"]),
                        )
                    ]
                elif "errors" in data_json:
                    result.errors = [
                        ErrorDetail(message=str(e)) for e in data_json["errors"]
                    ]
                elif "message" in data_json:
                    result.errors = [ErrorDetail(message=data_json["message"])]
                else:
                    result.errors = [ErrorDetail(message="Unknown Error")]
        return result

    @staticmethod
    def __retrieve_error(err: Any):
        if isinstance(err, dict):
            return err.get("message", err)
        return err


class BaseSAServiceProvider(BaseServiceProvider):
    def __init__(self, client: Client):
        self.client = client

    @property
    def entity(self):
        return getattr(getattr(self.client, "Meta", BaseEntity), "entity", BaseEntity)

    def paginate(
        self,
        url: str,
        chunk_size: int = 2000,
        query_params: dict[str, Any] = None,
        headers: dict[str, str] = None,
        entity_cls: Optional[Union[Type[BaseModel], Type[list[BaseModel]]]] = None,
        **kwargs,
    ) -> Response:
        offset = 0
        total = []
        entity_cls = entity_cls or self.entity
        if query_params is None:
            query_params = {}
        try:
            while True:
                query_params["offset"] = offset
                response = self.client.get(
                    url, params=query_params, headers=headers, **kwargs
                )
                response.raise_for_status()
                data = response.json().get("data", [])
                total.extend(data)
                data_len = len(data)
                offset += data_len
                if data_len < chunk_size:
                    break
        except httpx.HTTPStatusError as e:
            return Response[entity_cls](
                success=False,
                errors=[
                    ErrorDetail(
                        message=f"Request failed: {e.response.status_code} {e.response.text}"
                    )
                ],
            )
        except httpx.RequestError as e:
            raise RuntimeError(f"Request error: {str(e)}")

        return Response[entity_cls](data=total)

    def jsx_paginate(
        self,
        url: str,
        method: str = Literal["get", "post"],
        body_query: Query = None,
        query_params: dict = None,
        headers: dict = None,
        chunk_size: int = 100,
        entity_cls: Optional[Union[Type[BaseModel], Type[list[BaseModel]]]] = None,
        **kwargs,
    ) -> Response:
        entity_cls = entity_cls or self.entity
        offset = 0
        total = []

        while True:
            paginated_query = body_query & Limit(chunk_size) & Offset(offset)
            response = self.client.request(
                url=url,
                method=method,
                json=paginated_query.body_builder(),
                params=query_params,
                headers=headers,
                **kwargs,
            )
            response.raise_for_status()
            res_data = response.json()

            data = res_data.get("data", [])
            total.extend(data)

            if len(data) < chunk_size:
                break
            offset += chunk_size
        return Response[entity_cls](data=total)

    # TODO test
    def paginate_post(
        self,
        url: str,
        chunk_size: int = 2000,
        base_body: dict[str, Any] = None,
        query_params: dict[str, Any] = None,
        headers: dict[str, str] = None,
        entity_cls: Optional[Union[Type[BaseModel], Type[list[BaseModel]]]] = None,
    ) -> Response:
        offset = 0
        total = []
        entity_cls = entity_cls or self.entity
        base_body = base_body or {}

        try:
            while True:
                body = dict(base_body)
                body.update({"offset": offset, "limit": chunk_size})
                response = self.client.request(
                    url=url,
                    method="post",
                    json=body,
                    params=query_params,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()
                total.extend(data)
                data_len = len(data)
                offset += data_len
                if data_len < chunk_size:
                    break
        except httpx.HTTPStatusError as e:
            return Response[entity_cls](
                success=False,
                errors=ErrorDetail(
                    message=f"Request failed: {e.response.status_code} {e.response.text}"
                ),
            )
        except httpx.RequestError as e:
            raise RuntimeError(f"Request error: {str(e)}")

        return Response[entity_cls](data=total)


class AsyncSAServiceProvider(BaseServiceProvider):
    def __init__(self, client: AsyncClient):
        self.client = client

    @property
    def entity(self):
        return getattr(getattr(self.client, "Meta", BaseEntity), "entity", BaseEntity)

    async def paginate(
        self,
        url: str,
        chunk_size: int = 2000,
        query_params: dict[str, Any] = None,
        headers: dict[str, str] = None,
        entity_cls: Optional[Union[Type[BaseModel], Type[list[BaseModel]]]] = None,
        **kwargs,
    ) -> Response:
        offset = 0
        total = []
        entity_cls = entity_cls or self.entity
        try:
            while True:
                query_params["offset"] = offset
                response = await self.client.get(
                    url, params=query_params, headers=headers, **kwargs
                )
                response.raise_for_status()
                data = response.json().get("data", [])
                total.extend(data)
                data_len = len(data)
                offset += data_len
                if data_len < chunk_size:
                    break
        except httpx.HTTPStatusError as e:
            return Response[entity_cls](
                success=False,
                errors=[
                    ErrorDetail(
                        message=f"Request failed: {e.response.status_code} {e.response.text}"
                    )
                ],
            )
        except httpx.RequestError as e:
            raise RuntimeError(f"Request error: {str(e)}")

        return Response[entity_cls](data=total)

    async def jsx_paginate(
        self,
        url: str,
        method: str = Literal["get", "post"],
        body_query: Query = None,
        query_params: dict = None,
        headers: dict = None,
        chunk_size: int = 100,
        entity_cls: Optional[Union[Type[BaseModel], Type[list[BaseModel]]]] = None,
        **kwargs,
    ) -> Response:
        entity_cls = entity_cls or self.entity
        offset = 0
        total = []

        while True:
            paginated_query = body_query & Limit(chunk_size) & Offset(offset)
            response = await self.client.request(
                url=url,
                method=method,
                json=paginated_query.body_builder(),
                params=query_params,
                headers=headers,
                **kwargs,
            )
            response.raise_for_status()
            res_data = response.json()

            data = res_data.get("data", [])
            total.extend(data)

            if len(data) < chunk_size:
                break
            offset += chunk_size
        return Response[entity_cls](data=total)

    # TODO test
    async def paginate_post(
        self,
        url: str,
        chunk_size: int = 2000,
        base_body: dict[str, Any] = None,
        query_params: dict[str, Any] = None,
        headers: dict[str, str] = None,
        entity_cls: Optional[Union[Type[BaseModel], Type[list[BaseModel]]]] = None,
    ) -> Response:
        offset = 0
        total = []
        entity_cls = entity_cls or self.entity
        base_body = base_body or {}

        try:
            while True:
                body = dict(base_body)
                body.update({"offset": offset, "limit": chunk_size})
                response = await self.client.request(
                    url=url,
                    method="post",
                    json=body,
                    params=query_params,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()
                total.extend(data)
                data_len = len(data)
                offset += data_len
                if data_len < chunk_size:
                    break
        except httpx.HTTPStatusError as e:
            return Response[entity_cls](
                success=False,
                errors=ErrorDetail(
                    message=f"Request failed: {e.response.status_code} {e.response.text}"
                ),
            )
        except httpx.RequestError as e:
            raise RuntimeError(f"Request error: {str(e)}")

        return Response[entity_cls](data=total)
