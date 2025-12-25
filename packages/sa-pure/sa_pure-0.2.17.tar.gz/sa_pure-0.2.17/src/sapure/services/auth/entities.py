from typing import Any

from pydantic import BaseModel


class PermissionEntity(BaseModel):
    """Entity representing user permissions"""

    data: dict[str, Any] | None = None


class AuthEntity(BaseModel):
    """Entity representing authentication response"""

    data: dict[str, Any] | None = None


class PermissionCheckEntity(BaseModel):
    """Entity representing permission check result"""

    data: dict[str, Any] | None = None
