from typing import Optional

from pydantic import Field
from sapure.services.base.entities import TimedBaseEntity
from sapure.services.work_management.enums import WMUserStateEnum
from sapure.services.work_management.enums import WMUserTypeEnum
from sapure.services.work_management.enums import WorkflowTypeEnum


class ItemCategory(TimedBaseEntity):
    id: int
    project_id: int
    name: str


class WMUserEntity(TimedBaseEntity):
    id: Optional[int]
    team_id: Optional[int]
    role: WMUserTypeEnum
    email: Optional[str] = None
    state: Optional[WMUserStateEnum] = None
    custom_fields: Optional[dict] = Field(dict(), alias="customField")


class WorkflowEntity(TimedBaseEntity):
    id: int
    name: str
    description: Optional[str] = None
    organization_id: Optional[str]
    team_id: Optional[int]
    type: WorkflowTypeEnum
    raw_config: Optional[dict] = None


class CustomRoleEntity(TimedBaseEntity):
    name: str
    description: Optional[str] = None


class CustomStatusEntity(TimedBaseEntity):
    id: int
    status_id: int
    value: int
    status: Optional[dict] = None
