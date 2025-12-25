import os
from typing import Optional
from urllib.parse import urljoin

import httpx
import jwt
from httpx import AsyncClient
from sapure.services.auth.entities import AuthEntity
from sapure.services.auth.entities import PermissionCheckEntity
from sapure.services.auth.entities import PermissionEntity
from sapure.services.base.service_provider import AsyncSAServiceProvider
from sapure.services.base.service_provider import BaseSAServiceProvider
from sapure.services.base.service_provider import Response


class AuthServiceBase:
    """Base class with shared logic for AuthService"""

    URL_GET_PERMISSIONS = "api/permission"
    URL_GET_AUTH = "api/auth"
    URL_CHECK_PERMISSIONS = "api/permission/check/access"

    def __init__(self, jwt_token: str, service_url: Optional[str] = None):
        self.jwt_token = jwt_token
        self._service_url = service_url or os.environ.get("SA_AUTH_SERVICE_URL")
        if not self._service_url:
            raise ValueError(
                "service_url must be provided or SA_AUTH_SERVICE_URL environment variable must be set"
            )

    def _get_url(self, relative_url: str) -> str:
        """Build full URL from relative path"""
        return urljoin(self._service_url, relative_url)

    def _get_headers(self) -> dict[str, str]:
        """Get default headers for requests"""
        return {
            "Content-Type": "application/json",
            "Accept": "application/json;charset=UTF-8",
            "User-Agent": "SA_ZIMMER",
            "Authorization": self.jwt_token,
        }

    @staticmethod
    def get_jwt_token_payload(token: bytes) -> dict:
        """
        Returns decoded JWT token payload

        Args:
            token: JWT token as bytes (format: b'prefix:actual_token')

        Returns:
            Decoded JWT payload as dictionary
        """
        auth = token.split(b":")
        return jwt.decode(auth[1], options={"verify_signature": False})


class AuthService(AuthServiceBase, BaseSAServiceProvider):
    """Synchronous AuthService for authentication and permission management"""

    def __init__(
        self,
        jwt_token: str,
        client: httpx.Client,
        service_url: Optional[str] = None,
    ):
        AuthServiceBase.__init__(self, jwt_token, service_url)
        BaseSAServiceProvider.__init__(self, client)

    def get_permissions(
        self,
        level: str = "user",
        specific_resources: Optional[dict[str, int]] = None,
    ) -> Response[PermissionEntity]:
        """
        Get user permissions

        Args:
            level: Permission level (default: "user")
            specific_resources: Optional dict of specific resource IDs

        Returns:
            Response containing permission data
        """
        params = {"level": level}
        if specific_resources is not None:
            params.update(specific_resources)

        response = self.client.request(
            method="get",
            url=self._get_url(self.URL_GET_PERMISSIONS),
            params=params,
            headers=self._get_headers(),
        )
        return self.serialize_response(response, entity_cls=PermissionEntity)

    def do_auth(self) -> Response[AuthEntity]:
        """
        Perform authentication

        Returns:
            Response containing authentication data
        """
        response = self.client.request(
            method="get",
            url=self._get_url(self.URL_GET_AUTH),
            headers=self._get_headers(),
        )
        return self.serialize_response(response, entity_cls=AuthEntity)

    def check_permissions(
        self,
        action_name: str,
        specific_resources: dict[str, int],
        level: str = "user",
    ) -> Response[PermissionCheckEntity]:
        """
        Check if user has specific permissions

        Args:
            action_name: Name of the action to check
            specific_resources: Dict of specific resource IDs
            level: Permission level (default: "user")

        Returns:
            Response containing permission check result
        """
        params = {
            **specific_resources,
            "level": level,
            "action_name[]": action_name,
        }
        response = self.client.request(
            method="get",
            url=self._get_url(self.URL_CHECK_PERMISSIONS),
            params=params,
            headers=self._get_headers(),
        )
        return self.serialize_response(response, entity_cls=PermissionCheckEntity)


class AsyncAuthService(AuthServiceBase, AsyncSAServiceProvider):
    """Asynchronous AuthService for authentication and permission management"""

    def __init__(
        self,
        jwt_token: str,
        client: AsyncClient,
        service_url: Optional[str] = None,
    ):
        AuthServiceBase.__init__(self, jwt_token, service_url)
        AsyncSAServiceProvider.__init__(self, client)

    async def get_permissions(
        self,
        level: str = "user",
        specific_resources: Optional[dict[str, int]] = None,
    ) -> Response[PermissionEntity]:
        """
        Get user permissions (async)

        Args:
            level: Permission level (default: "user")
            specific_resources: Optional dict of specific resource IDs

        Returns:
            Response containing permission data
        """
        params = {"level": level}
        if specific_resources is not None:
            params.update(specific_resources)

        response = await self.client.request(
            method="get",
            url=self._get_url(self.URL_GET_PERMISSIONS),
            params=params,
            headers=self._get_headers(),
        )
        return self.serialize_response(response, entity_cls=PermissionEntity)

    async def do_auth(self) -> Response[AuthEntity]:
        """
        Perform authentication (async)

        Returns:
            Response containing authentication data
        """
        response = await self.client.request(
            method="get",
            url=self._get_url(self.URL_GET_AUTH),
            headers=self._get_headers(),
        )
        return self.serialize_response(response, entity_cls=AuthEntity)

    async def check_permissions(
        self,
        action_name: str,
        specific_resources: dict[str, int],
        level: str = "user",
    ) -> Response[PermissionCheckEntity]:
        """
        Check if user has specific permissions (async)

        Args:
            action_name: Name of the action to check
            specific_resources: Dict of specific resource IDs
            level: Permission level (default: "user")

        Returns:
            Response containing permission check result
        """
        params = {
            **specific_resources,
            "level": level,
            "action_name[]": action_name,
        }
        response = await self.client.request(
            method="get",
            url=self._get_url(self.URL_CHECK_PERMISSIONS),
            params=params,
            headers=self._get_headers(),
        )
        return self.serialize_response(response, entity_cls=PermissionCheckEntity)
