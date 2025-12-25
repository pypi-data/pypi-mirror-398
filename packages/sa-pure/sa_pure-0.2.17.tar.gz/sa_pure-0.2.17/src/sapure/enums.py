import typing
from enum import Enum
from enum import IntEnum


class TitledIntEnum(IntEnum):
    """IntEnum with a human-readable title/label."""

    def __new__(cls, value: int, title: str):
        obj = int.__new__(cls, value)
        obj._value_ = value
        obj.title = title
        return obj

    def __str__(self) -> str:
        return self.title

    @classmethod
    def choices(cls) -> typing.Tuple[typing.Tuple[int, str], ...]:
        """(value, title) pairs, e.g. for Django choices."""
        return tuple((m.value, m.title) for m in cls)

    @classmethod
    def titles(cls) -> typing.Tuple[str, ...]:
        return tuple(m.title for m in cls)

    @classmethod
    def values(cls) -> typing.List[int]:
        return [m.value for m in cls]

    @classmethod
    def from_any(cls, x: typing.Union[int, str, "TitledIntEnum"]) -> "TitledIntEnum":
        """
        Smart constructor:
        - int -> by value
        - str -> by name OR title (case-insensitive)
        - enum -> returns itself
        """
        if isinstance(x, cls):
            return x
        if isinstance(x, int):
            return cls(x)

        if isinstance(x, str):
            # by name
            if x in cls.__members__:
                return cls.__members__[x]
            # by title (case-insensitive)
            x_low = x.lower()
            for m in cls:
                if m.title.lower() == x_low:
                    return m

        raise ValueError(f"{x!r} is not a valid {cls.__name__}")


class StrEnum(str, Enum):
    pass


class CustomFieldEntityEnum(StrEnum):
    CONTRIBUTOR = "Contributor"
    TEAM = "Team"
    PROJECT = "Project"


class ProjectTypeEnum(StrEnum):
    Vector = "VECTOR"
    Pixel = "PIXEL"
    Video = "PUBLIC_VIDEO"
    Document = "PUBLIC_TEXT"
    Tiled = "TILED"
    Other = "CLASSIFICATION"
    PointCloud = "POINT_CLOUD"
    Multimodal = "CUSTOM_LLM"


class ProjectNumericEnum(IntEnum):
    VECTOR = 1
    PIXEL = 2
    VIDEO = 3
    DOCUMENT = 4
    TILED = 5
    OTHER = 6
    POINT_CLOUD = 7
    CUSTOM_EDITOR = 8


class ExportStatus(IntEnum):
    IN_PROGRESS = 1
    COMPLETE = 2
    CANCELED = 3  # noqa
    ERROR = 4


class GroupTypeEnum(StrEnum):
    RADIO = "radio"
    CHECKLIST = "checklist"
    NUMERIC = "numeric"
    TEXT = "text"
    OCR = "ocr"


class ClassTypeEnum(IntEnum):
    OBJECT = 1
    TAG = 2
    RELATIONSHIP = 3


class FolderStatus(TitledIntEnum):
    Undefined = (-1, "Undefined")
    NotStarted = (1, "NotStarted")
    InProgress = (2, "InProgress")
    Completed = (3, "Completed")
    OnHold = (4, "OnHold")


class ProjectStatus(TitledIntEnum):
    Undefined = (-1, "Undefined")
    NotStarted = (1, "NotStarted")
    InProgress = (2, "InProgress")
    Completed = (3, "Completed")
    OnHold = (4, "OnHold")


class ProjectStatusWMEnum(str, Enum):
    Undefined = "undefined"
    NotStarted = "notStarted"
    InProgress = "inProgress"
    Completed = "completed"
    OnHold = "onHold"
