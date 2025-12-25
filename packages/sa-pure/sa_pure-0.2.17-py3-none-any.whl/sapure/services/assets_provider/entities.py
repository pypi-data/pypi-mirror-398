from typing import Optional

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class ClassifiedItems(BaseModel):
    small: list[list[dict]]
    large: list[dict]


class UploadAnnotationsResponse(BaseModel):
    class Resource(BaseModel):
        classes: list[str] = Field([], alias="class")
        templates: list[str] = Field([], alias="template")
        attributes: list[str] = Field([], alias="attribute")
        attribute_groups: Optional[list[str]] = Field([], alias="attributeGroup")

    failed_items: list[str] = Field([], alias="failedItems")
    missing_resources: Resource = Field({}, alias="missingResources")

    model_config = ConfigDict(extra="allow")
