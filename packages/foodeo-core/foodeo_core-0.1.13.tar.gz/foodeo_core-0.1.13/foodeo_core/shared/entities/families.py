from typing import Optional

from pydantic import BaseModel, Field


class Families(BaseModel):
    id: int = Field(gt=0)
    name: str = Field(...)
    categories: Optional[list[int]] = Field(default=None)
    printers: Optional[list[int]] = Field(default=None)
