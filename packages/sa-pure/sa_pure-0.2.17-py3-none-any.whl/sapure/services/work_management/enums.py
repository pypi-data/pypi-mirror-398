from enum import auto
from enum import Enum


class WMUserTypeEnum(int, Enum):
    Contributor = 4
    TeamAdmin = 7
    TeamOwner = 12
    OrganizationAdmin = 15
    other = auto()


class WMUserStateEnum(str, Enum):
    Pending = "PENDING"
    Confirmed = "CONFIRMED"


class ProjectStateEnum(str, Enum):
    Pending = "PENDING"
    Confirmed = "CONFIRMED"


class WorkflowTypeEnum(str, Enum):
    SYSTEM = "system"
    USER = "user"
