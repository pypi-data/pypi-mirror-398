from typing import Optional

from pydantic import BaseModel, Field


class ReservationsOptions(BaseModel):
    id: int = Field(gt=0)
    title: str
    description: Optional[str] = Field(default=None)
    is_multiple: bool = Field(default=False)
