from typing import Optional

from pydantic import BaseModel


class Attachment(BaseModel):
    name: str
    path: str
    integration_id: Optional[int] = None


class AttachmentMeta(BaseModel):
    width: Optional[float] = None
    height: Optional[float] = None
    integration_id: Optional[int] = None
