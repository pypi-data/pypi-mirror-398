from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class StaffSchedule(BaseModel):
    id: int = Field(gt=0)
    staff_id: int
    start_time: datetime
    end_time: Optional[datetime]
    signed_by_id: int
