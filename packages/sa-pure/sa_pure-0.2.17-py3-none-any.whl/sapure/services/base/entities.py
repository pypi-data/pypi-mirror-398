from datetime import datetime
from datetime import timezone
from enum import Enum
from typing import Any
from typing import List
from typing import Optional
from typing import Union

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator
from pydantic import RootModel
from pydantic_extra_types.color import Color
from sapure.enums import ClassTypeEnum
from sapure.enums import GroupTypeEnum
from sapure.services.base.enums import ProjectStatusEnum


class StringDate(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.parse_datetime
        yield cls.format_iso8601

    @classmethod
    def parse_datetime(cls, value, info) -> datetime:
        if isinstance(value, datetime):
            dt = value
        elif isinstance(value, str):
            try:
                dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        else:
            raise TypeError("Invalid type for StringDate")

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)

        return dt

    @classmethod
    def format_iso8601(cls, value, info) -> str:
        if not isinstance(value, datetime):
            raise TypeError("Expected datetime after parsing")
        return value.isoformat(timespec="milliseconds").replace("+00:00", "Z")


class HexColor(RootModel[str]):
    @field_validator("root", mode="before")
    @classmethod
    def convert_to_hex(cls, value):
        color = Color(value)
        r, g, b = color.as_rgb_tuple()
        return "#{:02X}{:02X}{:02X}".format(r, g, b)


class BaseEntity(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        use_enum_values=True,
        json_encoders={
            Enum: lambda v: v.value,
            datetime.date: lambda v: v.isoformat(),
            datetime: lambda v: v.isoformat(),
        },
    )


class TimedBaseEntity(BaseModel):
    createdAt: Optional[StringDate] = Field(
        None, alias="createdAt", description="Date of creation"
    )
    updatedAt: Optional[StringDate] = Field(
        None, alias="updatedAt", description="Update date"
    )


class ItemEntity(TimedBaseEntity):
    model_config = ConfigDict(extra="allow")
    name: str
    id: Optional[int] = None
    folder_id: Optional[int] = None
    path: Optional[str] = Field(
        None, description="Item’s path in SuperAnnotate project"
    )
    url: Optional[str] = Field(None, description="Publicly available HTTP address")
    annotator_email: Optional[str] = Field(None, description="Annotator email")
    qa_email: Optional[str] = Field(None, description="QA email")
    annotation_status: Optional[Union[int, str]] = Field(
        None, description="Item annotation status"
    )
    entropy_value: Optional[float] = Field(
        None, description="Priority score of given item"
    )
    custom_metadata: Optional[dict] = None
    assignments: Optional[list] = Field([])
    organization_id: Optional[str]
    team_id: Optional[int]
    project_id: Optional[int]
    approval_status: Optional[str]
    is_pinned: Optional[int]
    metadata: Optional[dict] = Field(None, description="Item metadata")
    annotations: Optional[list[dict]] = Field([])
    categories: Optional[list] = Field([])

    def __hash__(self):
        return hash(self.name)

    def add_path(self, project_name: str, folder_name: str):
        self.path = (
            f"{project_name}{f'/{folder_name}' if folder_name != 'root' else ''}"
        )
        return self


class FolderEntity(TimedBaseEntity):
    id: Optional[int]
    name: Optional[str]
    status: Optional[Union[int, str]] = Field(None)
    project_id: Optional[int]
    team_id: Optional[int]
    is_root: Optional[bool] = False
    folder_users: Optional[List[dict]] = Field([])
    completedCount: Optional[int] = Field(None)


class Attribute(TimedBaseEntity):
    model_config = ConfigDict(extra="allow")
    id: Optional[int]
    group_id: Optional[int]
    project_id: Optional[int]
    name: Optional[str]
    default: Any

    def __hash__(self):
        return hash(f"{self.id}{self.group_id}{self.name}")


class AttributeGroup(TimedBaseEntity):
    model_config = ConfigDict(extra="allow", use_enum_values=True)
    id: Optional[int]
    group_type: Optional[GroupTypeEnum]
    class_id: Optional[int]
    name: Optional[str]
    isRequired: bool = Field(default=False)
    attributes: Optional[List[Attribute]]
    default_value: Optional[Any] = Field(default=None)

    def __hash__(self):
        return hash(f"{self.id}{self.class_id}{self.name}")


class AnnotationClassEntity(TimedBaseEntity):
    model_config = ConfigDict(
        extra="allow", use_enum_values=True, validate_assignment=True
    )
    id: Optional[int]
    project_id: Optional[int]
    type: ClassTypeEnum = ClassTypeEnum.OBJECT
    name: str
    color: HexColor
    attribute_groups: List[AttributeGroup] = []

    def __hash__(self):
        return hash(f"{self.id}{self.type}{self.name}")


class ProjectEntity(TimedBaseEntity):
    id: int
    team_id: int
    name: str
    status: Optional[ProjectStatusEnum] = None
    workflow_id: int
    description: Optional[str] = None
