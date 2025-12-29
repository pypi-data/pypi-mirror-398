from typing import Optional

from pydantic import BaseModel, Field


class Zones(BaseModel):
    id: int = Field(gt=0)
    name: str
    tpv: int
    not_assigned: bool = Field(default=False)
    tables: Optional[list[int]] = Field(...)
    tpv_name: str
