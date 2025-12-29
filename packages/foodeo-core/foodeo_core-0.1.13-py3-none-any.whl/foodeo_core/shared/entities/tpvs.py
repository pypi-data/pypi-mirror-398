from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class Tpvs(BaseModel):
    id: int = Field(gt=0)
    name: str
    key: UUID
    local_key: Optional[UUID] = Field(default=None)
