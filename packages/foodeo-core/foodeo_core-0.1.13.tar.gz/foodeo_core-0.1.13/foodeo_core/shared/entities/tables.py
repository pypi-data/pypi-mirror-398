from typing import Optional

from pydantic import BaseModel, Field


class Tables(BaseModel):
    id: int = Field(gt=0)
    name: str = Field(...)
    qr: str = Field(...)
    chairs: Optional[int] = Field(default=None)
    order: Optional[int] = Field(default=None)
    zone: Optional[int] = Field(default=None)
