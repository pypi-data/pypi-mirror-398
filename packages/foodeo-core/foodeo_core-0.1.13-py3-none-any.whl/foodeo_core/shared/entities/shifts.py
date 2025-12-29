from typing import Optional

from pydantic import BaseModel, Field


class Shifts(BaseModel):
    id: int = Field(gt=0)
    start_at: str
    end_at: str
    order_per_shift: int
    days_closed: Optional[list[int]] = Field(default=None)
